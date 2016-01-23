# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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

import posixpath  # Must use posixpath
import re
from urllib import urlencode

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class ThePirateBayProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "ThePirateBay")

        self.public = True

        self.ratio = None
        self.confirmed = True
        self.minseed = None
        self.minleech = None

        self.cache = tvcache.TVCache(self, min_time=30)  # only poll ThePirateBay every 30 minutes max

        self.url = 'https://thepiratebay.se/'
        self.urls = {
            'search': self.url + 's/',
            'rss': self.url + 'tv/latest'
        }

        self.custom_url = None

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        """
        205 = SD, 208 = HD, 200 = All Videos
        https://pirateproxy.pl/s/?q=Game of Thrones&type=search&orderby=7&page=0&category=200
        """
        search_params = {
            'q': '',
            'type': 'search',
            'orderby': 7,
            'page': 0,
            'category': 200
        }

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                search_params['q'] = search_string.strip()

                search_url = self.urls[('search', 'rss')[mode == 'RSS']] + '?' + urlencode(search_params)
                if self.custom_url:
                    search_url = posixpath.join(self.custom_url, search_url.split(self.url)[1].lstrip('/'))  # Must use posixpath

                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                data = self.get_url(search_url)
                if not data:
                    logger.log(u'URL did not return data, maybe try a custom url, or a different one', logger.DEBUG)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('table', id='searchResult')
                    torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                    # Continue only if one Release is found
                    if len(torrent_rows) < 2:
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    def process_column_header(th):
                        result = ''
                        if th.a:
                            result = th.a.get_text(strip=True)
                        if not result:
                            result = th.get_text(strip=True)
                        return result

                    labels = [process_column_header(label) for label in torrent_rows[0].find_all('th')]
                    for result in torrent_rows[1:]:
                        try:
                            cells = result.find_all('td')

                            title = result.find(class_='detName').get_text(strip=True)
                            download_url = result.find(title="Download this torrent using magnet")['href']
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index('SE')].get_text(strip=True))
                            leechers = try_int(cells[labels.index('LE')].get_text(strip=True))
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            # Accept Torrent only from Good People for every Episode Search
                            if self.confirmed and not result.find(alt=re.compile(r'VIP|Trusted')):
                                if mode != 'RSS':
                                    logger.log(u"Found result %s but that doesn't seem like a trusted result so I'm ignoring it" % title, logger.DEBUG)
                                continue

                            # Convert size after all possible skip scenarios
                            torrent_size = cells[labels.index('Name')].find(class_='detDesc').get_text(strip=True).split(', ')[1]
                            torrent_size = re.sub(r'Size ([\d.]+).+([KMGT]iB)', r'\1 \2', torrent_size)
                            size = convert_size(torrent_size) or -1

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = ThePirateBayProvider()
