# Author: Mr_Orange
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

import urllib
import re

import generic

from sickbeard import show_name_helpers
from sickbeard import logger
from sickbeard.common import Quality
from sickbeard import tvcache
from sickbeard import show_name_helpers


class NyaaProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "NyaaTorrents")

        self.supportsBacklog = True
        self.public = True
        self.supportsAbsoluteNumbering = True
        self.anime_only = True
        self.enabled = False
        self.ratio = None

        self.cache = NyaaCache(self)

        self.urls = {'base_url': 'http://www.nyaa.se/'}

        self.url = self.urls['base_url']

    def isEnabled(self):
        return self.enabled

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False, downCurQuality=False):
        return generic.TorrentProvider.findSearchResults(self, show, episodes, search_mode, manualSearch, downCurQuality)

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def _doSearch(self, search_string, search_mode='eponly', epcount=0, age=0, epObj=None):
        #FIXME
        if self.show and not self.show.is_anime:
            return []

        logger.log(u"Search string: %s " % search_string, logger.DEBUG)

        params = {
            "term": search_string.encode('utf-8'),
            "cats": '1_0',  # All anime
            "sort": '2',     # Sort Descending By Seeders
        }

        searchURL = self.url + '?page=rss&' + urllib.urlencode(params)
        logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG) 


        results = []
        for curItem in self.cache.getRSSFeed(searchURL, items=['entries'])['entries'] or []:
            title = curItem[0]
            download_url = curItem[1]
            #FIXME
            size = -1
            seeders = 1
            leechers = 0

            if not all([title, download_url]):
                continue

            #Filter unseeded torrent
            #if seeders < self.minseed or leechers < self.minleech:
            #    if mode != 'RSS':
            #        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
            #    continue

            item = title, download_url, size, seeders, leechers
            logger.log(u"Found result: %s " % title, logger.DEBUG)

            #FIX ME SORTING
            results.append(curItem)

        return results

    def _extract_name_from_filename(self, filename):
        name_regex = '(.*?)\.?(\[.*]|\d+\.TPB)\.torrent$'
        logger.log(u"Comparing %s against %s" % (name_regex, filename), logger.DEBUG)
        match = re.match(name_regex, filename, re.I)
        if match:
            return match.group(1)
        return None

    def seedRatio(self):
        return self.ratio


class NyaaCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # only poll NyaaTorrents every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        params = {
            "page": 'rss',   # Use RSS page
            "order": '1',    # Sort Descending By Date
            "cats": '1_37',  # Limit to English-translated Anime (for now)
        }

        url = self.provider.url + '?' + urllib.urlencode(params)

        logger.log(u"Cache update URL: %s" % url, logger.DEBUG)

        return self.getRSSFeed(url)

provider = NyaaProvider()
