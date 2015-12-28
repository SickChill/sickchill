# coding=utf-8
# Author: Jordon Smith <smith@jordon.me.uk>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import urllib
from datetime import datetime

import sickbeard
from sickbeard import tvcache
from sickbeard import classes
from sickbeard import logger
from sickbeard import show_name_helpers
from sickrage.helper.common import try_int
from sickrage.providers.nzb.NZBProvider import NZBProvider


class OmgwtfnzbsProvider(NZBProvider):
    def __init__(self):
        NZBProvider.__init__(self, "omgwtfnzbs")

        self.username = None
        self.api_key = None
        self.cache = OmgwtfnzbsCache(self)

        self.urls = {'base_url': 'https://omgwtfnzbs.org/'}
        self.url = self.urls['base_url']

    def _check_auth(self):

        if not self.username or not self.api_key:
            logger.log(u"Invalid api key. Check your settings", logger.WARNING)

        return True

    def _checkAuthFromData(self, parsed_data, is_XML=True):

        if parsed_data is None:
            return self._check_auth()

        if is_XML:
            # provider doesn't return xml on error
            return True
        else:
            parsedJSON = parsed_data

            if 'notice' in parsedJSON:
                description_text = parsedJSON.get('notice')

                if 'information is incorrect' in parsedJSON.get('notice'):
                    logger.log(u"Invalid api key. Check your settings", logger.WARNING)

                elif '0 results matched your terms' in parsedJSON.get('notice'):
                    return True

                else:
                    logger.log(u"Unknown error: %s" % description_text, logger.DEBUG)
                    return False

            return True

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def _get_title_and_url(self, item):
        return item['release'], item['getnzb']

    def _get_size(self, item):
        return try_int(item['sizebytes'], -1)

    def search(self, search, age=0, ep_obj=None):

        self._check_auth()

        params = {'user': self.username,
                  'api': self.api_key,
                  'eng': 1,
                  'catid': '19,20',  # SD,HD
                  'retention': sickbeard.USENET_RETENTION,
                  'search': search}

        if age or not params['retention']:
            params['retention'] = age

        searchURL = 'https://api.omgwtfnzbs.org/json/?' + urllib.urlencode(params)
        logger.log(u"Search string: %s" % params, logger.DEBUG)
        logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)

        parsedJSON = self.get_url(searchURL, json=True)
        if not parsedJSON:
            return []

        if self._checkAuthFromData(parsedJSON, is_XML=False):
            results = []

            for item in parsedJSON:
                if 'release' in item and 'getnzb' in item:
                    logger.log(u"Found result: %s " % item.get('title'), logger.DEBUG)
                    results.append(item)

            return results

        return []

    def find_propers(self, search_date=None):
        search_terms = ['.PROPER.', '.REPACK.']
        results = []

        for term in search_terms:
            for item in self.search(term, age=4):
                if 'usenetage' in item:

                    title, url = self._get_title_and_url(item)
                    try:
                        result_date = datetime.fromtimestamp(int(item['usenetage']))
                    except Exception:
                        result_date = None

                    if result_date:
                        results.append(classes.Proper(title, url, result_date, self.show))

        return results


class OmgwtfnzbsCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)
        self.minTime = 20

    def _get_title_and_url(self, item):
        """
        Retrieves the title and URL data from the item XML node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns: A tuple containing two strings representing title and URL respectively
        """

        title = item.get('title')
        if title:
            title = u'' + title
            title = title.replace(' ', '.')

        url = item.get('link')
        if url:
            url = url.replace('&amp;', '&')

        return title, url

    def _getRSSData(self):
        params = {'user': provider.username,
                  'api': provider.api_key,
                  'eng': 1,
                  'catid': '19,20'}  # SD,HD

        rss_url = 'https://rss.omgwtfnzbs.org/rss-download.php?' + urllib.urlencode(params)

        logger.log(u"Cache update URL: %s" % rss_url, logger.DEBUG)

        return self.getRSSFeed(rss_url)

provider = OmgwtfnzbsProvider()
