# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class StrikeProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Strike")

        self.public = True
        self.url = 'https://getstrike.net/'
        params = {'RSS': ['x264']}  # Use this hack for RSS search since most results will use this codec
        self.cache = tvcache.TVCache(self, min_time=10, search_params=params)
        self.minseed, self.minleech = 2 * [None]

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        for mode in search_strings:  # Mode = RSS, Season, Episode
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: " + search_string.strip(), logger.DEBUG)

                search_url = self.url + "api/v2/torrents/search/?category=TV&phrase=" + search_string
                jdata = self.get_url(search_url, returns='json')
                if not jdata:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    return []

                results = []

                for item in jdata['torrents']:
                    seeders = ('seeds' in item and item['seeds']) or 0
                    leechers = ('leeches' in item and item['leeches']) or 0
                    title = ('torrent_title' in item and item['torrent_title']) or ''
                    torrent_size = ('size' in item and item['size'])
                    size = convert_size(torrent_size) or -1
                    download_url = ('magnet_uri' in item and item['magnet_uri']) or ''

                    if not all([title, download_url]):
                        continue

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                       (title, seeders, leechers), logger.DEBUG)
                        continue

                    if mode != 'RSS':
                        logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': None}
                    items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results


provider = StrikeProvider()
