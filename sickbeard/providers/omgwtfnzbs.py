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
from sickrage.helper.common import try_int
from sickrage.providers.nzb.NZBProvider import NZBProvider


class OmgwtfnzbsProvider(NZBProvider):
    def __init__(self):
        NZBProvider.__init__(self, "omgwtfnzbs")

        self.username = None
        self.api_key = None
        self.cache = OmgwtfnzbsCache(self)

        self.url = 'https://omgwtfnzbs.org/'
        self.urls = {
            'rss': 'https://rss.omgwtfnzbs.org/rss-download.php',
            'api': 'https://api.omgwtfnzbs.org/json/'
        }

    def _check_auth(self):

        if not self.username or not self.api_key:
            logger.log(u"Invalid api key. Check your settings", logger.WARNING)
            return False

        return True

    def _checkAuthFromData(self, parsed_data, is_XML=True):

        if parsed_data is None:
            return self._check_auth()

        if is_XML:
            # provider doesn't return xml on error
            return True
        else:
            if 'notice' in parsed_data:
                description_text = parsed_data.get('notice')

                if 'information is incorrect' in parsed_data.get('notice'):
                    logger.log(u"Invalid api key. Check your settings", logger.WARNING)

                elif '0 results matched your terms' in parsed_data.get('notice'):
                    return True

                else:
                    logger.log(u"Unknown error: %s" % description_text, logger.DEBUG)
                    return False

            return True

    def _get_title_and_url(self, item):
        return item['release'], item['getnzb']

    def _get_size(self, item):
        return try_int(item['sizebytes'], -1)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self._check_auth():
            return results

        search_params = {
            'user': self.username,
            'api': self.api_key,
            'eng': 1,
            'catid': '19,20',  # SD,HD
            'retention': sickbeard.USENET_RETENTION,
        }
        if age or not search_params['retention']:
            search_params['retention'] = age

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                search_params['search'] = search_string

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                logger.log(u"Search URL: %s" % self.urls['api'] + '?' + urllib.urlencode(search_params), logger.DEBUG)

                data = self.get_url(self.urls['api'], params=search_params, json=True)
                if not data:
                    continue

                if self._checkAuthFromData(data, is_XML=False):
                    continue

                for item in data:
                    if 'release' in item and 'getnzb' in item:
                        logger.log(u"Found result: %s " % item.get('title'), logger.DEBUG)
                        items.append(item)

            results += items

        return results

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
        search_params = {
            'user': provider.username,
            'api': provider.api_key,
            'eng': 1,
            'catid': '19,20'  # SD,HD
        }

        rss_url = self.provider.urls['rss'] + '?' + urllib.urlencode(search_params)

        logger.log(u"Cache update URL: %s" % rss_url, logger.DEBUG)

        return self.getRSSFeed(rss_url)

provider = OmgwtfnzbsProvider()
