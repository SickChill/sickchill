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

from __future__ import unicode_literals

import re

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class NyaaProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, 'NyaaTorrents')

        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True

        self.url = 'http://www.nyaa.se'

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

        self.regex = re.compile(r'(\d+) seeder\(s\), (\d+) leecher\(s\), \d+ download\(s\) - (\d+.?\d* [KMGT]iB)(.*)', re.DOTALL)

        self.cache = tvcache.TVCache(self, min_time=20)  # only poll NyaaTorrents every 20 minutes max

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if self.show and not self.show.is_anime:
            return results

        for mode in search_strings:
            items = []
            logger.log(u'Search Mode: {0}'.format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u'Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)

                search_params = {
                    'page': 'rss',
                    'cats': '1_0',  # All anime
                    'sort': 2,  # Sort Descending By Seeders
                    'order': 1
                }
                if mode != 'RSS':
                    search_params['term'] = search_string

                results = []
                data = self.cache.getRSSFeed(self.url, params=search_params)['entries']
                if not data:
                    logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)

                for curItem in data:
                    try:
                        title = curItem['title']
                        download_url = curItem['link']
                        if not all([title, download_url]):
                            continue

                        item_info = self.regex.search(curItem['summary'])
                        if not item_info:
                            logger.log('There was a problem parsing an item summary, skipping: {0}'.format
                                       (title), logger.DEBUG)
                            continue

                        seeders, leechers, torrent_size, verified = item_info.groups()
                        seeders = try_int(seeders)
                        leechers = try_int(leechers)

                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log('Discarding torrent because it doesn\'t meet the'
                                           ' minimum seeders or leechers: {0} (S:{1} L:{2})'.format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        if self.confirmed and not verified and mode != 'RSS':
                            logger.log('Found result {0} but that doesn\'t seem like a verified result so I\'m ignoring it'.format
                                       (title), logger.DEBUG)
                            continue

                        size = convert_size(torrent_size) or -1
                        result = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                        if mode != 'RSS':
                            logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                       (title, seeders, leechers), logger.DEBUG)

                        items.append(result)
                    except StandardError:
                        continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = NyaaProvider()
