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

import datetime
import time
from urllib import urlencode

from sickbeard import logger, tvcache
from sickbeard.indexers.indexer_config import INDEXER_TVDB

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class RarbgProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "Rarbg")

        self.public = True
        self.ratio = None
        self.minseed = None
        self.ranked = None
        self.sorting = None
        self.minleech = None
        self.token = None
        self.token_expires = None

        # Spec: https://torrentapi.org/apidocs_v2.txt
        self.url = u'https://rarbg.com'
        self.url_api = u'http://torrentapi.org/pubapi_v2.php'

        self.proper_strings = ['{{PROPER|REPACK}}']

        self.cache = tvcache.TVCache(self, min_time=10)  # only poll RARBG every 10 minutes max

    def login(self):
        if self.token and self.token_expires and datetime.datetime.now() < self.token_expires:
            return True

        login_params = {
            'get_token': 'get_token',
            'format': 'json',
            'app_id': 'sickrage2'
        }

        response = self.get_url(self.url_api, params=login_params, timeout=30, json=True)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        self.token = response.get('token')
        self.token_expires = datetime.datetime.now() + datetime.timedelta(minutes=14) if self.token else None
        return self.token is not None

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals
        results = []
        if not self.login():
            return results

        search_params = {
            'app_id': 'sickrage2',
            'category': 'tv',
            'min_seeders': try_int(self.minseed),
            'min_leechers': try_int(self.minleech),
            'limit': 100,
            'format': 'json_extended',
            'ranked': try_int(self.ranked),
            'token': self.token,
        }

        if ep_obj is not None:
            ep_indexerid = ep_obj.show.indexerid
            ep_indexer = ep_obj.show.indexer
        else:
            ep_indexerid = None
            ep_indexer = None

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            if mode == 'RSS':
                search_params['sort'] = 'last'
                search_params['mode'] = 'list'
                search_params.pop('search_string', None)
                search_params.pop('search_tvdb', None)
            else:

                search_params['sort'] = self.sorting if self.sorting else 'seeders'
                search_params['mode'] = 'search'

                if ep_indexer == INDEXER_TVDB and ep_indexerid:
                    search_params['search_tvdb'] = ep_indexerid
                else:
                    search_params.pop('search_tvdb', None)

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    search_params['search_string'] = search_string
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                logger.log(u"Search URL: %s" % self.url_api + '?' + urlencode(search_params), logger.DEBUG)
                data = self.get_url(self.url_api, params=search_params, json=True)
                if not all([isinstance(data, dict), data.get('torrent_results')]):
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                for item in data.get('torrent_results', []):
                    try:
                        title = item.get('title')
                        download_url = item.get('download')
                        seeders = item.get('seeders', 0)
                        leechers = item.get('leechers', 0)
                        size = convert_size(item.get('size', -1)) or -1
                    except Exception:
                        logger.log(u"Skipping invalid result. JSON item: %s" % item, logger.DEBUG)
                        continue

                    if not all([title, download_url]):
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode != 'RSS':
                        logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)
                    items.append(item)

                time.sleep(10)

            # For each search mode sort all the items by seeders
            items.sort(key=lambda tup: tup[3], reverse=True)
            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = RarbgProvider()
