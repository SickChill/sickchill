# coding=utf-8
#
# URL: https://sick-rage.github.io
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

from __future__ import print_function, unicode_literals

import re

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.helper.exceptions import AuthException
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class TVChaosUKProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, 'TvChaosUK')

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None
        self.freeleech = None

        self.url = 'https://www.tvchaosuk.com/'
        self.urls = {
            'login': self.url + 'takelogin.php',
            'index': self.url + 'index.php',
            'search': self.url + 'browse.php'
        }

        self.cache = tvcache.TVCache(self)

    def _check_auth(self):
        if self.username and self.password:
            return True

        raise AuthException('Your authentication credentials for ' + self.name + ' are missing, check your config.')

    def login(self):
        if len(self.session.cookies) >= 4:
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'logout': 'no',
            'submit': 'LOGIN',
            'returnto': '/browse.php'
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log('Unable to connect to provider', logger.WARNING)
            return False

        if re.search('Error: Username or password incorrect!', response):
            logger.log('Invalid username or password. Check your settings', logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            'do': 'search',
            'search_type': 't_name',
            'category': 0,
            'include_dead_torrents': 'no',
            'submit': 'search'
        }

        # Units
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode == 'Season':
                    search_string = re.sub(r'(.*)S0?', r'\1Series ', search_string)

                if mode != 'RSS':
                    logger.log('Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)

                search_params['keywords'] = search_string
                data = self.get_url(self.urls['search'], post_data=search_params, returns='text')
                if not data:
                    logger.log('No data returned from provider', logger.DEBUG)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find(id='sortabletable')
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    labels = [label.img['title'] if label.img else label.get_text(strip=True) for label in torrent_rows[0]('td')]
                    for torrent in torrent_rows[1:]:
                        try:
                            if self.freeleech and not torrent.find('img', alt=re.compile('Free Torrent')):
                                continue

                            title = torrent.find(class_='tooltip-content').div.get_text(strip=True)
                            download_url = torrent.find(title='Click to Download this Torrent!').parent['href']
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(torrent.find(title='Seeders').get_text(strip=True))
                            leechers = try_int(torrent.find(title='Leechers').get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log('Discarding torrent because it doesn\'t meet the'
                                               ' minimum seeders or leechers: {0} (S:{1} L:{2})'.format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            # Chop off tracker/channel prefix or we cant parse the result!
                            if mode != 'RSS' and search_params['keywords']:
                                show_name_first_word = re.search(r'^[^ .]+', search_params['keywords']).group()
                                if not title.startswith(show_name_first_word):
                                    title = re.sub(r'.*(' + show_name_first_word + '.*)', r'\1', title)

                            # Change title from Series to Season, or we can't parse
                            if mode == 'Season':
                                title = re.sub(r'(.*)(?i)Series', r'\1Season', title)

                            # Strip year from the end or we can't parse it!
                            title = re.sub(r'(.*)[\. ]?\(\d{4}\)', r'\1', title)
                            title = re.sub(r'\s+', r' ', title)

                            torrent_size = torrent('td')[labels.index('Size')].get_text(strip=True)
                            size = convert_size(torrent_size, units=units) or -1

                            if mode != 'RSS':
                                logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                           (title, seeders, leechers), logger.DEBUG)

                            item = {'title': title + '.hdtv.x264', 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = TVChaosUKProvider()
