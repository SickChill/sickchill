# coding=utf-8
# Author: Jodi Jones <venom@gen-x.co.nz>
# URL: http://code.google.com/p/sickbeard/
# Rewrite: Gonçalo <matigonkas@outlook.com>
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

from urllib import urlencode
from sickbeard import logger
from sickbeard import tvcache
from sickrage.providers.TorrentProvider import TorrentProvider


class BTDIGGProvider(TorrentProvider):

    def __init__(self):
        TorrentProvider.__init__(self, "BTDigg")

        self.public = True
        self.ratio = 0
        self.urls = {'url': u'https://btdigg.org/',
                     'api': u'https://api.btdigg.org/api/private-341ada3245790954/s02'}

        self.proper_strings = ['PROPER', 'REPACK']

        self.url = self.urls['url']

        # # Unsupported
        # self.minseed = 1
        # self.minleech = 0

        self.cache = BTDiggCache(self)

    def search(self, search_strings, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}
        search_params = {'p': 0}

        for mode in search_strings:
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                search_params['q'] = search_string.encode('utf-8')

                if mode != 'RSS':
                    logger.log(u"Search string: %s" % search_string, logger.DEBUG)
                    search_params['order'] = '0'
                else:
                    search_params['order'] = '2'

                search_url = self.urls['api'] + '?' + urlencode(search_params)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                jdata = self.get_url(search_url, json=True)
                if not jdata:
                    logger.log(u"No data returned to be parsed!!!", logger.DEBUG)
                    continue

                for torrent in jdata:
                    if not torrent['name']:
                        logger.log(u"Ignoring result since it has no name", logger.DEBUG)
                        continue

                    if torrent['ff']:
                        logger.log(u"Ignoring result for %s since it's a fake (level = %s)" % (torrent['name'], torrent['ff']), logger.DEBUG)
                        continue

                    if not torrent['files']:
                        logger.log(u"Ignoring result for %s without files" % torrent['name'], logger.DEBUG)
                        continue

                    download_url = torrent['magnet'] + self._custom_trackers

                    if not download_url:
                        logger.log(u"Ignoring result for %s without a url" % torrent['name'], logger.DEBUG)
                        continue

                    # FIXME
                    seeders = 1
                    leechers = 0

                    # # Filter unseeded torrent (Unsupported)
                    # if seeders < self.minseed or leechers < self.minleech:
                    #    if mode != 'RSS':
                    #        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                    #    continue

                    if mode != 'RSS':
                        logger.log(u"Found result: %s" % torrent['name'], logger.DEBUG)

                    item = torrent['name'], download_url, torrent['size'], seeders, leechers
                    items[mode].append(item)

            # # For each search mode sort all the items by seeders if available (Unsupported)
            # items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio


class BTDiggCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Cache results for a 30min, since BTDigg takes some time to crawl
        self.minTime = 30

    def _getRSSData(self):

        # Use this hacky way for RSS search since most results will use this codecs
        search_params = {'RSS': ['x264', 'x264.HDTV', '720.HDTV.x264']}
        return {'entries': self.provider.search(search_params)}

provider = BTDIGGProvider()
