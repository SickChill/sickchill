# coding=utf-8
# Author: Jordon Smith <smith@jordon.me.uk>
#
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# First Party Imports
import sickbeard
from sickbeard import logger, tvcache
from sickchill.helper.common import try_int
from .NZBProvider import NZBProvider


class OmgwtfnzbsProvider(NZBProvider):
    def __init__(self):
        super().__init__('OMGWTFNZBs', extra_options=('username', 'api_key'))

        self.cache: tvcache.TVCache = OmgwtfnzbsCache(self)

        self.url = 'https://omgwtfnzbs.me/'
        self.urls = {
            'rss': 'https://rss.omgwtfnzbs.me/rss-download.php',
            'api': 'https://api.omgwtfnzbs.me/json/'
        }

        self.proper_strings = ['.PROPER.', '.REPACK.']

    def _check_auth(self) -> bool:

        if not self.config('username') or not self.config('api_key'):
            logger.warning('Invalid api key. Check your settings')
            return False

        return True

    def _check_auth_from_data(self, parsed_data, is_XML: bool = True) -> bool:

        if not parsed_data:
            return self._check_auth()

        if is_XML:
            # provider doesn't return xml on error
            return True

        if 'notice' in parsed_data:
            description_text = parsed_data.get('notice')
            if 'information is incorrect' in description_text:
                logger.warning('Invalid api key. Check your settings')
            elif '0 results matched your terms' not in description_text:
                logger.debug('Unknown error: {0}'.format(description_text))
            return False

        return True

    def _get_title_and_url(self, item) -> tuple:
        return item['release'], item['getnzb']

    def _get_size(self, item) -> int:
        return try_int(item['sizebytes'], -1)

    def search(self, search_strings, ep_obj=None) -> list:
        results = []
        if not self._check_auth():
            return results

        search_strings = {
            'user': self.config('username'),
            'api': self.config('api_key'),
            'eng': 1,
            'catid': '19,20,30',  # SD,HD,UHD
            'retention': self.config('retention'),
        }

        for mode in search_strings:
            items = []
            logger.debug('Search Mode: {0}'.format(mode))
            for search_string in search_strings[mode]:
                search_strings['search'] = search_string
                if mode != 'RSS':
                    logger.debug('Search string: {0}'.format(search_string))

                data = self.get_url(self.urls['api'], params=search_strings, returns='json')
                if not data:
                    logger.debug('No data returned from provider')
                    continue

                if not self._check_auth_from_data(data, is_XML=False):
                    continue

                for item in data:
                    if not self._get_title_and_url(item):
                        continue

                    logger.debug('Found result: {0}'.format(item.get('release')))
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

    def get_rss_data(self):
        search_params = {
            'user': self.provider.config('username'),
            'api': self.provider.config('api_key'),
            'eng': 1,
            'catid': '19,20,30',  # SD,HD,UHD
        }
        return self.get_rss_feed(self.provider.urls['rss'], params=search_params)


