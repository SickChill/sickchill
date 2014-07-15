# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
import time

import sickbeard
import generic

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.exceptions import AuthException


class WombleProvider(generic.NZBProvider):
    def __init__(self):
        generic.NZBProvider.__init__(self, "Womble's Index")
        self.enabled = False
        self.cache = WombleCache(self)
        self.url = 'http://newshost.co.za/'

    def isEnabled(self):
        return self.enabled


class WombleCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)
        # only poll Womble's Index every 15 minutes max
        self.minTime = 15

    def updateCache(self):

        # delete anything older then 7 days
        self._clearCache()

        data = None

        if not self.shouldUpdate():
            return

        cl = []
        for url in [self.provider.url + 'rss/?sec=tv-sd&fr=false', self.provider.url + 'rss/?sec=tv-hd&fr=false']:
            logger.log(u"Womble's Index cache update URL: " + url, logger.DEBUG)
            data = self.getRSSFeed(url)

            # As long as we got something from the provider we count it as an update
            if not data:
                return []

            # By now we know we've got data and no auth errors, all we need to do is put it in the database
            for item in data.entries:
                ci = self._parseItem(item)
                if ci is not None:
                    cl.append(ci)



        if len(cl) > 0:
            myDB = self._getDB()
            myDB.mass_action(cl)

        # set last updated
        if data:
            self.setLastUpdate()

    def _checkAuth(self, data):
        return data != 'Invalid Link'

provider = WombleProvider()

