# -*- coding: latin-1 -*-
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
from urllib import urlencode

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class XthorProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "Xthor")

        self.url = 'https://xthor.bz'
        self.urls = {
            'login': self.url + '/takelogin.php',
            'search': self.url + '/browse.php?'
        }

        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.username = None
        self.password = None
        self.freeleech = None
        self.proper_strings = ['PROPER']
        self.cache = tvcache.TVCache(self, min_time=30)

    def login(self):

        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'submitme': 'X'}

        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('donate.php', response):
            return True
        else:
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
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
        search_params = {
            'only_free': try_int(self.freeleech),
            'searchin': 'title',
            'incldead': 0,
            'type': 'desc',
            'c13': 1, 'c14': 1, 'c15': 1,
            'c16': 1, 'c17': 1, 'c32': 1
        }

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)

            # Sorting: 1: Name, 3: Comments, 5: Size, 6: Completed, 7: Seeders, 8: Leechers (4: Time ?)
            search_params['sort'] = (7, 4)[mode == 'RSS']
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                search_params['search'] = search_string
                search_url = self.urls['search'] + urlencode(search_params)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)
                data = self.get_url(search_url)
                if not data:
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

                    def process_column_header(td):
                        result = ''
                        if td.a:
                            result = td.a.get('title', td.a.get_text(strip=True))
                        if not result:
                            result = td.get_text(strip=True)
                        return result

                    # Catégorie, Nom du Torrent, (Download), (Bookmark), Com., Taille, Compl�t�, Seeders, Leechers
                    labels = [process_column_header(label) for label in torrent_rows[0].find_all('td')]

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
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            size = convert_size(cells[labels.index('Taille')].get_text(strip=True))

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)
                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = XthorProvider()
