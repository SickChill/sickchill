# coding=utf-8
# Author: adaur <adaur.underground@gmail.com>
# Rewrite: Dustyn Gibson (miigotu) <miigotu@gmail.com>
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
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class XthorProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "Xthor")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None
        self.freeleech = None

        # URLs
        self.url = 'https://xthor.bz'
        self.urls = {
            'login': self.url + '/takelogin.php',
            'search': self.url + '/browse.php?'
        }

        # Proper Strings
        self.proper_strings = ['PROPER']

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'submitme': 'X'
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if not re.search('donate.php', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []
        if not self.login():
            return results

        """
        Séries / Pack TV 13
        Séries / TV FR 14
        Séries / HD FR 15
        Séries / TV VOSTFR 16
        Séries / HD VOSTFR 17
        Mangas (Anime) 32
        Sport 34
        """

        # Search Params
        search_params = {
            'only_free': try_int(self.freeleech),
            'searchin': 'title',
            'incldead': 0,
            'type': 'desc',
            'c13': 1, 'c14': 1, 'c15': 1,
            'c16': 1, 'c17': 1, 'c32': 1
        }

        # Units
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

        def process_column_header(td):
            result = ''
            if td.a:
                result = td.a.get('title', td.a.get_text(strip=True))
            if not result:
                result = td.get_text(strip=True)
            return result

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)

            # Sorting: 1: Name, 3: Comments, 5: Size, 6: Completed, 7: Seeders, 8: Leechers (4: Time ?)
            search_params['sort'] = (7, 4)[mode == 'RSS']

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_params['search'] = search_string

                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find("table", class_="table2 table-bordered2")
                    torrent_rows = []
                    if torrent_table:
                        torrent_rows = torrent_table.find_all("tr")

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    # Catégorie, Nom du Torrent, (Download), (Bookmark), Com., Taille, Compl�t�, Seeders, Leechers
                    labels = [process_column_header(label) for label in torrent_rows[0].find_all('td')]

                    # Skip column headers
                    for row in torrent_rows[1:]:
                        cells = row.find_all('td')
                        if len(cells) < len(labels):
                            continue

                        try:
                            title = cells[labels.index('Nom du Torrent')].get_text(strip=True)
                            download_url = self.url + '/' + row.find("a", href=re.compile("download.php"))['href']
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index('Seeders')].get_text(strip=True))
                            leechers = try_int(cells[labels.index('Leechers')].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the"
                                               u" minimum seeders or leechers: {} (S:{} L:{})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            torrent_size = cells[labels.index('Taille')].get_text()
                            size = convert_size(torrent_size, units=units) or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': None}
                            if mode != 'RSS':
                                logger.log(u"Found result: {0} with {1} seeders and {2} leechers".format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = XthorProvider()
