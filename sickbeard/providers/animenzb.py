# coding=utf-8

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
from sickrage.providers.nzb.NZBProvider import NZBProvider


class animenzb(NZBProvider):

    def __init__(self):

        NZBProvider.__init__(self, "AnimeNZB")

        self.supports_backlog = False
        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True

        self.urls = {'base_url': 'http://animenzb.com/'}
        self.url = self.urls['base_url']

        self.cache = animenzbCache(self)

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def search(self, search_string, age=0, ep_obj=None):

        logger.log(u"Search string: %s " % search_string, logger.DEBUG)

        if self.show and not self.show.is_anime:
            return []

        params = {
            "cat": "anime",
            "q": search_string.encode('utf-8'),
            "max": "100"
        }

        searchURL = self.url + "rss?" + urllib.urlencode(params)
        logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
        results = []
        if 'entries' in self.cache.getRSSFeed(searchURL): 
            for curItem in self.cache.getRSSFeed(searchURL)['entries']:
                (title, url) = self._get_title_and_url(curItem)
    
                if title and url:
                    results.append(curItem)
                    logger.log(u"Found result: %s " % title, logger.DEBUG)
    
            # For each search mode sort all the items by seeders if available if available
            results.sort(key=lambda tup: tup[0], reverse=True)

        return results

    def find_propers(self, search_date=None):

        results = []

        for item in self.search("v2|v3|v4|v5"):

            (title, url) = self._get_title_and_url(item)

            if 'published_parsed' in item and item['published_parsed']:
                result_date = item.published_parsed
                if result_date:
                    result_date = datetime.datetime(*result_date[0:6])
            else:
                continue

            if not search_date or result_date > search_date:
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
