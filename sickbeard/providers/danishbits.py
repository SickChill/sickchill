# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
#
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
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
import json

# Third Party Imports
from requests.utils import dict_from_cookiejar

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class DanishbitsProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "Danishbits")

        # Credentials
        self.username = None
        self.passkey = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0
        self.freeleech = True

        # URLs
        self.url = 'https://danishbits.org/'
        self.urls = {
            'login': self.url + 'login.php',
            'search': self.url + 'couchpotato.php',
        }

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll Danishbits every 10 minutes max

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            'user': self.username,
            'passkey': self.passkey,
            'search': '.',  # Dummy query for RSS search, needs the search param sent.
            'latest': 'true'
        }

        # Units
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

        def process_column_header(td):
            result = ''
            if td.img:
                result = td.img.get('title')
            if not result:
                result = td.get_text(strip=True)
            return result.encode('utf-8')

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                    search_params['latest'] = 'false'
                    search_params['search'] = search_string

                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                result = json.loads(data)
                if 'results' in result:
                    for torrent in result['results']:
                        title = torrent['release_name']
                        download_url = torrent['download_url']
                        seeders  = torrent['seeders']
                        leechers  = torrent['leechers']
                        if seeders < self.minseed or leechers < self.minleech:
                            logger.log("Discarded {0} because with {1}/{2} seeders/leechers does not meet the requirement of {3}/{4} seeders/leechers".format(title, seeders, leechers, self.minseed, self.minleech))
                            continue

                        freeleech = torrent['freeleech']
                        if self.freeleech and not freeleech:
                            continue

                        size = torrent['size']
                        size = convert_size(size, units=units) or -1
                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                'leechers': leechers, 'hash': ''}
                        logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                                    (title, seeders, leechers), logger.DEBUG)
                        items.append(item)

                if 'error' in result:
                    logger.log(result['error'], logger.WARNING)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = DanishbitsProvider()
