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

from __future__ import print_function, unicode_literals

import re

from requests.compat import urljoin
from requests.utils import dict_from_cookiejar
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickbeard.show_name_helpers import allPossibleShowNames
from sickrage.helper.common import convert_size, try_int
from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


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
        self.minseed = None
        self.minleech = None
        self.freeleech = None

        # URLs
        self.url = 'https://www.morethan.tv/'
        self.urls = {
            'login': urljoin(self.url, 'login.php'),
            'search': urljoin(self.url, 'torrents.php'),
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

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Your username or password was incorrect.', response):
            logger.log("Invalid username or password. Check your settings", logger.WARNING)
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
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                if mode == 'Season':
                    searchedSeason = re.match('.*\s(Season\s\d+|S\d\d+)', search_string).group(1)

                search_params['searchstr'] = search_string
                data = self.get_url(self.urls['search'], params=search_params, returns='text')

                if not data:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('table', class_='torrent_table')
                    torrent_rows = torrent_table('tr') if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    labels = [process_column_header(label) for label in torrent_rows[0]('td')]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        try:
                            # skip if torrent has been nuked due to poor quality
                            if result.find('img', alt='Nuked'):
                                continue

                            title = result.find('a', title='View torrent').get_text(strip=True)

                            if mode == 'Season':
                                # Skip if torrent isn't the right season, we can't search
                                # for an exact season on MTV, it returns all of them
                                if searchedSeason not in title:
                                    continue
                                # If torrent is grouped, we need a folder name for title
                                if 'Season' in title:
                                    torrentid = urljoin(self.url, result.find('span', title='Download').parent['href'])
                                    torrentid = re.match('.*?id=([0-9]+)', torrentid).group(1)

                                    group_params = {
                                        'torrentid': 'torrentid'
                                    }

                                    # Obtain folder name to use as title
                                    torrentInfo = self.get_url(self.urls['search'],params=group_params,
                                                               returns='text').replace('\n', '')

                                    releaseregex = '.*files_{0}.*?;">/(.+?(?=/))'.format(torrentid)
                                    releasename = re.search(releaseregex, torrentInfo).group(1)
                                    title = releasename


                            download_url = urljoin(self.url, result.find('span', title='Download').parent['href'])
                            if not all([title, download_url]):
                                continue

                            cells = result('td')
                            seeders = try_int(cells[labels.index('Seeders')].get_text(strip=True))
                            leechers = try_int(cells[labels.index('Leechers')].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log("Discarding torrent because it doesn't meet the"
                                               " minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            torrent_size = cells[labels.index('Size')].get_text(strip=True)
                            size = convert_size(torrent_size, units=units) or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results

    def _get_season_search_strings(self, episode):
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
                # MTV renames most season packs to just "Season ##"
                mtv_season_string = '{0} Season {1}'.format(show_name, int(episode.scene_season))
                search_string['Season'].append(mtv_season_string.encode('utf-8').strip())

            search_string['Season'].append(season_string.encode('utf-8').strip())

        return [search_string]
		

provider = MoreThanTVProvider()
