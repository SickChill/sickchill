# -*- coding: latin-1 -*-
# Author: adaur <adaur.underground@gmail.com>
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
import requests
from urllib import urlencode

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.providers.torrent.TorrentProvider import TorrentProvider

from sickrage.helper.common import try_int, convert_size


class PhxBitProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "PhxBit")

        self.url = 'https://phxbit.com'
        self.urls = {
            'login': self.url + '/connect.php',
            'search': self.url + '/sphinx.php?'
        }

        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.username = None
        self.password = None
        self.proper_strings = ['PROPER']
        self.cache = PhxBitCache(self)

    def login(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('dons.php', response):
            return True
        else:
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if not self.login():
            return results

        search_params = {
            'exact': 1,
            'order': 'desc',
            'sort': 'normal',
            'group': 'series'
        }

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                search_params['q'] = search_string
                search_url = self.urls['search'] + urlencode(search_params)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)
                data = self.get_url(search_url)
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find("table")
                    torrent_rows = []
                    if torrent_table:
                        torrent_rows = torrent_table.find_all("tr")

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    def process_column_header(td):
                        result = ''
                        if td.img:
                            result = td.img.get('alt', '')
                        if not result:
                            result = td.get_text(strip=True)
                        return result

                    # Cat�gorie, Nom,  DL, Com, Taille, C, Seed, Leech,	Share
                    labels = [process_column_header(label) for label in torrent_rows[0].find_all('td')]

                    # We don't loop through the latest entry
                    for row in torrent_rows[1:]:
                        cells = row.find_all('td')
                        if len(cells) < len(labels):
                            continue

                        try:
                            title = cells[labels.index('Nom')].get_text(strip=True)
                            download_url = cells[labels.index('DL')].find('a')['href']
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index('Seed')].get_text(strip=True))
                            leechers = try_int(cells[labels.index('Leech')].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            size = convert_size(cells[labels.index('Taille')].get_text(strip=True)) or -1

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items.append(item)

                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio


class PhxBitCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}


provider = PhxBitProvider()
