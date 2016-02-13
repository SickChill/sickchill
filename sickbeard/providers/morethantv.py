# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
#
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import re

from requests.compat import urlencode
from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.exceptions import AuthException
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider
from sickbeard.show_name_helpers import allPossibleShowNames


class MoreThanTVProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "MoreThanTV")

        # Credentials
        self.username = None
        self.password = None
        self._uid = None
        self._hash = None

        # Torrent Stats
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = None

        # URLs
        self.url = 'https://www.morethan.tv/'
        self.urls = {
            'login': self.url + 'login.php',
            'search': self.url + 'torrents.php',
        }

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK']

        # Cache
        self.cache = tvcache.TVCache(self)

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'keeplogged': '1',
            'login': 'Log in',
        }

        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Your username or password was incorrect.', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            'tags_type': 1,
            'order_by': 'time',
            'order_way': 'desc',
            'action': 'basic',
            'searchsubmit': 1,
            'group_results': 0,
            'searchstr': ''
        }

        # Units
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

        def process_column_header(td):
            result = ''
            if td.a and td.a.img:
                result = td.a.img.get('title', td.a.get_text(strip=True))
            if not result:
                result = td.get_text(strip=True)
            return result

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)

            if str(mode) in ('Season', 'RSS'):
                search_params['group_results'] = 1
            else:
                search_params['group_results'] = 0

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: {search}".format(search=search_string.decode('utf-8')),
                               logger.DEBUG)

                search_params['searchstr'] = search_string

                search_url = "%s?%s" % (self.urls['search'], urlencode(search_params))
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                data = self.get_url(search_url)
                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('table', class_='torrent_table')
                    torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    labels = [process_column_header(label) for label in torrent_rows[0].find_all('td')]

                    season = -1
                    show_name = ''
                    release_type = ''

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        try:
                            # skip if torrent has been nuked due to poor quality
                            if result.find('img', alt='Nuked'):
                                continue

                            # Check if a grouped release follows
                            if 'group' in result['class']:
                                title_group = result.find('a', title='View torrent group').get_text(strip=True)
                                if not title_group or 'Season ' not in title_group:
                                    season = -1
                                    show_name = ''
                                    release_type = ''
                                    continue
                                # Grab the season's number
                                season = try_int(title_group.strip('Season '), -1)

                                # Check if this is the season we are looking for
                                if 'Season %d' % season not in search_string and mode != 'RSS':
                                    season = -1
                                    show_name = ''
                                    release_type = ''
                                    continue

                                # Grab the show name
                                show_name = result.find('div', {'class' : 'tp-showname'}).get_text(strip=True)
                                continue

                            # Check if this torrent belongs to a group
                            elif 'group_torrent' in result['class']:
                                #Check if this is a sub-group
                                if 'edition' in result['class']:
                                    #Grab relase type (HDTV, Web-DL, BluRay)
                                    release_type = result.find('td', {'colspan' : '9'}).get_text(strip=True).split(' ')[3]
                                    continue

                                # Check if the group that the torrent belongs to is valid
                                if season == -1 or show_name == '' or release_type == '':
                                    continue

                                #Grab resolution and codec
                                resolution_codec = result.find('td', {'colspan' : '3'}).get_text(strip=True)
                                resolution = ''
                                codec = resolution_codec.split(' ')[0][1:]
                                quality = resolution_codec.split(' ')[2]
                                if quality != 'SD':
                                    resolution = quality

                                season_str = 'S%02d' % season

                                #Generate the actual title for SickRage
                                if resolution != '':
                                    title = '%s.%s.%s.%s.%s' % (show_name, season_str, resolution, release_type, codec)
                                else:
                                    title = '%s.%s.%s.%s' % (show_name, season_str, release_type, codec)
                                download_url = self.url + result.find('span', title='Download').parent['href']

                                cells = result.find_all('td')
                                seeders = try_int(cells[-2].get_text(strip=True))
                                leechers = try_int(cells[-1].get_text(strip=True))
                            else:
                                title = result.find('a', title='View torrent').get_text(strip=True)
                                download_url = self.url + result.find('span', title='Download').parent['href']
                                cells = result.find_all('td')
                                seeders = try_int(cells[labels.index('Seeders')].get_text(strip=True))
                                leechers = try_int(cells[labels.index('Leechers')].get_text(strip=True))

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the"
                                               u" minimum seeders or leechers: {} (S:{} L:{})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            torrent_size = cells[labels.index('Size')].get_text(strip=True)
                            size = convert_size(torrent_size, units=units) or -1

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: {} with {} seeders and {} leechers".format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)
            results += items

        return results

    #Get search string in compatible 'Season x' mode
    def _get_season_search_strings(self, episode):
        search_string = super(MoreThanTVProvider, self)._get_season_search_strings(episode)

        if not any([episode.show.air_by_date, episode.show.sports, episode.show.anime]):
            for show_name in set(allPossibleShowNames(self.show)):
                episode_string = show_name + ' '
                episode_string += 'Season %d' % int(episode.scene_season)
                search_string[0]['Season'].append(episode_string.encode('utf-8').strip())

        return search_string

    def seed_ratio(self):
        return self.ratio

provider = MoreThanTVProvider()
