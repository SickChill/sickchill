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
from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size, try_int
from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TVChaosUKProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, 'TvChaosUK')

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = None

        # URLs
        self.url = 'https://tvchaosuk.com/'
        self.urls = {
            'login': self.url + 'takelogin.php',
            'index': self.url + 'index.php',
            'search': self.url + 'browse.php'
        }

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self)

    def _check_auth(self):
        if self.username and self.password:
            return True

        raise AuthException('Your authentication credentials for ' + self.name + ' are missing, check your config.')

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'logout': 'no',
            'submit': 'LOGIN',
            'returnto': '/browse.php'
        }

        # Must be done twice, or it isnt really logged in
        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Error: Username or password incorrect!', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
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
            logger.log(u"Search Mode: {}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode == 'Season':
                    search_string = re.sub(ur'(.*)Season', ur'\1Series', search_string)

                if mode != 'RSS':
                    logger.log(u"Search string: {}".format(search_string), logger.DEBUG)

                search_params['keywords'] = search_string.strip()
                data = self.get_url(self.urls['search'], post_data=search_params)
                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find(id='sortabletable')
                    if not torrent_table:
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    torrent_rows = torrent_table.find_all('tr')
                    if not torrent_rows:
                        continue

                    labels = [label.img['title'] if label.img else label.get_text(strip=True) for label in torrent_rows[0].find_all('td')]
                    for torrent in torrent_rows[1:]:
                        try:
                            if self.freeleech and not torrent.find('img', alt=re.compile('Free Torrent')):
                                continue

                            title = torrent.find(class_='tooltip-content').div.get_text(strip=True).replace("mp4", "x264")
                            download_url = torrent.find(title="Click to Download this Torrent!").parent['href']
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(torrent.find(title='Seeders').get_text(strip=True))
                            leechers = try_int(torrent.find(title='Leechers').get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the"
                                               u" minimum seeders or leechers: {} (S:{} L:{})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            # Chop off tracker/channel prefix or we cant parse the result!
                            if mode != 'RSS' and search_params['keywords']:
                                show_name_first_word = re.search(ur'^[^ .]+', search_params['keywords']).group()
                                if not title.startswith(show_name_first_word):
                                    title = re.sub(ur'.*(' + show_name_first_word + '.*)', ur'\1', title)

                            # Change title from Series to Season, or we can't parse
                            if mode == 'Season':
                                title = re.sub(ur'(.*)(?i)Series', ur'\1Season', title)

                            # Strip year from the end or we can't parse it!
                            title = re.sub(ur'(.*)[\. ]?\(\d{4}\)', ur'\1', title)
                            title = re.sub(ur'\s+', ur' ', title)

                            torrent_size = torrent.find_all('td')[labels.index('Size')].get_text(strip=True)
                            size = convert_size(torrent_size, units=units) or -1

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: {} with {} seeders and {} leechers".format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)
            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = TVChaosUKProvider()
