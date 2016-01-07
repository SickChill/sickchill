# coding=utf-8
# Author: Gonçalo (aka duramato) <matigonkas@outlook.com>
# URL: https://github.com/SickRage/SickRage
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

from sickbeard import logger
from sickbeard import tvcache
from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class STRIKEProvider(TorrentProvider):

    def __init__(self):
        TorrentProvider.__init__(self, "Strike")

        self.public = True
        self.url = 'https://getstrike.net/'
        self.ratio = 0
        self.cache = StrikeCache(self)
        self.minseed, self.minleech = 2 * [None]

    def search(self, search_strings, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():  # Mode = RSS, Season, Episode
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: " + search_string.strip(), logger.DEBUG)

                searchURL = self.url + "api/v2/torrents/search/?category=TV&phrase=" + search_string
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                jdata = self.get_url(searchURL, json=True)
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
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        continue

                    if mode != 'RSS':
                        logger.log(u"Found result: %s " % title, logger.DEBUG)

                    item = title, download_url, size, seeders, leechers
                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio


class StrikeCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Cache results for 10 min
        self.minTime = 10

    def _getRSSData(self):

        # Use this hacky way for RSS search since most results will use this codec
        search_params = {'RSS': ['x264']}
        return {'entries': self.provider.search(search_params)}

provider = STRIKEProvider()
