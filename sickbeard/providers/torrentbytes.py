# coding=utf-8
# Author: Idan Gutman
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
from urllib import quote

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TorrentBytesProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "TorrentBytes")

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = False

        self.urls = {
            'base_url': 'https://www.torrentbytes.net',
            'login': 'https://www.torrentbytes.net/takelogin.php',
            'detail': 'https://www.torrentbytes.net/details.php?id=%s',
            'search': 'https://www.torrentbytes.net/browse.php?search=%s%s',
            'download': 'https://www.torrentbytes.net/download.php?id=%s&name=%s'
        }

        self.url = self.urls['base_url']

        self.categories = "&c41=1&c33=1&c38=1&c32=1&c37=1"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = tvcache.TVCache(self)

    def login(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'login': 'Log in!'}

        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username or password incorrect', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []
        if not self.login():
            return results

        for mode in search_params:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                search_url = self.urls['search'] % (quote(search_string.encode('utf-8')), self.categories)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                data = self.get_url(search_url)
                if not data:
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        # Continue only if one Release is found
                        empty = html.find('Nothing found!')
                        if empty:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrent_table = html.find('table', attrs={'border': '1'})
                        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                        for result in torrent_rows[1:]:
                            cells = result.find_all('td')
                            torrent_size = None
                            link = cells[1].find('a', attrs={'class': 'index'})

                            full_id = link['href'].replace('details.php?id=', '')
                            torrent_id = full_id.split("&")[0]

                            # Free leech torrents are marked with green [F L] in the title (i.e. <font color=green>[F&nbsp;L]</font>)
                            freeleechTag = cells[1].find('font', attrs={'color': 'green'})
                            if freeleechTag and freeleechTag.text == u'[F\xa0L]':
                                isFreeleechTorrent = True
                            else:
                                isFreeleechTorrent = False

                            if self.freeleech and not isFreeleechTorrent:
                                continue

                            try:
                                if link.get('title', ''):
                                    title = cells[1].find('a', {'class': 'index'})['title']
                                else:
                                    title = link.contents[0]
                                download_url = self.urls['download'] % (torrent_id, link.contents[0])
                                seeders = int(cells[8].find('span').contents[0])
                                leechers = int(cells[9].find('span').contents[0])

                                # Need size for failed downloads handling
                                torrent_size = cells[6].text if torrent_size is None else torrent_size

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            size = convert_size(torrent_size) or -1

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                            items.append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = TorrentBytesProvider()
