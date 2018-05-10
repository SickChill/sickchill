# coding=utf-8
# Author: adaur <adaur.underground@gmail.com>
# Contributor: PHD <phd59fr@gmail.com>
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

import re

from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class YggTorrentProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, 'YggTorrent')

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # URLs
        self.url = 'https://yggtorrent.is/'
        self.urls = {
            'login': urljoin(self.url, 'user/login'),
            'search': urljoin(self.url, 'engine/search')
        }

        # Proper Strings
        self.proper_strings = ['PROPER']

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)

    def login(self):
        login_params = {
            'id': self.username,
            'pass': self.password,
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='response')

        # The login is now an AJAX call (401 : Bad credentials, 200 : Logged in, other : server failure)
        if response.status_code == 401:
            logger.log('Invalid username or password. Check your settings', logger.WARNING)
            return False
        elif response.status_code == 200:
            # It seems we are logged, let's verify that !
            response = self.get_url(self.url, returns='response')

            if response.status_code != 200:
                logger.log('Unable to connect to provider', logger.WARNING)
                return False
            if 'logout' not in response.text:
                logger.log('Invalid username or password. Check your settings', logger.WARNING)
                return False
        else:
            logger.log('Unable to connect to provider', logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log('Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)
                # search string needs to be normalized, single quotes are apparently not allowed on the site
                # ç should also be replaced, people tend to use c instead
                replace_chars = {
                                "'": '',
                                "ç": 'c'
                }

                for k, v in replace_chars.iteritems():
                    search_string = search_string.replace(k, v)

                logger.log('Sanitized string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)

                try:
                    search_params = {
                        'category': "2145",
                        'sub_category' : "2184",
                        'name': re.sub(r'[()]', '', search_string),
                        'do': 'search'
                    }
                    data = self.get_url(self.urls['search'], params=search_params, returns='text')
                    if not data:
                        continue

                    if 'logout' not in data:
                        logger.log('Refreshing cookies', logger.DEBUG)
                        self.login()

                    with BS4Parser(data, 'html5lib') as html:
                        torrent_table = html.find(class_='table')
                        torrent_rows = torrent_table('tr') if torrent_table else []

                        # Continue only if at least one Release is found
                        if len(torrent_rows) < 2:
                            logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                            continue

                        # Skip column headers
                        for result in torrent_rows[1:]:
                            cells = result('td')
                            if len(cells) < 9:
                                continue

                            title = cells[1].find('a').get_text(strip=True)
                            id = cells[2].find('a')['target']
                            download_url = urljoin(self.url, 'engine/download_torrent?id=' + id)

                            if not (title and download_url):
                                continue

                            seeders = try_int(cells[7].get_text(strip=True))
                            leechers = try_int(cells[8].get_text(strip=True))

                            torrent_size = cells[5].get_text()
                            size = convert_size(torrent_size) or -1

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log('Discarding torrent because it doesn\'t meet the minimum seeders or leechers: {0} (S:{1} L:{2})'.format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.log('Failed parsing provider {}.'.format(self.name), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = YggTorrentProvider()
