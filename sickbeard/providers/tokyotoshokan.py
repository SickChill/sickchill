# coding=utf-8
# Author: Mr_Orange
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

from __future__ import print_function, unicode_literals

import re

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class TokyoToshokanProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "TokyoToshokan")

        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True

        self.minseed = None
        self.minleech = None

        self.url = 'https://www.tokyotosho.info/'
        self.urls = {
            'search': self.url + 'search.php',
            'rss': self.url + 'rss.php'
        }
        self.cache = tvcache.TVCache(self, min_time=15)  # only poll TokyoToshokan every 15 minutes max

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        if not self.show or not self.show.is_anime:
            return results

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_params = {
                    "terms": search_string,
                    "type": 1,  # get anime types
                }

                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as soup:
                    torrent_table = soup.find('table', class_='listing')
                    torrent_rows = torrent_table('tr') if torrent_table else []

                    # Continue only if one Release is found
                    if len(torrent_rows) < 2:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    a = 1 if len(torrent_rows[0]('td')) < 2 else 0

                    for top, bot in zip(torrent_rows[a::2], torrent_rows[a + 1::2]):
                        try:
                            desc_top = top.find('td', class_='desc-top')
                            title = desc_top.get_text(strip=True)
                            download_url = desc_top.find('a')['href']

                            desc_bottom = bot.find('td', class_='desc-bot').get_text(strip=True)
                            size = convert_size(desc_bottom.split('|')[1].strip('Size: ')) or -1

                            stats = bot.find('td', class_='stats').get_text(strip=True)
                            sl = re.match(r'S:(?P<seeders>\d+)L:(?P<leechers>\d+)C:(?:\d+)ID:(?:\d+)', stats.replace(' ', ''))
                            seeders = try_int(sl.group('seeders')) if sl else 0
                            leechers = try_int(sl.group('leechers')) if sl else 0
                        except StandardError:
                            continue

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                        if mode != 'RSS':
                            logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                        items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results

provider = TokyoToshokanProvider()
