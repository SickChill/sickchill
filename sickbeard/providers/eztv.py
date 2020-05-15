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

# Third Party Imports
from requests.compat import urljoin

# First Party Imports
import sickbeard
from sickbeard import logger, tvcache
from sickchill.helper.common import try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class EZTVProvider(TorrentProvider):

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "EZTV")

        # Credentials
        self.public = True

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # URLs
        self.url = "https://eztv.io"
        self.api = urljoin(self.url, "api/get-torrents")

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)  # only poll ThePirateBay every 30 minutes max

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        search_params = {
            "imdb_id": None,
            "page": 1,
            "limit": 100
        }

        # Just doing the first page of results, because there is no search filter
        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            if mode != "RSS":
                if not (self.show and self.show.imdbid):
                    continue

                search_params["imdb_id"] = self.show.imdbid.strip('tt')
                logger.log("Search string: {}".format(self.show.imdbid), logger.DEBUG)
            else:
                search_params.pop('imdb_id')

            data = self.get_url(self.api, params=search_params, returns="json")

            if not (data and isinstance(data, dict) and 'torrents' in data):
                logger.log("URL did not return data", logger.DEBUG)
                continue

            for result in data['torrents']:
                try:
                    title = result['title'][0:-5].replace(' ', '.')
                    info_hash = result['hash']
                    if not all([title, info_hash]):
                        continue

                    link = result[('magnet_url', 'torrent_url')[sickbeard.TORRENT_METHOD == 'blackhole']]

                    seeders = result['seeds']
                    leechers = result['peers']

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != "RSS":
                            logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                       (title, seeders, leechers), logger.DEBUG)
                        continue

                    torrent_size = try_int(result['size_bytes'])

                    item = {'title': title, 'link': link, 'size': torrent_size, 'seeders': seeders, 'leechers': leechers, 'hash': info_hash}
                    if mode != "RSS":
                        logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                   (title, seeders, leechers), logger.DEBUG)

                    items.append(item)
                except StandardError:
                    continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = EZTVProvider()
