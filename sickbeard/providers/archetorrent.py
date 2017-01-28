# coding=utf-8
# Author: ellmout <ellmout@ellmout.net>
# Inspired from : adaur <adaur.underground@gmail.com> (ABNormal)
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


class ArcheTorrentProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, 'ArcheTorrent')
        self.enable_cookies = True

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Freelech
        self.freeleech = False

        # URLs
        self.url = 'https://www.archetorrent.com/'
        self.urls = {
            'login': urljoin(self.url, 'account-login.php'),
            'search': urljoin(self.url, 'torrents-search.php'),
            'download': urljoin(self.url, 'download.php'),
        }

        # Proper Strings
        self.proper_strings = ['PROPER']

        # Cache
        self.cache = tvcache.TVCache(self, min_time=15)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'returnto': '/index.php'
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if response:
            logger.log('Unable to connect to provider', logger.WARNING)
            return False

        search = self.get_url(self.urls['search'])

        if not re.search('torrents.php', search):
            logger.log('Invalid username or password. Check your settings', logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if not self.login():
            return results

        freeleech = '2' if self.freeleech else '0'

        # Search Params
        # c59=1&c73=1&c5=1&c41=1&c60=1&c66=1&c65=1&c67=1&c62=1&c64=1&c61=1&search=Good+Behavior+S01E01&cat=0&incldead=0&freeleech=0&lang=0
        search_params = {
            'c5': '1', # Category: Series - DVDRip 
            'c41': '1', # Category: Series - HD
            'c60': '1', # Category: Series - Pack TV
            'c62': '1', # Category: Series - BDRip
            'c64': '1', # Category: Series - VOSTFR
            'c65': '1', # Category: Series - TV 720p
            'c66': '1', # Category: Series - TV 1080p
            'c67': '1', # Category: Series - Pack TV HD
            'c73': '1', # Category: Anime
            'incldead': '0',  # Include dead torrent - 0: off 1: yes 2: only dead
            'freeleech': freeleech, # Only freeleech torrent - 0: off 1: no freeleech 2: Only freeleech
            'lang': '0' # Langugage - 0: off 1: English 2: French ....
        }

        # Units
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:
                logger.log('Search String: %s for mode %s' % (search_strings[mode], mode), logger.DEBUG)
                if mode != 'RSS':
                    logger.log('Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)
                
                search_params['search'] = re.sub(r'[()]', '', search_string)
                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find(class_='ttable_headinner')
                    torrent_rows = torrent_table('tr') if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                        continue

                    # Catégorie, Release, Date, DL, Size, C, S, L
                    labels = [label.get_text(strip=True) for label in torrent_rows[0]('th')]
                    
                    # Skip column headers
                    for result in torrent_rows[1:]:
                        cells = result('td')
                        if len(cells) < len(labels):
                            continue

                        try:
                            id = re.search('id=([0-9]+)', cells[labels.index('Nom')].find('a')['href']).group(1)
                            title = cells[labels.index('Nom')].get_text(strip=True)
                            download_url = urljoin(self.urls['download'], '?id=%s&name=%s' % (id, title))
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index('S')].get_text(strip=True))
                            leechers = try_int(cells[labels.index('L')].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log('Discarding torrent because it doesn\'t meet the minimum seeders or leechers: {0} (S:{1} L:{2})'.format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            size_index = labels.index('Size') if 'Size' in labels else labels.index('Taille')
                            torrent_size = cells[size_index].get_text()
                            size = convert_size(torrent_size, units=units) or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = ArcheTorrentProvider()
