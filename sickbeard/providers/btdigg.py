# Author: Jodi Jones <venom@gen-x.co.nz>
# URL: http://code.google.com/p/sickbeard/
#
# Ported to sickrage by: matigonkas
#
# This file is part of SickRage.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from sickbeard.providers import generic

from sickbeard import logger
from sickbeard import tvcache

class BTDIGGProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "BTDigg")

        self.supportsBacklog = True
        self.public = True
        self.ratio = 0
        self.urls = {'url': u'https://btdigg.org/',
                     'api': u'https://api.btdigg.org/'}

        self.url = self.urls['url']

        self.cache = BTDiggCache(self)

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s" % search_string, logger.DEBUG)

                searchURL = self.urls['api'] + "api/private-341ada3245790954/s02?q=" + search_string + "&p=0&order=1"
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)

                jdata = self.getURL(searchURL, json=True)
                if not jdata:
                    logger.log(u"No data returned to be parsed!!!")
                    return []

                for torrent in jdata:
                    if not torrent['ff']:
                        title = torrent['name']
                        download_url = torrent['magnet']
                        size = torrent['size']
                        # FIXME
                        seeders = 1
                        leechers = 0

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        # if seeders < self.minseed or leechers < self.minleech:
                        #    if mode is not 'RSS':
                        #        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        #    continue

                        item = title, download_url, size, seeders, leechers
                        if mode is not 'RSS':
                            logger.log(u"Found result: %s" % title, logger.DEBUG)

                        items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

class BTDiggCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Cache results for a hour ,since BTDigg takes some time to crawl
        self.minTime = 60

    def _getRSSData(self):

        # Use x264 for RSS search since most results will use that codec and since the site doesnt have latest results search
        search_params = {'RSS': ['x264']}
        return {'entries': self.provider._doSearch(search_params)}

provider = BTDIGGProvider()
