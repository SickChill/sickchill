# Author: Nic Wolfe <nic@wolfeden.ca>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import datetime


from sickbeard import classes
from sickbeard import show_name_helpers

from sickbeard import logger

from sickbeard import tvcache
from sickbeard.providers import generic


class animenzb(generic.NZBProvider):

    def __init__(self):

        generic.NZBProvider.__init__(self, "AnimeNZB")

        self.supportsBacklog = False
        self.public = True
        self.supportsAbsoluteNumbering = True
        self.anime_only = True

        self.cache = animenzbCache(self)

        self.urls = {'base_url': 'http://animenzb.com//'}

        self.url = self.urls['base_url']

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def _doSearch(self, search_string, search_mode='eponly', epcount=0, age=0, epObj=None):

        logger.log(u"Search string: %s " % search_string, logger.DEBUG)

        if self.show and not self.show.is_anime:
            return []

        params = {
            "cat": "anime",
            "q": search_string.encode('utf-8'),
            "max": "100"
        }

        searchURL = self.url + "rss?" + urllib.urlencode(params)
        logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
        results = []
        for curItem in self.cache.getRSSFeed(searchURL)['entries'] or []:
            (title, url) = self._get_title_and_url(curItem)

            if title and url:
                results.append(curItem)
                logger.log(u"Found result: %s " % title, logger.DEBUG)

        # For each search mode sort all the items by seeders if available if available
        results.sort(key=lambda tup: tup[0], reverse=True)

        return results

    def findPropers(self, date=None):

        results = []

        for item in self._doSearch("v2|v3|v4|v5"):

            (title, url) = self._get_title_and_url(item)

            if item.has_key('published_parsed') and item['published_parsed']:
                result_date = item.published_parsed
                if result_date:
                    result_date = datetime.datetime(*result_date[0:6])
            else:
                continue

            if not date or result_date > date:
                search_result = classes.Proper(title, url, result_date, self.show)
                results.append(search_result)

        return results


class animenzbCache(tvcache.TVCache):

    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll animenzb every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):

        params = {
            "cat": "anime".encode('utf-8'),
            "max": "100".encode('utf-8')
        }

        rss_url = self.provider.url + 'rss?' + urllib.urlencode(params)

        return self.getRSSFeed(rss_url)

provider = animenzb()
