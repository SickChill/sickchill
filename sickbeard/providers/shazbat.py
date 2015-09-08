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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import generic

from sickbeard.exceptions import AuthException
from sickbeard import logger
from sickbeard import tvcache


class ShazbatProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "Shazbat.tv")

        self.supportsBacklog = False

        self.enabled = False
        self.passkey = None
        self.ratio = None
        self.options = None

        self.cache = ShazbatCache(self)

        self.urls = {'base_url': 'http://www.shazbat.tv/'}
        self.url = self.urls['base_url']

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'shazbat.png'

    def _checkAuth(self):
        if not self.passkey:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _checkAuthFromData(self, data):
        if not self.passkey:
            self._checkAuth()
        elif not (data['entries'] and data['feed']):
            logger.log(u"Incorrect authentication credentials for " + self.name, logger.DEBUG)
            raise AuthException(
                u"Your authentication credentials for " + self.name + " are incorrect, check your config")

        return True

    def seedRatio(self):
        return self.ratio


class ShazbatCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # only poll Shazbat feed every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):

        rss_url = self.provider.url + 'rss/recent?passkey=' + provider.passkey + '&fname=true'
        logger.log(self.provider.name + u" cache update URL: " + rss_url, logger.DEBUG)

        return self.getRSSFeed(rss_url, items=['entries', 'feed'])

    def _checkAuth(self, data):
        return self.provider._checkAuthFromData(data)

provider = ShazbatProvider()
