# coding=utf-8
# Author: Mr_Orange
#
# URL: https://sick-rage.github.io
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

from __future__ import print_function, unicode_literals

import re

from sickbeard import logger, tvcache
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class NyaaProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, 'Nyaa')

        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True

        self.url = 'https://nyaa.si'

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

        self.cache = tvcache.TVCache(self, min_time=20)  # only poll Nyaa every 20 minutes max

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if self.show and not self.show.is_anime:
            return results

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log('Search string: {0}'.format(search_string.decode('utf-8')), logger.DEBUG)

                search_params = {
                    'page': 'rss',
                    'c': '1_0',  # Category: All anime
                    's': 'id',  # Sort by: 'id'=Date / 'size' / 'name' / 'seeders' / 'leechers' / 'downloads'
                    'o': 'desc',  # Sort direction: asc / desc
                    'f': ('0', '2')[self.confirmed]  # Quality filter: 0 = None / 1 = No Remakes / 2 = Trusted Only
                }
                if mode != 'RSS':
                    search_params['q'] = search_string

                results = []
                data = self.cache.get_rss_feed(self.url, params=search_params)['entries']
                if not data:
                    logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                    continue

                for curItem in data:
                    try:
                        title = curItem['title']
                        download_url = curItem['link']
                        if not all([title, download_url]):
                            continue

                        seeders = try_int(curItem['nyaa_seeders'])
                        leechers = try_int(curItem['nyaa_leechers'])
                        torrent_size = curItem['nyaa_size']
                        info_hash = curItem['nyaa_infohash']

                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log('Discarding torrent because it doesn\'t meet the'
                                           ' minimum seeders or leechers: {0} (S:{1} L:{2})'.format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        size = convert_size(torrent_size, units=['BYTES', 'KIB', 'MIB', 'GIB', 'TIB', 'PIB']) or -1
                        result = {'title': title, 'link': download_url, 'size': size,
                                  'seeders': seeders, 'leechers': leechers, 'hash': info_hash}
                        if mode != 'RSS':
                            logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                       (title, seeders, leechers), logger.DEBUG)

                        items.append(result)
                    except StandardError:
                        continue

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: d.get('seeders', 0), reverse=True)
            results += items

        return results


provider = NyaaProvider()
