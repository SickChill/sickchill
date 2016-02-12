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

import re

from requests.compat import urlencode, urljoin

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class ThePirateBayProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "ThePirateBay")

        # Credentials
        self.public = True

        # Torrent Stats
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = None
        self.confirmed = True

        # URLs
        self.url = 'https://thepiratebay.se'
        self.urls = {
            'rss': self.url + '/browse/200',
            'search': self.url + '/s/',
        }
        self.custom_url = None

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)  # only poll ThePirateBay every 30 minutes max

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branche, too-many-statements
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

        # Units
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

        def process_column_header(th):
            result = ''
            if th.a:
                result = th.a.get_text(strip=True)
            if not result:
                result = th.get_text(strip=True)
            return result

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {search}".format(search=search_string.decode('utf-8')),
                               logger.DEBUG)

                search_params['q'] = search_string.strip()

                search_url = self.urls['search'] + '?' + urlencode(search_params) if mode != 'RSS' else self.urls['rss']
                if self.custom_url:
                    search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                data = self.get_url(search_url)
                if not data:
                    logger.log(u'URL did not return data, maybe try a custom url, or a different one', logger.DEBUG)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('table', id='searchResult')
                    torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    labels = [process_column_header(label) for label in torrent_rows[0].find_all('th')]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        try:
                            cells = result.find_all('td')

                            title = result.find(class_='detName').get_text(strip=True)
                            download_url = result.find(title="Download this torrent using magnet")['href'] + self._custom_trackers
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index('SE')].get_text(strip=True))
                            leechers = try_int(cells[labels.index('LE')].get_text(strip=True))

                            # Filter unseeded torrent
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
                            size = convert_size(torrent_size, units=units) or -1

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
