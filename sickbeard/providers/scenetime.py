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

from __future__ import print_function, unicode_literals

from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class SceneTimeProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "SceneTime")

        self.username = None
        self.password = None
        self.minseed = None
        self.minleech = None

        self.enable_cookies = True

        self.cache = tvcache.TVCache(self)  # only poll SceneTime every 20 minutes max

        self.urls = {'base_url': 'https://www.scenetime.com',
                     'login': 'https://www.scenetime.com/takelogin.php',
                     'detail': 'https://www.scenetime.com/details.php?id=%s',
                     'apisearch': 'https://www.scenetime.com/browse.php',
                     'download': 'https://www.scenetime.com/download.php/%s/%s'}

        self.url = self.urls['base_url']

        self.categories = [2, 42, 9, 63, 77, 79, 100, 83]

    def login(self):
        cookie_dict = dict_from_cookiejar(self.session.cookies)
        if cookie_dict.get('uid') and cookie_dict.get('pass'):
            return True

        if self.cookies:
            success, status = self.add_cookies_from_ui()
            if not success:
                logger.log(status, logger.INFO)
                return False

            login_params = {'username': self.username, 'password': self.password}

            response = self.get_url(self.urls['login'], post_data=login_params, returns='response')
            if not response or response.status_code != 200:
                logger.log("Unable to connect to provider", logger.WARNING)
                return False

            if dict_from_cookiejar(self.session.cookies).get('uid') in response.text:
                return True
            else:
                logger.log('Failed to login, check your cookies', logger.WARNING)
                return False

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals
        results = []
        if not self.login():
            return results

        for mode in search_params:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                query = { 'sec': 'jax', 'cata': 'yes', 'search': search_string }
                query.update({"c"+str(i): 1 for i in self.categories})

                data = self.get_url(self.urls['apisearch'], returns='text', post_data=query)

                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find(id='torrenttable')
                    if torrent_table:
                        torrent_rows = torrent_table.findAll('tr')
                    else:
                        torrent_rows = []

                    # Continue only if one Release is found
                    if len(torrent_rows) < 2:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    # Scenetime apparently uses different number of cells in #torrenttable based
                    # on who you are. This works around that by extracting labels from the first
                    # <tr> and using their index to find the correct download/seeders/leechers td.
                    labels = [label.get_text(strip=True) or label.img['title'] for label in torrent_rows[0]('td')]

                    for result in torrent_rows[1:]:
                        try:
                            cells = result('td')

                            link = cells[labels.index('Name')].find('a')
                            torrent_id = link['href'].replace('details.php?id=', '').split("&")[0]

                            title = link.get_text(strip=True)
                            download_url = self.urls['download'] % (torrent_id, "{0}.torrent".format(title.replace(" ", ".")))

                            seeders = try_int(cells[labels.index('Seeders')].get_text(strip=True))
                            leechers = try_int(cells[labels.index('Leechers')].get_text(strip=True))
                            torrent_size = cells[labels.index('Size')].get_text()

                            size = convert_size(torrent_size) or -1

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                        if mode != 'RSS':
                            logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                        items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items
        
        return results

provider = SceneTimeProvider()
