# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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
from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class ILoveTorrentsProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):
    
        # Provider Init
        TorrentProvider.__init__(self, "ILoveTorrents")
        
        # URLs
        self.url = 'https://www.ilovetorrents.me/'
        self.urls = {
            'login': urljoin(self.url, "takelogin.php"),
            'detail': urljoin(self.url, "details.php?id=%s"),
            'search': urljoin(self.url, "browse.php"),
            'download': urljoin(self.url, "%s"),
        }


        # Credentials
        self.username = None
        self.password = None
        
        # Torrent Stats        
        self.minseed = None
        self.minleech = None
        
        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK", "REAL"]

        # Cache
        self.cache = tvcache.TVCache(self)


    def _check_auth(self):
        if not self.username or not self.password:
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'logout': 'false',
            'submit': 'Welcome to ILT'
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username or password incorrect', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        if not self.login():
            return results
        search_params = {
            "cat": 0
        }
        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_params['search'] = search_string

                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    continue

                try:
                    with BS4Parser(data, "html.parser") as html:
                        torrent_table = html.find('table', class_='koptekst')
                        torrent_rows = torrent_table('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
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
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue
                            #Use same failsafe as Bitsoup
                            if seeders >= 32768 or leechers >= 32768:
                                continue

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': None}
                            if mode != 'RSS':
                                logger.log(u"Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                            items.append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: {0}".format(traceback.format_exc()), logger.WARNING)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results


provider = ILoveTorrentsProvider()
