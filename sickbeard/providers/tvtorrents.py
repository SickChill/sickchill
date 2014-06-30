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

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree

import sickbeard
import generic

from sickbeard.exceptions import ex, AuthException
from sickbeard import helpers
from sickbeard import logger
from sickbeard import tvcache


class TvTorrentsProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "TvTorrents")

        self.supportsBacklog = False

        self.enabled = False
        self.hash = None
        self.digest = None
        self.ratio = None
        self.options = None

        self.cache = TvTorrentsCache(self)

        self.url = 'http://www.tvtorrents.com/'

    def __del__(self):
        pass

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'tvtorrents.png'

    def _checkAuth(self):

        if not self.digest or not self.hash:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _checkAuthFromData(self, data):

        if data is None or data.feed is None:
            return self._checkAuth()

        description_text = data.feed.title

        if "User can't be found" in description_text or "Invalid Hash" in description_text:
            logger.log(u"Incorrect authentication credentials for " + self.name + " : " + str(description_text),
                       logger.DEBUG)
            raise AuthException(
                u"Your authentication credentials for " + self.name + " are incorrect, check your config")

        return True

    def seedRatio(self):
        return self.ratio


class TvTorrentsCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # only poll TvTorrents every 15 minutes max
        self.minTime = 15

    def __del__(self):
        pass

    def _getRSSData(self):
        # These will be ignored on the serverside.
        ignore_regex = "all.month|month.of|season[\s\d]*complete"

        rss_url = self.provider.url + 'RssServlet?digest=' + provider.digest + '&hash=' + provider.hash + '&fname=true&exclude=(' + ignore_regex + ')'
        logger.log(self.provider.name + u" cache update URL: " + rss_url, logger.DEBUG)

        return self.getRSSFeed(rss_url)

    def _checkAuth(self, data):
        return self.provider._checkAuthFromData(data)


provider = TvTorrentsProvider()
