# Author: Mr_Orange <mr_orange@hotmail.it>
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
from urllib import urlencode

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.common import USER_AGENT


class ThePirateBayProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "ThePirateBay")

        self.supportsBacklog = True
        self.public = True

        self.ratio = None
        self.confirmed = True
        self.minseed = None
        self.minleech = None

        self.cache = ThePirateBayCache(self)

        self.urls = {
            'base_url': 'https://pirateproxy.la/',
            'search': 'https://pirateproxy.la/s/',
            'rss': 'https://pirateproxy.la/tv/latest'
        }

        self.url = self.urls['base_url']
        self.headers.update({'User-Agent': USER_AGENT})

        """
        205 = SD, 208 = HD, 200 = All Videos
        https://thepiratebay.gd/s/?q=Game of Thrones&type=search&orderby=7&page=0&category=200
        """
        self.search_params = {
            'q': '',
            'type': 'search',
            'orderby': 7,
            'page': 0,
            'category': 200
        }

        self.re_title_url = r'/torrent/(?P<id>\d+)/(?P<title>.*?)".+?(?P<url>magnet.*?)".+?Size (?P<size>[\d\.]*&nbsp;[TGKMiB]{2,3}).+?(?P<seeders>\d+)</td>.+?(?P<leechers>\d+)</td>'

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                self.search_params.update({'q': search_string.strip()})

                if mode is not 'RSS':
                    logger.log(u"Search string: " + search_string, logger.DEBUG)

                searchURL = self.urls[('search', 'rss')[mode is 'RSS']] + '?' + urlencode(self.search_params)
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                data = self.getURL(searchURL)
                # data = self.getURL(self.urls[('search', 'rss')[mode is 'RSS']], params=self.search_params)
                if not data:
                    continue

                matches = re.compile(self.re_title_url, re.DOTALL).finditer(data)
                for torrent in matches:
                    title = torrent.group('title')
                    download_url = torrent.group('url')
                    # id = int(torrent.group('id'))
                    size = self._convertSize(torrent.group('size'))
                    seeders = int(torrent.group('seeders'))
                    leechers = int(torrent.group('leechers'))

                    if not all([title, download_url]):
                        continue

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode is not 'RSS':
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        continue

                    # Accept Torrent only from Good People for every Episode Search
                    if self.confirmed and re.search(r'(VIP|Trusted|Helper|Moderator)', torrent.group(0)) is None:
                        if mode is not 'RSS':
                            logger.log(u"Found result %s but that doesn't seem like a trusted result so I'm ignoring it" % title, logger.DEBUG)
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode is not 'RSS':
                        logger.log(u"Found result: %s " % title, logger.DEBUG)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _convertSize(self, size):
        size, modifier = size.split('&nbsp;')
        size = float(size)
        if modifier in 'KiB':
            size = size * 1024
        elif modifier in 'MiB':
            size = size * 1024**2
        elif modifier in 'GiB':
            size = size * 1024**3
        elif modifier in 'TiB':
            size = size * 1024**4
        return size

    def seedRatio(self):
        return self.ratio


class ThePirateBayCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll ThePirateBay every 30 minutes max
        self.minTime = 30

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = ThePirateBayProvider()
