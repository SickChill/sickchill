# coding=utf-8
# Author: Naufrage7 <naufrage7@gmail.com>
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
import json

from urllib import quote
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class XbitProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, 'Xbit')

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # URLs
        self.url = 'https://xbit.pw/'
        self.urls = {
            'search': 'api?search='
        }

        # Proper Strings
        self.proper_strings = ['PROPER']

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log('Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)

                try:
                    search_params = {
                        'q': re.sub(r'[()]', '', search_string)
                    }

                    url_search = self.url + self.urls['search'] + quote(search_params['q'])
                    logger.log('Searching with ' + url_search, logger.DEBUG)
                    data = self.get_url(url_search, returns='text')
                    if not data:
                        continue

                    data = json.loads(data)
                    dht_results = data['dht_results']

                    for result in dht_results:
                        if len(result):
                            title = result['NAME']
                            download_link = result['MAGNET']
                            seeders = 0
                            leechers = 0
                            logger.log('Found ' + result['NAME'], logger.DEBUG)
                            item = {'title': title, 'link': download_link, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            items.append(item)

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.log('Failed parsing provider {}.'.format(self.name), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = XbitProvider()
