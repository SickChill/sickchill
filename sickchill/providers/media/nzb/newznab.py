# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# Rewrite: Dustyn Gibson (miigotu) <miigotu@gmail.com>
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
# Stdlib Imports
import os
import re
import time

# Third Party Imports
import validators
from requests.compat import urljoin

# First Party Imports
import sickbeard
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickbeard.common import cpu_presets
from sickchill.helper.common import convert_size, try_int

# Local Folder Imports
from .NZBProvider import NZBProvider


class NewznabProvider(NZBProvider):
    """
    Generic provider for built in and custom providers who expose a newznab
    compatible api.
    Tested with: newznab, nzedb, spotweb, torznab
    """
    def __init__(self, name: str):

        super().__init__(name, extra_options=('url', 'key', 'search_mode', 'search_fallback', 'daily', 'backlog', 'categories', 'retention'))

        self._caps = False
        self.use_tv_search = None
        self.cap_tv_search = None
        # self.cap_search = None
        # self.cap_movie_search = None
        # self.cap_audio_search = None

        self.min_cache_time = 30
        self.__torznab = False

    def image_name(self):
        """
        Checks if we have an image for this provider already.
        Returns found image or the default newznab image
        """
        if os.path.isfile(os.path.join(sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME, 'images', 'providers', self.get_id() + '.png')):
            return self.get_id() + '.png'
        return 'newznab.png'

    @property
    def caps(self):
        return self._caps

    @caps.setter
    def caps(self, data):
        # Override nzb.su - tvsearch without tvdbid, with q param
        if 'nzb.su' in self.config('url'):
            self.use_tv_search = True
            self.cap_tv_search = ''
            self._caps = True
            return

        elm = data.find('tv-search')
        self.use_tv_search = elm and elm.get('available') == 'yes'
        if self.use_tv_search:
            self.cap_tv_search = elm.get('supportedparams', 'tvdbid,season,ep')

        self._caps = any([self.cap_tv_search])

    @property
    def needs_auth(self):
        return self.config('key') and self.config('key') != '0'

    def get_newznab_categories(self, just_caps=False):
        """
        Uses the newznab provider url and apikey to get the capabilities.
        Makes use of the default newznab caps param. e.a. http://yournewznab/api?t=caps&apikey=skdfiw7823sdkdsfjsfk
        Returns a tuple with (succes or not, array with dicts [{'id': '5070', 'name': 'Anime'},
        {'id': '5080', 'name': 'Documentary'}, {'id': '5020', 'name': 'Foreign'}...etc}], error message)
        """
        return_categories = []

        if not self._check_auth():
            return False, return_categories, 'Provider requires auth and your key is not set'

        url_params = {'t': 'caps'}
        if self.needs_auth and self.config('key'):
            url_params['apikey'] = self.config('key')

        data = self.get_url(urljoin(self.config('url'), 'api'), params=url_params, returns='text')
        if not data:
            error_string = 'Error getting caps xml for [{0}]'.format(self.name)
            logger.warning(error_string)
            return False, return_categories, error_string

        with BS4Parser(data, 'html5lib') as html:
            try:
                self.__torznab = html.find('server').get('title') == 'Jackett'
            except AttributeError:
                self.__torznab = False

            if not html.find('categories'):
                error_string = 'Error parsing caps xml for [{0}]'.format(self.name)
                logger.debug(error_string)
                return False, return_categories, error_string

            self.caps = html.find('searching')
            if just_caps:
                return True, return_categories, 'Just checking caps!'

            for category in html('category'):
                if 'TV' in category.get('name', '') and category.get('id', ''):
                    return_categories.append({'id': category['id'], 'name': category['name']})
                    for subcat in category('subcat'):
                        if subcat.get('name', '') and subcat.get('id', ''):
                            return_categories.append({'id': subcat['id'], 'name': subcat['name']})

            return True, return_categories, ''

    def _check_auth(self):
        """
        Checks that user has set their api key if it is needed
        Returns: True/False
        """
        if self.needs_auth and not self.config('key'):
            logger.warning('Invalid api key. Check your settings')
            return False

        return True

    def _check_auth_from_data(self, data):
        """
        Checks that the returned data is valid
        Returns: _check_auth if valid otherwise False if there is an error
        """
        if data('categories') + data('item'):
            return self._check_auth()

        try:
            err_desc = data.error.attrs['description']
            if not err_desc:
                raise AttributeError
        except (AttributeError, TypeError):
            return self._check_auth()

        logger.info(err_desc)

        return False

    def search(self, search_strings, ep_obj=None) -> list:
        """
        Searches indexer using the params in search_strings, either for latest releases, or a string/id search
        Returns: list of results in dict form
        """
        results = []
        if not self._check_auth():
            return results

        if 'gingadaddy' not in self.config('url'):  # gingadaddy has no caps.
            if not self.caps:
                self.get_newznab_categories(just_caps=True)

            if not self.caps:
                return results

        for mode in search_strings:
            search_strings = {
                't': ('search', 'tvsearch')[bool(self.use_tv_search)],
                'limit': 100,
                'offset': 0,
                'cat': self.config('categories').strip(', ') or '5030,5040',
                'maxage': self.config('retention')
            }

            if self.needs_auth and self.config('key'):
                search_strings['apikey'] = self.config('key')

            if mode != 'RSS':
                if self.use_tv_search:
                    if 'tvdbid' in str(self.cap_tv_search):
                        search_strings['tvdbid'] = ep_obj.show.indexerid

                    if ep_obj.show.air_by_date or ep_obj.show.sports:
                        date_str = str(ep_obj.airdate)
                        search_strings['season'] = date_str.partition('-')[0]
                        search_strings['ep'] = date_str.partition('-')[2].replace('-', '/')
                    elif ep_obj.show.is_anime:
                        search_strings['ep'] = ep_obj.absolute_number
                    else:
                        search_strings['season'] = ep_obj.scene_season
                        search_strings['ep'] = ep_obj.scene_episode

                if mode == 'Season':
                    search_strings.pop('ep', '')

            if self.__torznab:
                search_strings.pop('ep', '')
                search_strings.pop('season', '')

            items = []
            logger.debug('Search Mode: {0}'.format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.debug('Search string: {0}'.format(search_string))

                    if 'tvdbid' not in search_strings:
                        search_strings['q'] = search_string

                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
                data = self.get_url(urljoin(self.config('url'), 'api'), params=search_strings, returns='text')
                if not data:
                    break

                with BS4Parser(data, 'html5lib') as html:
                    if not self._check_auth_from_data(html):
                        break

                    # try:
                    #     self.__torznab = 'xmlns:torznab' in html.rss.attrs
                    # except AttributeError:
                    #     self.__torznab = False

                    for item in html('item'):
                        try:
                            title = item.title.get_text(strip=True)
                            download_url = None
                            if item.link:
                                if validators.url(item.link.get_text(strip=True)):
                                    download_url = item.link.get_text(strip=True)
                                elif validators.url(item.link.next.strip()):
                                    download_url = item.link.next.strip()

                            if (not download_url, item.enclosure and
                                    validators.url(item.enclosure.get('url', '').strip())):
                                download_url = item.enclosure.get('url', '').strip()

                            if not (title and download_url):
                                continue

                            seeders = leechers = None
                            if 'gingadaddy' in self.config('url'):
                                size_regex = re.search(r'\d*.?\d* [KMGT]B', str(item.description))
                                item_size = size_regex.group() if size_regex else -1
                            else:
                                item_size = item.size.get_text(strip=True) if item.size else -1
                                for attr in item.find_all(['newznab:attr','torznab:attr']):
                                    item_size = attr['value'] if attr['name'] == 'size' else item_size
                                    seeders = try_int(attr['value']) if attr['name'] == 'seeders' else seeders
                                    leechers = try_int(attr['value']) if attr['name'] == 'peers' else leechers

                            if not item_size or (self.__torznab and (seeders is None or leechers is None)):
                                continue

                            size = convert_size(item_size) or -1

                            result = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                            items.append(result)
                        except Exception:
                            continue

                # Since we aren't using the search string,
                # break out of the search string loop
                if 'tvdbid' in search_strings:
                    break

            if self.__torznab:
                results.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results

    def _get_size(self, item):
        """
        Gets size info from a result item
        Returns int size or -1
        """
        return try_int(item.get('size', -1), -1)
