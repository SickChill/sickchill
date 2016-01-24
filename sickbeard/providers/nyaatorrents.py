# coding=utf-8
# Author: Mr_Orange
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

import re
from urllib import urlencode

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class NyaaProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "NyaaTorrents")

        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True
        self.ratio = None

        self.cache = tvcache.TVCache(self, min_time=15)  # only poll NyaaTorrents every 15 minutes max

        self.urls = {'base_url': 'http://www.nyaa.se/'}

        self.url = self.urls['base_url']

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        if self.show and not self.show.is_anime:
            return results

        for mode in search_strings:
            items = []
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

                search_url = self.url + '?' + urlencode(params)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                summary_regex = ur"(\d+) seeder\(s\), (\d+) leecher\(s\), \d+ download\(s\) - (\d+.?\d* [KMGT]iB)(.*)"
                s = re.compile(summary_regex, re.DOTALL)

                results = []
                for curItem in self.cache.getRSSFeed(search_url)['entries'] or []:
                    title = curItem['title']
                    download_url = curItem['link']
                    if not all([title, download_url]):
                        continue

                    seeders, leechers, torrent_size, verified = s.findall(curItem['summary'])[0]
                    size = convert_size(torrent_size) or -1

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
                        logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                    items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)
            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = NyaaProvider()
