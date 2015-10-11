# Author: Mr_Orange
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import re

import generic

from sickbeard import show_name_helpers
from sickbeard import logger
from sickbeard.common import Quality
from sickbeard import tvcache
from sickbeard import show_name_helpers


class NyaaProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "NyaaTorrents")

        self.supportsBacklog = True
        self.public = True
        self.supportsAbsoluteNumbering = True
        self.anime_only = True
        self.enabled = False
        self.ratio = None

        self.cache = NyaaCache(self)

        self.urls = {'base_url': 'http://www.nyaa.se/'}

        self.url = self.urls['base_url']

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

    def isEnabled(self):
        return self.enabled

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        if self.show and not self.show.is_anime:
            return []

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: %s" % search_string, logger.DEBUG)

                params = {
                    "page": 'rss',
                    "cats": '1_0',  # All anime
                    "sort": 2,     # Sort Descending By Seeders
                    "order": 1
                }
                if mode != 'RSS':
                    params["term"] = search_string.encode('utf-8')

                searchURL = self.url + '?' + urllib.urlencode(params)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)

                summary_regex = ur"(\d+) seeder\(s\), (\d+) leecher\(s\), \d+ download\(s\) - (\d+.?\d* [KMGT]iB)(.*)"
                s = re.compile(summary_regex, re.DOTALL)

                results = []
                for curItem in self.cache.getRSSFeed(searchURL, items=['entries'])['entries'] or []:
                    title = curItem['title']
                    download_url = curItem['link']
                    if not all([title, download_url]):
                        continue

                    seeders, leechers, size, verified = s.findall(curItem['summary'])[0]
                    size = self._convertSize(size)

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        continue

                    if self.confirmed and not verified and mode != 'RSS':
                        logger.log(u"Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it", logger.DEBUG)
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode != 'RSS':
                        logger.log(u"Found result: %s " % title, logger.DEBUG)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _extract_name_from_filename(self, filename):
        name_regex = '(.*?)\.?(\[.*]|\d+\.TPB)\.torrent$'
        logger.log(u"Comparing %s against %s" % (name_regex, filename), logger.DEBUG)
        match = re.match(name_regex, filename, re.I)
        if match:
            return match.group(1)
        return None

    def _convertSize(self, size):
        size, modifier = size.split(' ')
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


class NyaaCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # only poll NyaaTorrents every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = NyaaProvider()
