# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://github.com/SickRage/SickRage
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

import re
import traceback
from six.moves import urllib
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.common import USER_AGENT
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TorrentzProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "Torrentz")
        self.public = True
        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.cache = TorrentzCache(self)
        self.headers.update({'User-Agent': USER_AGENT})
        self.urls = {'verified': 'https://torrentz.eu/feed_verified',
                     'feed': 'https://torrentz.eu/feed',
                     'base': 'https://torrentz.eu/'}
        self.url = self.urls['base']

    def seed_ratio(self):
        return self.ratio

    @staticmethod
    def _split_description(description):
        match = re.findall(r'[0-9]+', description)
        return int(match[0]) * 1024 ** 2, int(match[1]), int(match[2])

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []

        for mode in search_strings:
            items = []
            for search_string in search_strings[mode]:
                search_url = self.urls['verified'] if self.confirmed else self.urls['feed']
                if mode != 'RSS':
                    search_url += '?q=' + urllib.parse.quote_plus(search_string)

                data = self.get_url(search_url)
                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                if not data.startswith("<?xml"):
                    logger.log(u"Expected xml but got something else, is your mirror failing?", logger.INFO)
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as parser:
                        for item in parser.findAll('item'):
                            if item.category and 'tv' not in item.category.text:
                                continue

                            title = item.title.text.rsplit(' ', 1)[0].replace(' ', '.')
                            t_hash = item.guid.text.rsplit('/', 1)[-1]

                            if not all([title, t_hash]):
                                continue

                            download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + self._custom_trackers
                            torrent_size, seeders, leechers = self._split_description(item.find('description').text)
                            size = convert_size(torrent_size) or -1

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            items.append((title, download_url, size, seeders, leechers))

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.log(u"Failed parsing provider. Traceback: %r" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)
            results += items

        return results


class TorrentzCache(tvcache.TVCache):

    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        return {'entries': self.provider.search({'RSS': ['']})}

provider = TorrentzProvider()
