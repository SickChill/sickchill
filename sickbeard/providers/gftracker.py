# coding=utf-8
# Author: Seamus Wassman
# URL: http://code.google.com/p/sickbeard/
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
import requests
import traceback

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size
from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class GFTrackerProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "GFTracker")

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls = {
            'base_url': 'https://www.thegft.org',
            'login': 'https://www.thegft.org/loginsite.php',
            'search': 'https://www.thegft.org/browse.php?view=%s%s',
            'download': 'https://www.thegft.org/%s',
        }

        self.url = self.urls['base_url']

        self.categories = "0&c26=1&c37=1&c19=1&c47=1&c17=1&c4=1&search="

        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        self.cache = GFTrackerCache(self)

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password}

        # Initialize session with get to have cookies
        initialize = self.get_url(self.url, timeout=30)  # pylint: disable=unused-variable
        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)

        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username or password incorrect', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if not self.login():
            return results

        for mode in search_params:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                search_url = self.urls['search'] % (self.categories, search_string)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                # Returns top 30 results by default, expandable in user profile
                data = self.get_url(search_url)
                if not data:
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        torrent_table = html.find("div", id="torrentBrowse")
                        torrent_rows = torrent_table.findChildren("tr") if torrent_table else []

                        # Continue only if at least one release is found
                        if len(torrent_rows) < 1:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in torrent_rows[1:]:
                            try:
                                cells = result.findChildren("td")
                                title = cells[1].find("a").find_next("a").get('title') or cells[1].find("a").get('title')
                                download_url = self.urls['download'] % cells[3].find("a").get('href')
                                shares = cells[8].get_text().split("/", 1)
                                seeders = int(shares[0])
                                leechers = int(shares[1])

                                torrent_size = cells[7].get_text().split("/", 1)[0]
                                size = convert_size(torrent_size) or -1

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items.append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio


class GFTrackerCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Poll delay in minutes
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider.search(search_params)}

provider = GFTrackerProvider()
