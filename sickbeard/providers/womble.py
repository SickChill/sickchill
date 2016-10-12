# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
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

from requests.compat import urljoin

from sickbeard import logger, tvcache

from sickrage.providers.nzb.NZBProvider import NZBProvider


class WombleProvider(NZBProvider):

    def __init__(self):

        NZBProvider.__init__(self, 'Womble\'s Index')

        self.public = True

        self.url = 'http://newshost.co.za'
        self.urls = {'rss': urljoin(self.url, 'rss')}
        self.supports_backlog = False

        self.cache = WombleCache(self, min_time=20)


class WombleCache(tvcache.TVCache):
    def updateCache(self):

        if not self.shouldUpdate():
            return

        self._clearCache()
        self.setLastUpdate()

        cl = []
        search_params_list = [{'sec': 'tv-x264'}, {'sec': 'tv-hd'}, {'sec': 'tv-sd'}, {'sec': 'tv-dvd'}]
        for search_params in search_params_list:
            search_params.update({'fr': 'false'})
            data = self.getRSSFeed(self.provider.urls['rss'], params=search_params)['entries']
            if not data:
                logger.log('No data returned from provider', logger.DEBUG)
                continue

            for item in data:
                ci = self._parseItem(item)
                if ci:
                    cl.append(ci)

        if cl:
            cache_db_con = self._getDB()
            cache_db_con.mass_action(cl)

    def _checkAuth(self, data):
        return data if data['feed'] and data['feed']['title'] != 'Invalid Link' else None

provider = WombleProvider()
