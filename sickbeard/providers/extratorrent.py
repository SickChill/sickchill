# coding=utf-8
# Author: duramato <matigonkas@outlook.com>
# Author: miigotu
# URL: https://github.com/SickRage/sickrage
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

import re
import sickbeard
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.common import USER_AGENT
from sickrage.helper.common import try_int
from sickbeard.bs4_parser import BS4Parser
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class ExtraTorrentProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes
    def __init__(self):
        TorrentProvider.__init__(self, "ExtraTorrent")

        self.urls = {
            'index': 'http://extratorrent.cc',
            'rss': 'http://extratorrent.cc/rss.xml',
        }

        self.url = self.urls['index']

        self.public = True
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.custom_url = None

        self.cache = ExtraTorrentCache(self)
        self.headers.update({'User-Agent': USER_AGENT})
        self.search_params = {'cid': 8}

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                self.search_params.update({'type': ('search', 'rss')[mode == 'RSS'], 'search': search_string})
                url = self.urls['rss'] if not self.custom_url else self.urls['rss'].replace(self.urls['index'], self.custom_url)
                data = self.get_url(url, params=self.search_params)
                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                if not data.startswith('<?xml'):
                    logger.log(u'Expected xml but got something else, is your mirror failing?', logger.INFO)
                    continue

                with BS4Parser(data, 'html5lib') as parser:
                    for item in parser.findAll('item'):
                        try:
                            title = re.sub(r'^<!\[CDATA\[|\]\]>$', '', item.find('title').get_text(strip=True))
                            size = try_int(item.find('size').get_text(strip=True), -1)
                            seeders = try_int(item.find('seeders').get_text(strip=True))
                            leechers = try_int(item.find('leechers').get_text(strip=True))

                            if sickbeard.TORRENT_METHOD == 'blackhole':
                                enclosure = item.find('enclosure')  # Backlog doesnt have enclosure
                                download_url = enclosure['url'] if enclosure else item.find('link').next.strip()
                                download_url = re.sub(r'(.*)/torrent/(.*).html', r'\1/download/\2.torrent', download_url)
                            else:
                                info_hash = item.find('info_hash').get_text(strip=True)
                                download_url = "magnet:?xt=urn:btih:" + info_hash + "&dn=" + title + self._custom_trackers

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

                        if not all([title, download_url]):
                            continue

                            # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        item = title, download_url, size, seeders, leechers
                        if mode != 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                        items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio


class ExtraTorrentCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}


provider = ExtraTorrentProvider()
