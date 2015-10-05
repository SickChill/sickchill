# Author: Jodi Jones <venom@gen-x.co.nz>
# URL: http://code.google.com/p/sickbeard/
#
#Ported to sickrage by: matigonkas
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import generic

from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard.common import WANTED
from sickbeard.config import naming_ep_type
from sickbeard.helpers import sanitizeSceneName

class BTDIGGProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "BTDigg")

        self.supportsBacklog = True
        self.public = True

        self.urls = {'url': u'https://btdigg.org/',
                     'api': u'https://api.btdigg.org/',
                     }
        self.url = self.urls['url']

        self.cache = BTDiggCache(self)

    def isEnabled(self):
        return self.enabled

    def _get_title_and_url(self, item):
        title, url, size = item
        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)


    def _get_size(self, item):
        title, url, size = item

        return size

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        for mode in search_strings.keys():
        
            for search_string in search_strings[mode]:
                # TODO: Make order configurable. 0: weight, 1: req, 2: added, 3: size, 4: files, 5

                if mode != 'RSS':
                    logger.log(u"Search string: %s" %  search_params, logger.DEBUG)
                    
                searchUrl = self.urls['api'] + "api/private-341ada3245790954/s02?q=" + search_string + "&p=0&order=1"
                jdata = self.getURL(searchUrl, json=True)
                if not jdata:
                    logger.log("No data returned to be parsed!!!")
                    return []

                for torrent in jdata:
                    if not torrent['ff']:
                        if mode != 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)
                        results.append((torrent['name'], torrent['magnet'], torrent['size']))
        return results


class BTDiggCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # set this 0 to suppress log line, since we aren't updating it anyways
        self.minTime = 0

    def _getRSSData(self):
        # no rss for btdigg, can't search with empty string
        # newest results are always > 1 day since added anyways
        return {'entries': {}}

provider = BTDIGGProvider()
