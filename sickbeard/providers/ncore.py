# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Fre$
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or$
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import json
import re

from sickbeard import logger, tvcache
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class NcoreProvider(TorrentProvider): # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "ncore.cc")
        self.username = None
        self.password = None
        self.minseed = None
        self.minleech = None

        categories = [
            'xvidser_hun', 'xvidser',
            'dvdser_hun', 'dvdser',
            'hdser_hun', 'hdser'
        ]
        categories = '&'.join(['kivalasztott_tipus[]=' + x for x in categories])
		
        self.url = 'https://ncore.cc/'
        self.urls = {
            'login': 'https://ncore.cc/login.php',
            'search': ('https://ncore.cc/torrents.php?nyit_sorozat_resz=true&{cats}&mire=%s&miben=name'
                       '&tipus=kivalasztottak_kozott&submit.x=0&submit.y=0&submit=Ok'
                       '&tags=&searchedfrompotato=true&jsons=true').format(cats=categories),
		}
        
        self.cache = tvcache.TVCache(self)

    def login(self):

        login_params = {
            'nev': self.username,
            'pass': self.password,
            'submitted': '1',
        }

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        if re.search('images/warning.png', response):
            logger.log("Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None): # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:
                if mode != "RSS":
                    logger.log("Search string: {0}".format(search_string.decode("utf-8")), logger.DEBUG)

                url = self.urls['search'] % (search_string)
                data = self.get_url(url, returns="text")

                try:
                  parsed_json = json.loads(data)
                except ValueError as e:
                  continue

                if not isinstance(parsed_json, dict):
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                torrent_results = parsed_json['total_results']

                if not torrent_results:
                    logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue

                logger.log('Number of torrents found on nCore = ' + str(torrent_results), logger.INFO)

                for item in parsed_json['results']:
                    try:
                        title = item.pop("release_name")
                        download_url = item.pop("download_url")
                        if not all([title, download_url]):
                            continue

                        seeders = item.pop("seeders")
                        leechers = item.pop("leechers")

                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        torrent_size = item.pop("size", -1)
                        size = convert_size(torrent_size) or -1

                        if mode != "RSS":
                            logger.log("Found result: {0} with {1} seeders and {2} leechers with a file size {3}".format(title, seeders, leechers, size), logger.DEBUG)

                            result = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                        items.append(result)

                    except StandardError:
                        continue

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items
        return results

provider = NcoreProvider()
