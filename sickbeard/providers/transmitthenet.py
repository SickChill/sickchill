# coding=utf-8
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

import re
import traceback
from requests.utils import dict_from_cookiejar
from requests.compat import urljoin

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import try_int
from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TransmitTheNetProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "TransmitTheNet")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None
        self.freeleech = None

        # URLs
        self.url = 'https://transmithe.net/'
        self.urls = {
            'login': urljoin(self.url, '/login.php'),
            'search': urljoin(self.url, '/torrents.php'),
        }

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self)

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'keeplogged': 'on',
            'login': 'Login'
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username Incorrect', response) or re.search('Password Incorrect', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_params = {
                    'searchtext': search_string,
                    'filter_freeleech': (0, 1)[self.freeleech is True],
                    'order_by': ('seeders', 'time')[mode == 'RSS'],
                    "order_way": "desc"
                }

                if not search_string:
                    del search_params['searchtext']

                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        torrent_table = html.find('table', {'id': 'torrent_table'})
                        if not torrent_table:
                            logger.log(u"Data returned from {0} does not contain any torrents".format(self.name), logger.DEBUG)
                            continue

                        torrent_rows = torrent_table('tr', class_='torrent')

                        # Continue only if one Release is found
                        if not torrent_rows:
                            logger.log(u"Data returned from {0} does not contain any torrents".format(self.name), logger.DEBUG)
                            continue

                        for torrent_row in torrent_rows:
                            freeleech = torrent_row.find('img', alt="Freeleech") is not None
                            if self.freeleech and not freeleech:
                                continue

                            # Normal Download Link
                            download_item = torrent_row.find('a', {'title': 'Download Torrent'})

                            if not download_item:
                                # If the user has downloaded it
                                download_item = torrent_row.find('a', {'title': 'Previously Grabbed Torrent File'})
                            if not download_item:
                                # If the user is seeding
                                download_item = torrent_row.find('a', {'title': 'Currently Seeding Torrent'})
                            if not download_item:
                                # If the user is leeching
                                download_item = torrent_row.find('a', {'title': 'Currently Leeching Torrent'})
                            if not download_item:
                                # If there are none
                                continue

                            download_url = urljoin(self.url, download_item['href'])

                            temp_anchor = torrent_row.find('a', {"data-src": True})
                            title = temp_anchor['data-src'].rsplit('.', 1)[0]
                            if not all([title, download_url]):
                                continue

                            cells = torrent_row('td')
                            seeders = try_int(cells[8].text.strip())
                            leechers = try_int(cells[9].text.strip())

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the"
                                               u" minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            size = temp_anchor['data-filesize'] or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.log(u"Found result: {0} with {1} seeders and {2} leechers".format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: {0}".format(traceback.format_exc()), logger.ERROR)

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = TransmitTheNetProvider()
