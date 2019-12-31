# coding=utf-8
# Author: Idan Gutman
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

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import re
import traceback

# Third Party Imports
from requests.utils import dict_from_cookiejar

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class GimmePeersProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "GimmePeers")

        self.urls = {
            'base_url': 'https://www.gimmepeers.com',
            'login': 'https://www.gimmepeers.com/takelogin.php',
            'detail': 'https://www.gimmepeers.com/details.php?id=%s',
            'search': 'https://www.gimmepeers.com/browse.php',
            'download': 'https://gimmepeers.com/%s',
        }

        self.url = self.urls['base_url']

        self.username = None
        self.password = None
        self.minseed = None
        self.minleech = None

        self.cache = tvcache.TVCache(self)

        self.search_params = {
            #c20=1&c21=1&c25=1&c24=1&c23=1&c22=1&c1=1
            "c20": 1, "c21": 1, "c25": 1, "c24": 1, "c23": 1, "c22": 1, "c1": 1
        }

    def _check_auth(self):
        if not self.username or not self.password:
            logger.log("Invalid username or password. Check your settings", logger.WARNING)

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'ssl': 'yes'
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username or password incorrect!', response):
            logger.log("Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                self.search_params['search'] = search_string

                data = self.get_url(self.urls['search'], params=self.search_params, returns='text')
                if not data:
                    continue

                # Checks if cookie has timed-out causing search to redirect to login page.
                # If text matches on loginpage we login and generate a new cookie and load the search data again.
                if re.search('Still need help logging in?', data):
                    logger.log("Login has timed out. Need to generate new cookie for GimmePeers and search again.", logger.DEBUG)
                    self.session.cookies.clear()
                    self.login()

                    data = self.get_url(self.urls['search'], params=self.search_params, returns='text')
                    if not data:
                        continue

                try:
                    with BS4Parser(data, "html.parser") as html:
                        torrent_table = html.find('table', class_='browsetable')
                        torrent_rows = torrent_table('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in torrent_rows[1:]:
                            cells = result('td')

                            link = cells[1].find('a')
                            download_url = self.urls['download'] % cells[2].find('a')['href']

                            try:
                                title = link.getText()
                                seeders = int(cells[10].getText().replace(',', ''))
                                leechers = int(cells[11].getText().replace(',', ''))
                                torrent_size = cells[8].getText()
                                size = convert_size(torrent_size) or -1
                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                                # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            if seeders >= 32768 or leechers >= 32768:
                                continue

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                            items.append(item)

                except Exception:
                    logger.log("Failed parsing provider. Traceback: {0}".format(traceback.format_exc()), logger.WARNING)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results


provider = GimmePeersProvider()
