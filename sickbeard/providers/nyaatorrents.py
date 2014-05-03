# Author: Mr_Orange
# URL: http://code.google.com/p/sickbeard/
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

import urllib
import re
import sickbeard
import generic

from sickbeard import show_name_helpers
from sickbeard import logger
from sickbeard.common import Quality
from sickbeard.name_parser.parser import NameParser, InvalidNameException
from sickbeard import tvcache

REMOTE_DBG = False

class NyaaProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "NyaaTorrents")

        self.supportsBacklog = True

        self.supportsAbsoluteNumbering = True

        self.cache = NyaaCache(self)

        self.url = 'http://www.nyaa.eu/'

    def isEnabled(self):
        return sickbeard.NYAA

    def imageName(self):
        return 'nyaatorrents.png'

    def getQuality(self, item, anime=False):
        self.debug()
        title = item.title
        quality = Quality.sceneQuality(title)
        return quality

    def getSearchResults(self, show, season, episodes, seasonSearch=False, manualSearch=False):
        results = generic.TorrentProvider.getSearchResults(self, show, season, episodes, seasonSearch, manualSearch)
        return results

    def _get_season_search_strings(self, ep_obj):
        names = []
        names.extend(show_name_helpers.makeSceneshowSearchStrings(self.show))
        return names

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return self._get_season_search_strings(ep_obj)

    def _doSearch(self, search_string, show=None, age=None):

        params = {"term": search_string.encode('utf-8'),
                  "sort": '2',  #Sort Descending By Seeders
        }

        searchURL = self.url + '?page=rss&' + urllib.urlencode(params)

        logger.log(u"Search string: " + searchURL, logger.DEBUG)


        data = self.getURL(searchURL)

        if not data:
            logger.log(u"Error trying to load NyaaTorrents RSS feed: " + searchURL, logger.ERROR)
            logger.log(u"RSS data: " + data, logger.DEBUG)
            return []

        items = data.entries

        results = []

        for curItem in items:

            (title, url) = self._get_title_and_url(curItem)

            if not title or not url:
                logger.log(
                    u"The XML returned from the NyaaTorrents RSS feed is incomplete, this result is unusable: " + data,
                    logger.ERROR)
                continue

            results.append(curItem)

        return results

    def _get_title_and_url(self, item):

        return generic.TorrentProvider._get_title_and_url(self, item)

    def _extract_name_from_filename(self, filename):
        name_regex = '(.*?)\.?(\[.*]|\d+\.TPB)\.torrent$'
        logger.log(u"Comparing " + name_regex + " against " + filename, logger.DEBUG)
        match = re.match(name_regex, filename, re.I)
        if match:
            return match.group(1)
        return None


class NyaaCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # only poll NyaaTorrents every 15 minutes max
        self.minTime = 15


    def _getRSSData(self):
        params = {
            "page": 'rss',  # Use RSS page
            "order": '1'  #Sort Descending By Date
        }

        url = self.provider.url + '?' + urllib.urlencode(params)

        logger.log(u"NyaaTorrents cache update URL: " + url, logger.DEBUG)

        return self.provider.getRSSFeed(url)

    def _parseItem(self, item):
        (title, url) = self.provider._get_title_and_url(item)

        if not title or not url:
            logger.log(u"The XML returned from the NyaaTorrents RSS feed is incomplete, this result is unusable",
                       logger.ERROR)
            return None

        logger.log(u"Adding item from RSS to cache: " + title, logger.DEBUG)

        return self._addCacheEntry(title, url)


provider = NyaaProvider()