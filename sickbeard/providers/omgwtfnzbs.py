# coding=utf-8
# Author: Jordon Smith <smith@jordon.me.uk>
#
# URL: https://sickrage.github.io
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

from __future__ import unicode_literals

import sickbeard
from sickbeard import logger, tvcache

from sickrage.helper.common import try_int
from sickrage.providers.nzb.NZBProvider import NZBProvider


class OmgwtfnzbsProvider(NZBProvider):
    def __init__(self):
        NZBProvider.__init__(self, 'OMGWTFNZBs')

        self.username = None
        self.api_key = None

        self.cache = OmgwtfnzbsCache(self)

        self.url = 'https://omgwtfnzbs.me/'
        self.urls = {
            'rss': 'https://rss.omgwtfnzbs.me/rss-download.php',
            'api': 'https://api.omgwtfnzbs.me/json/'
        }

        self.proper_strings = ['.PROPER.', '.REPACK.']

    def _check_auth(self):

        if not self.username or not self.api_key:
            logger.log('Invalid api key. Check your settings', logger.WARNING)
            return False

        return True

    def _check_auth_from_data(self, parsed_data, is_XML=True):

        if not parsed_data:
            return self._check_auth()

        if is_XML:
            # provider doesn't return xml on error
            return True

        if 'notice' in parsed_data:
            description_text = parsed_data.get('notice')
            if 'information is incorrect' in description_text:
                logger.log('Invalid api key. Check your settings', logger.WARNING)
            elif '0 results matched your terms' not in description_text:
                logger.log('Unknown error: {0}'.format(description_text), logger.DEBUG)
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

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                search_params['search'] = search_string
                if mode != 'RSS':
                    logger.log('Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)

                data = self.get_url(self.urls['api'], params=search_params, returns='json')
                if not data:
                    logger.log('No data returned from provider', logger.DEBUG)
                    continue

                if not self._check_auth_from_data(data, is_XML=False):
                    continue

                for item in data:
                    if not self._get_title_and_url(item):
                        continue

                    logger.log('Found result: {0}'.format(item.get('release')), logger.DEBUG)
                    items.append(item)

            results += items

        return results


class OmgwtfnzbsCache(tvcache.TVCache):
    def _get_title_and_url(self, item):
        title = item.get('title')
        if title:
            title = title.replace(' ', '.')

        url = item.get('link')
        if url:
            url = url.replace('&amp;', '&')

        return title, url

    def _get_rss_data(self):
        search_params = {
            'user': provider.username,
            'api': provider.api_key,
            'eng': 1,
            'catid': '19,20'  # SD,HD
        }
        return self.get_rss_feed(self.provider.urls['rss'], params=search_params)

provider = OmgwtfnzbsProvider()
