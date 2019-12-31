# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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
import string

# Third Party Imports
from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class SpeedCDProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "Speedcd")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None
        self.freeleech = False

        # URLs
        self.url = 'https://speed.cd'
        self.urls = {
            'login': urljoin(self.url, 'takeElogin.php'),
            'search': urljoin(self.url, 'browse.php'),
        }

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK']

        # Cache
        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
        }

        # Yay lets add another request to the process since they are unreasonable.
        response = self.get_url(self.url, returns='text')
        with BS4Parser(response, 'html5lib') as html:
            form = html.find('form', id='loginform')
            if form:
                self.urls['login'] = urljoin(self.url, form['action'])

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Incorrect username or Password. Please try again.', response):
            logger.log("Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if not self.login():
            return results

        # http://speed.cd/browse.php?c49=1&c50=1&c52=1&c41=1&c55=1&c2=1&c30=1&freeleech=on&search=arrow&d=on
        # Search Params
        search_params = {
            'c30': 1,  # Anime
            'c41': 1,  # TV/Packs
            'c49': 1,  # TV/HD
            'c50': 1,  # TV/Sports
            'c52': 1,  # TV/B-Ray
            'c55': 1,  # TV/Kids
            'search': '',
        }

        # Units
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

        def process_column_header(td):
            result = ''
            img = td.find('img')
            if img:
                result = img.get('alt')
            if not result:
                result = td.get_text(strip=True)
            return result

        if self.freeleech:
            search_params['freeleech'] = 'on'

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_params['search'] = search_string.translate(None, string.punctuation)

                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('div', class_='boxContent')
                    torrent_table = torrent_table.find('table') if torrent_table else []
                    torrent_rows = torrent_table('tr') if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    labels = [process_column_header(label) for label in torrent_rows[0]('th')]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        try:
                            cells = result('td')

                            title = cells[labels.index('Title')].find('a').get_text()
                            download_url = urljoin(self.url, cells[labels.index('Download') - 1].a['href'])
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index('Seeders') - 1].get_text(strip=True))
                            leechers = try_int(cells[labels.index('Leechers') - 1].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            torrent_size = cells[labels.index('Size') - 1].get_text()
                            torrent_size = torrent_size[:-2] + ' ' + torrent_size[-2:]
                            size = convert_size(torrent_size, units=units) or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = SpeedCDProvider()
