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

from sickbeard import logger, tvcache

from sickrage.providers.nzb.NZBProvider import NZBProvider


class WombleProvider(NZBProvider):

    def __init__(self):

        NZBProvider.__init__(self, "Womble's Index")

        self.public = True
        self.cache = WombleCache(self, min_time=15)  # only poll Womble's Index every 15 minutes max
        self.urls = {'base_url': 'http://newshost.co.za/'}
        self.url = self.urls['base_url']
        self.supports_backlog = False


class WombleCache(tvcache.TVCache):
    def updateCache(self):
        # check if we should update
        if not self.shouldUpdate():
            return

        # clear cache
        self._clearCache()

        # set updated
        self.setLastUpdate()

        cl = []
        for url in [self.provider.url + 'rss/?sec=tv-x264&fr=false',
                    self.provider.url + 'rss/?sec=tv-sd&fr=false',
                    self.provider.url + 'rss/?sec=tv-dvd&fr=false',
                    self.provider.url + 'rss/?sec=tv-hd&fr=false']:
            logger.log(u"Cache update URL: %s" % url, logger.DEBUG)

            for item in self.getRSSFeed(url)['entries'] or []:
                ci = self._parseItem(item)
                if ci is not None:
                    cl.append(ci)

        if len(cl) > 0:
            cache_db_con = self._getDB()
            cache_db_con.mass_action(cl)

    def _checkAuth(self, data):
        return data if data['feed'] and data['feed']['title'] != 'Invalid Link' else None

provider = WombleProvider()
