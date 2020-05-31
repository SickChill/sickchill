# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import re
from base64 import b16encode, b32decode
from datetime import datetime
from itertools import chain
from os.path import join
from random import shuffle

# Third Party Imports
import six
from requests.utils import add_dict_to_cookiejar

# First Party Imports
import sickbeard
from sickbeard import logger
from sickbeard.classes import Proper, SearchResult
from sickbeard.common import MULTI_EP_RESULT, Quality, SEASON_RESULT, ua_pool
from sickbeard.db import DBConnection
from sickbeard.helpers import download_file, getURL, make_session, remove_file_failed
from sickbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickbeard.show_name_helpers import allPossibleShowNames
from sickbeard.tvcache import TVCache
from sickchill.helper.common import sanitize_filename
from sickchill.helper.encoding import ek


class GenericProvider(object):
    NZB = 'nzb'
    NZBDATA = 'nzbdata'
    TORRENT = 'torrent'

    PROVIDER_BROKEN = 0
    PROVIDER_DAILY = 1
    PROVIDER_BACKLOG = 2
    PROVIDER_OK = 3

    ProviderStatus = {
        PROVIDER_BROKEN: _("Not working"),
        PROVIDER_DAILY: _("Daily/RSS only"),
        PROVIDER_BACKLOG: _("Backlog/Manual Search only"),
        PROVIDER_OK: _("Daily/RSS and Backlog/Manual Searches working")
    }

    def __init__(self, name):
        self.name = name

        self.anime_only = False
        self.bt_cache_urls = [
            #'http://torcache.net/torrent/{torrent_hash}.torrent',
            'http://torrentproject.se/torrent/{torrent_hash}.torrent',
            'http://thetorrent.org/torrent/{torrent_hash}.torrent',
            'http://btdig.com/torrent/{torrent_hash}.torrent',
            ('https://t.torrage.info/download?h={torrent_hash}', 'https://torrage.info/torrent.php?h={torrent_hash}'),
            'https://itorrents.org/torrent/{torrent_hash}.torrent?title={torrent_name}'
        ]
        self.cache = TVCache(self)
        self.enable_backlog = False
        self.enable_daily = False
        self.enabled = False
        self.headers = {'User-Agent': ua_pool.random}
        self.proper_strings = ['PROPER|REPACK|REAL']
        self.provider_type = None
        self.public = False
        self.search_fallback = False
        self.search_mode = None
        self.session = make_session()
        self.show = None
        self.supports_absolute_numbering = False
        self.supports_backlog = True
        self.url = ''
        self.urls = {}

        # Use and configure the attribute enable_cookies to show or hide the cookies input field per provider
        self.enable_cookies = False
        self.cookies = ''
        self.rss_cookies = ''

        self.ability_status = self.PROVIDER_OK

        shuffle(self.bt_cache_urls)

    def download_result(self, result):
        if not self.login():
            return False

        urls, filename = self._make_url(result)

        for url in urls:
            if 'NO_DOWNLOAD_NAME' in url:
                continue

            if isinstance(url, tuple):
                referer = url[1]
                url = url[0]
            else:
                referer = '/'.join(url.split('/')[:3]) + '/'

            if url.startswith('http'):
                self.headers.update({
                    'Referer': referer
                })

            logger.log('Downloading a result from {0} at {1}'.format(self.name, url))

            downloaded_filename = download_file(url, filename, session=self.session, headers=self.headers,
                                                hooks={'response': self.get_url_hook}, return_filename=True)
            if downloaded_filename:
                if self._verify_download(downloaded_filename):
                    logger.log('Saved result to {0}'.format(downloaded_filename), logger.INFO)
                    return True

                logger.log('Could not download {0}'.format(url), logger.WARNING)
                remove_file_failed(downloaded_filename)

        if urls:
            logger.log('Failed to download any results', logger.WARNING)

        return False

    def find_propers(self, search_date=None):
        results = self.cache.list_propers(search_date)

        return [Proper(x[b'name'], x[b'url'], datetime.fromtimestamp(x[b'time']), self.show) for x in results]

    def find_search_results(self, show, episodes, search_mode,
                            manual_search=False, download_current_quality=False):
        self._check_auth()
        self.show = show

        results = {}
        items_list = []
        searched_scene_season = None

        for episode in episodes:
            cache_result = self.cache.search_cache(episode, manual_search=manual_search,
                                                   down_cur_quality=download_current_quality)
            if cache_result:
                if episode.episode not in results:
                    results[episode.episode] = cache_result
                else:
                    results[episode.episode].extend(cache_result)

                continue

            if len(episodes) > 1 and search_mode == 'sponly' and searched_scene_season == episode.scene_season:
                continue

            search_strings = []
            searched_scene_season = episode.scene_season

            if len(episodes) > 1 and search_mode == 'sponly':
                search_strings = self.get_season_search_strings(episode)
            elif search_mode == 'eponly':
                search_strings = self.get_episode_search_strings(episode)

            for search_string in search_strings:
                items_list += self.search(search_string, ep_obj=episode)

        if len(results) == len(episodes):
            return results

        if items_list:
            items = {}
            unknown_items = []

            for item in items_list:
                quality = self.get_quality(item, anime=show.is_anime)

                if quality == Quality.UNKNOWN:
                    unknown_items.append(item)
                elif quality == Quality.NONE:
                    pass  # Skipping an HEVC when HEVC is not allowed by settings
                else:
                    if quality not in items:
                        items[quality] = []
                    items[quality].append(item)

            items_list = list(chain(*[v for (k_, v) in sorted(six.iteritems(items), reverse=True)]))
            items_list += unknown_items

        cl = []

        for item in items_list:
            (title, url) = self._get_title_and_url(item)

            try:
                parse_result = NameParser(parse_method=('normal', 'anime')[show.is_anime]).parse(title)
            except (InvalidNameException, InvalidShowException) as error:
                logger.log("{0}".format(error), logger.DEBUG)
                continue

            show_object = parse_result.show
            quality = parse_result.quality
            release_group = parse_result.release_group
            version = parse_result.version
            add_cache_entry = False

            if not (show_object.air_by_date or show_object.sports):
                if search_mode == 'sponly':
                    if parse_result.episode_numbers:
                        logger.log(
                            'This is supposed to be a season pack search but the result {0} is not a valid season pack, skipping it'.format(title),
                            logger.DEBUG
                        )
                        add_cache_entry = True
                    elif not [ep for ep in episodes if parse_result.season_number == (ep.season, ep.scene_season)[ep.show.is_scene]]:
                        logger.log(
                            'This season result {0} is for a season we are not searching for, skipping it'.format(title),
                            logger.DEBUG
                        )
                        add_cache_entry = True

                else:
                    if not all([

                        parse_result.season_number is not None,
                        parse_result.episode_numbers,
                        [ep for ep in episodes if (ep.season, ep.scene_season)[ep.show.is_scene] ==
                        (parse_result.season_number, parse_result.scene_season)[ep.show.is_scene] and
                        (ep.episode, ep.scene_episode)[ep.show.is_scene] in parse_result.episode_numbers]
                    ]) and not all([
                        # fallback for anime on absolute numbering
                        parse_result.is_anime,
                        parse_result.ab_episode_numbers is not None,
                        [ep for ep in episodes if ep.show.is_anime and
                        ep.absolute_number in parse_result.ab_episode_numbers]
                    ]):

                        logger.log(
                            'The result {0} doesn\'t seem to match an episode that we are currently trying to snatch, skipping it'.format(title),
                            logger.DEBUG)
                        add_cache_entry = True

                if not add_cache_entry:
                    actual_season = parse_result.season_number
                    actual_episodes = parse_result.episode_numbers
            else:
                same_day_special = False

                if not parse_result.is_air_by_date:
                    logger.log(
                        'This is supposed to be a date search but the result {0} didn\'t parse as one, skipping it'.format(title),
                        logger.DEBUG)
                    add_cache_entry = True
                else:
                    air_date = parse_result.air_date.toordinal()
                    db = DBConnection()
                    sql_results = db.select(
                        'SELECT season, episode FROM tv_episodes WHERE showid = ? AND airdate = ?',
                        [show_object.indexerid, air_date]
                    )

                    if len(sql_results) == 2:
                        if int(sql_results[0][b'season']) == 0 and int(sql_results[1][b'season']) != 0:
                            actual_season = int(sql_results[1][b'season'])
                            actual_episodes = [int(sql_results[1][b'episode'])]
                            same_day_special = True
                        elif int(sql_results[1][b'season']) == 0 and int(sql_results[0][b'season']) != 0:
                            actual_season = int(sql_results[0][b'season'])
                            actual_episodes = [int(sql_results[0][b'episode'])]
                            same_day_special = True
                    elif len(sql_results) != 1:
                        logger.log(
                            'Tried to look up the date for the episode {0} but the database didn\'t give proper results, skipping it'.format(title),
                            logger.WARNING)
                        add_cache_entry = True

                if not add_cache_entry and not same_day_special:
                    actual_season = int(sql_results[0][b'season'])
                    actual_episodes = [int(sql_results[0][b'episode'])]

            if add_cache_entry:
                logger.log('Adding item from search to cache: {0}'.format(title), logger.DEBUG)

                # Access to a protected member of a client class
                ci = self.cache._add_cache_entry(title, url, parse_result=parse_result)

                if ci is not None:
                    cl.append(ci)

                continue

            episode_wanted = True

            for episode_number in actual_episodes:
                if not show_object.wantEpisode(actual_season, episode_number, quality, manual_search,
                                               download_current_quality):
                    episode_wanted = False
                    break

            if not episode_wanted:
                logger.log('Ignoring result {0}.'.format(title), logger.DEBUG)
                continue

            logger.log('Found result {0} at {1}'.format(title, url), logger.DEBUG)

            episode_object = []
            for current_episode in actual_episodes:
                episode_object.append(show_object.getEpisode(actual_season, current_episode))

            result = self.get_result(episode_object)
            result.show = show_object
            result.url = url
            result.name = title
            result.quality = quality
            result.release_group = release_group
            result.version = version
            result.content = None
            result.size = self._get_size(item)

            if len(episode_object) == 1:
                episode_number = episode_object[0].episode
                logger.log('Single episode result.', logger.DEBUG)
            elif len(episode_object) > 1:
                episode_number = MULTI_EP_RESULT
                logger.log('Separating multi-episode result to check for later - result contains episodes: {0}'.format(
                    parse_result.episode_numbers), logger.DEBUG)
            elif len(episode_object) == 0:
                episode_number = SEASON_RESULT
                logger.log('Separating full season result to check for later', logger.DEBUG)

            if episode_number not in results:
                results[episode_number] = [result]
            else:
                results[episode_number].append(result)

        if cl:

            # Access to a protected member of a client class
            cache_db = self.cache._get_db()
            cache_db.mass_action(cl)

        return results

    def get_id(self, suffix=''):
        return GenericProvider.make_id(self.name) + six.text_type(suffix)

    def get_quality(self, item, anime=False):
        (title, url_) = self._get_title_and_url(item)
        quality = Quality.scene_quality(title, anime)

        return quality

    def get_result(self, episodes):
        result = self._get_result(episodes)
        result.provider = self

        return result

    @staticmethod
    def get_url_hook(response, **kwargs_):
        if response:
            logger.log('{0} URL: {1} [Status: {2}]'.format
                       (response.request.method, response.request.url, response.status_code), logger.DEBUG)

            if response.request.method == 'POST':
                logger.log('With post data: {0}'.format(response.request.body), logger.DEBUG)

    def get_url(self, url, post_data=None, params=None, timeout=30, **kwargs):
        kwargs['hooks'] = {'response': self.get_url_hook}
        return getURL(url, post_data, params, self.headers, timeout, self.session, **kwargs)

    def image_name(self):
        return self.get_id() + '.png'

    @property
    def is_active(self):
        return False

    @property
    def is_enabled(self):
        return bool(self.enabled)

    @property
    def daily_enabled(self):
        return int(self.enable_daily)

    @property
    def backlog_enabled(self):
        return int(self.enable_backlog)

    @property
    def search_fallback_enabled(self):
        return int(self.search_fallback)

    @property
    def can_daily(self):
        return self.ability_status & self.PROVIDER_DAILY != 0

    @property
    def can_backlog(self):
        return self.ability_status & self.PROVIDER_BACKLOG != 0 and self.supports_backlog

    def status(self):
        return self.ProviderStatus.get(self.ability_status)

    @staticmethod
    def make_id(name):
        if not name:
            return ''

        return re.sub(r'[^\w\d_]', '_', str(name).strip().lower())

    def search_rss(self, episodes):
        return self.cache.find_needed_episodes(episodes)

    def seed_ratio(self):
        return ''

    def _check_auth(self):
        return True

    def login(self):
        return True

    def search(self, search_params, age=0, ep_obj=None):
        return []

    def _get_result(self, episodes):
        return SearchResult(episodes)

    def get_episode_search_strings(self, episode, add_string=''):
        if not episode:
            return []

        search_string = {
            'Episode': []
        }

        for show_name in allPossibleShowNames(episode.show, season=episode.scene_season):
            episode_string = show_name + ' '
            episode_string_fallback = None

            if episode.show.air_by_date:
                episode_string += str(episode.airdate).replace('-', ' ')
            elif episode.show.sports:
                episode_string += str(episode.airdate).replace('-', ' ')
                episode_string += ('|', ' ')[len(self.proper_strings) > 1]
                episode_string += episode.airdate.strftime('%b')
            elif episode.show.anime:
                episode_string_fallback = episode_string + '{0:02d}'.format(int(episode.scene_absolute_number))
                episode_string += '{0:03d}'.format(int(episode.scene_absolute_number))
            else:
                episode_string += sickbeard.config.naming_ep_type[2] % {
                    'seasonnumber': episode.scene_season,
                    'episodenumber': episode.scene_episode,
                }

            if add_string:
                episode_string += ' ' + add_string
                if episode_string_fallback:
                    episode_string_fallback += ' ' + add_string

            search_string['Episode'].append(episode_string.encode('utf-8').strip())
            if episode_string_fallback:
                search_string['Episode'].append(episode_string_fallback.encode('utf-8').strip())

        return [search_string]

    def get_season_search_strings(self, episode):
        search_string = {
            'Season': []
        }

        for show_name in allPossibleShowNames(episode.show, season=episode.scene_season):
            season_string = show_name + ' '

            if episode.show.air_by_date or episode.show.sports:
                season_string += str(episode.airdate).split('-')[0]
            elif episode.show.anime:
                # use string below if you really want to search on season with number
                # season_string += 'Season ' + '{0:d}'.format(int(episode.scene_season))
                season_string += 'Season'  # ignore season number to get all seasons in all formats
            else:
                season_string += 'S{0:02d}'.format(int(episode.scene_season))

            search_string['Season'].append(season_string.encode('utf-8').strip())

        return [search_string]

    def _get_size(self, item):
        try:
            return item.get('size', -1)
        except AttributeError:
            return -1

    def _get_storage_dir(self):
        return ''

    def _get_title_and_url(self, item):
        if not item:
            return '', ''

        title = item.get('title', '')
        url = item.get('link', '')

        if title:
            title = '' + title.replace(' ', '.')
        else:
            title = ''

        if url:
            url = url.replace('&amp;', '&').replace('%26tr%3D', '&tr=')
        else:
            url = ''

        return title, url

    @staticmethod
    def hash_from_magnet(magnet):
        try:
            torrent_hash = re.findall(r'urn:btih:([\w]{32,40})', magnet)[0].upper()
            if len(torrent_hash) == 32:
                torrent_hash = b16encode(b32decode(torrent_hash)).upper()
            return torrent_hash
        except Exception:
            logger.log('Unable to extract torrent hash or name from magnet: {0}'.format(magnet), logger.ERROR)
            return ''

    def _make_url(self, result):
        if not result:
            return '', ''

        filename = ''

        result.url = result.url.replace('http://itorrents.org', 'https://itorrents.org')

        urls = [result.url]
        if result.url.startswith('magnet'):
            torrent_hash = self.hash_from_magnet(result.url)
            if not torrent_hash:
                return urls, filename

            try:
                torrent_name = re.findall('dn=([^&]+)', result.url)[0]
            except Exception:
                torrent_name = 'NO_DOWNLOAD_NAME'

            urls = []
            for cache_url in self.bt_cache_urls:
                if isinstance(cache_url, tuple):
                    urls.append(
                        (cache_url[0].format(torrent_hash=torrent_hash, torrent_name=torrent_name),
                         cache_url[1].format(torrent_hash=torrent_hash, torrent_name=torrent_name)))
                else:
                    urls.append(cache_url.format(torrent_hash=torrent_hash, torrent_name=torrent_name))

        if 'torrage.info/torrent.php' in result.url:
            torrent_hash = result.url.split('=')[1]
            urls = [(
                'https://t.torrage.info/download?h={torrent_hash}'.format(torrent_hash=torrent_hash),
                'https://torrage.info/torrent.php?h={torrent_hash}'.format(torrent_hash=torrent_hash)
            )]

        filename = ek(join, self._get_storage_dir(), sanitize_filename(result.name) + '.' + self.provider_type)

        return urls, filename

    def _verify_download(self, file_name):
        return True

    def add_cookies_from_ui(self):
        """
        Adds the cookies configured from UI to the providers requests session
        :return: A tuple with the the (success result, and a descriptive message in str)
        """

        # This is the generic attribute used to manually add cookies for provider authentication
        if self.enable_cookies and self.cookies:
            cookie_validator = re.compile(r'^(\w+=\w+)(;\w+=\w+)*$')
            if not cookie_validator.match(self.cookies):
                return False, 'Cookie is not correctly formatted: {0}'.format(self.cookies)
            add_dict_to_cookiejar(self.session.cookies, dict(x.rsplit('=', 1) for x in self.cookies.split(';')))
            return True, 'torrent cookie'

        return False, 'No Cookies added from ui for provider: {0}'.format(self.name)
