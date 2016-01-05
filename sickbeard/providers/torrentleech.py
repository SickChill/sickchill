# coding=utf-8
# Author: Idan Gutman
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import re
import urllib

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.providers.torrent.TorrentProvider import TorrentProvider

from sickrage.helper.common import try_int


class TorrentLeechProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "TorrentLeech")

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls = {'base_url': 'https://torrentleech.org/',
                     'login': 'https://torrentleech.org/user/account/login/',
                     'detail': 'https://torrentleech.org/torrent/%s',
                     'search': 'https://torrentleech.org/torrents/browse/index/query/%s/categories/%s',
                     'download': 'https://torrentleech.org%s',
                     'index': 'https://torrentleech.org/torrents/browse/index/categories/%s'}

        self.url = self.urls['base_url']

        self.categories = "2,7,26,27,32,34,35"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TorrentLeechCache(self)

    def login(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'remember_me': 'on',
                        'login': 'submit'}

        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Invalid Username/password', response) or re.search('<title>Login :: TorrentLeech.org</title>', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self.login():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode == 'RSS':
                    searchURL = self.urls['index'] % self.categories
                else:
                    searchURL = self.urls['search'] % (urllib.quote_plus(search_string.encode('utf-8')), self.categories)
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                data = self.get_url(searchURL)
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('table', id='torrenttable')
                    torrent_rows = []
                    if torrent_table:
                        torrent_rows = torrent_table.find_all('tr')

                    # Continue only if one Release is found
                    if len(torrent_rows) < 2:
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    labels = [label.get_text(strip=True) for label in torrent_rows[0].find_all('td')]
                    for result in torrent_rows[1:]:
                        try:
                            title = result.find('td', class_='name').find('a').get_text(strip=True)
                            download_url = self.urls['download'] % \
                                result.find('td', class_='quickdownload').find('a')['href']

                            seeders = try_int(result.find('td', class_='seeders').get_text(strip=True))
                            leechers = try_int(result.find('td', class_='leechers').get_text(strip=True))
                            size = self._convertSize(result.find_all('td')[labels.index('Size')].get_text(strip=True))
                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        item = title, download_url, size, seeders, leechers
                        if mode != 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                        items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio

    @staticmethod
    def _convertSize(size):
        modifier = size[-2:].upper()
        size = size[:-2].strip()
        try:
            size = float(size)
            if modifier in 'KB':
                size = size * 1024 ** 1
            elif modifier in 'MB':
                size = size * 1024 ** 2
            elif modifier in 'GB':
                size = size * 1024 ** 3
            elif modifier in 'TB':
                size = size * 1024**4
            else:
                raise
        except Exception:
            size = -1

        return long(size)

class TorrentLeechCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll TorrentLeech every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider.search(search_params)}


provider = TorrentLeechProvider()
