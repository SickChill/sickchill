# coding=utf-8
# Author: Mr_Orange <mr_orange@hotmail.it>
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

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import re

# Third Party Imports
import validators
from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

# First Party Imports
from sickbeard import logger, tvcache
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class TorrentDayProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, 'TorrentDay')

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None
        self.freeleech = False

        # URLs
        self.custom_url = None
        self.url = 'https://www.torrentday.com'
        self.urls = {
            'login': urljoin(self.url, '/t'),
            'search': urljoin(self.url, '/t.json'),
            'download': urljoin(self.url, '/download.php/')
        }

        self.categories = {
            'Season': {'14': 1},
            'Episode': {'2': 1, '26': 1, '7': 1, '24': 1, '34': 1},
            'RSS': {'2': 1, '26': 1, '7': 1, '24': 1, '34': 1, '14': 1}
        }

        self.enable_cookies = True

        # Cache
        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll IPTorrents every 10 minutes max

    def login(self):
        cookie_dict = dict_from_cookiejar(self.session.cookies)
        if cookie_dict.get('uid') and cookie_dict.get('pass'):
            return True

        if self.cookies:
            success, status = self.add_cookies_from_ui()
            if not success:
                logger.log(status, logger.INFO)
                return False

            login_params = {'username': self.username, 'password': self.password, 'submit.x': 0, 'submit.y': 0}
            login_url = self.urls['login']
            if self.custom_url:
                if not validators.url(self.custom_url):
                    logger.log("Invalid custom url: {0}".format(self.custom_url), logger.WARNING)
                    return False

                login_url = urljoin(self.custom_url, self.urls['login'].split(self.url)[1])

            response = self.get_url(login_url, post_data=login_params, returns='response')
            if not response or response.status_code != 200:
                logger.log('Unable to connect to provider', logger.WARNING)
                return False

            if re.search('You tried too often', response.text):
                logger.log('Too many login access attempts', logger.WARNING)
                return False

            if dict_from_cookiejar(self.session.cookies).get('uid') in response.text:
                return True
            else:
                logger.log('Failed to login, check your cookies', logger.WARNING)
                return False
        else:
            logger.log('You need to set your cookies to use torrentday')
            return False

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []

        search_url = self.urls['search']
        download_url = self.urls['download']
        if self.custom_url:
            if not validators.url(self.custom_url):
                logger.log("Invalid custom url: {0}".format(self.custom_url), logger.WARNING)
                return results

            search_url = urljoin(self.custom_url, search_url.split(self.url)[1])
            download_url = urljoin(self.custom_url, download_url.split(self.url)[1])

        if not self.login():
            return results

        for mode in search_params:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log('Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)

                get_params = {}
                get_params.update(self.categories[mode])
                get_params["q"] = search_string.decode('utf-8', 'ignore')

                try:
                    torrents = self.get_url(search_url, params=get_params, returns='json')
                    # Handle empty string response or None #4304
                    assert torrents
                    # Make sure it is iterable #4304
                    iter(torrents)
                except (TypeError, AssertionError):
                    logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                    continue

                for torrent in torrents:

                    title = re.sub(r'\[.*\=.*\].*\[/.*\]', '', torrent['name']) if torrent['name'] else None
                    torrent_url = urljoin(download_url, '{0}/{1}.torrent'.format(torrent['t'], torrent['name'])) if torrent['t'] and torrent['name'] else \
                        None
                    if not all([title, torrent_url]):
                        continue

                    seeders = try_int(torrent['seeders'])
                    leechers = try_int(torrent['leechers'])

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log('Discarding torrent because it doesn\'t meet the minimum seeders or leechers: {0} (S:{1} L:{2})'.format(title, seeders, leechers), logger.DEBUG)
                        continue

                    torrent_size = torrent['size']
                    size = convert_size(torrent_size) or -1

                    item = {'title': title, 'link': torrent_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}

                    if mode != 'RSS':
                        logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                   (title, seeders, leechers), logger.DEBUG)

                    items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = TorrentDayProvider()
