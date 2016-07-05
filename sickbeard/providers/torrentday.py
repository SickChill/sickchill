# coding=utf-8
# Author: Mr_Orange <mr_orange@hotmail.it>
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

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


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
        self.url = 'https://classic.torrentday.com'
        self.urls = {
            'login': urljoin(self.url, '/t'),
            'search': urljoin(self.url, '/V3/API/API.php'),
            'download': urljoin(self.url, '/download.php/')
        }

        self.categories = {
            'Season': {'c14': 1},
            'Episode': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1},
            'RSS': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c14': 1}
        }

        self.enable_cookies = True

        # Cache
        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll IPTorrents every 10 minutes max

    def login(self):
        if dict_from_cookiejar(self.session.cookies).get('uid') and dict_from_cookiejar(self.session.cookies).get('pass'):
            return True

        if self.cookies:
            if 'uid' in self.cookies and 'pass' in self.cookies:
                self.add_cookies_from_ui()

            login_params = {
                'username': self.username,
                'password': self.password,
                'submit.x': 0,
                'submit.y': 0,
            }

            response = self.get_url(self.urls['login'], post_data=login_params, returns='response')
            if response.status_code not in [200]:
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

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        if not self.login():
            return results

        for mode in search_params:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log('Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)

                post_data = {'/browse.php?': None, 'cata': 'yes', 'jxt': 8, 'jxw': 'b', 'search': search_string}
                post_data.update(self.categories[mode])

                if self.freeleech:
                    post_data.update({'free': 'on'})

                parsedJSON = self.get_url(self.urls['search'], post_data=post_data, returns='json')
                if not parsedJSON:
                    logger.log('No data returned from provider', logger.DEBUG)
                    self.session.cookies.clear()
                    continue

                try:
                    torrents = parsedJSON.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
                except Exception:
                    logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                    continue

                for torrent in torrents:

                    title = re.sub(r'\[.*\=.*\].*\[/.*\]', '', torrent['name']) if torrent['name'] else None
                    download_url = urljoin(self.urls['download'], '{0}/{1}'.format(torrent['id'], torrent['fname'])) if torrent['id'] and torrent['fname'] else None
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(torrent['seed'])
                    leechers = try_int(torrent['leech'])

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log('Discarding torrent because it doesn\'t meet the minimum seeders or leechers: {0} (S:{1} L:{2})'.format(title, seeders, leechers), logger.DEBUG)
                        continue

                    torrent_size = torrent['size']
                    size = convert_size(torrent_size) or -1

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}

                    if mode != 'RSS':
                        logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                   (title, seeders, leechers), logger.DEBUG)

                    items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = TorrentDayProvider()
