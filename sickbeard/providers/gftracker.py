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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import re
import traceback

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.exceptions import AuthException


class GFTrackerProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "GFTracker")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls = {'base_url': 'https://www.thegft.org',
                     'login': 'https://www.thegft.org/loginsite.php',
                     'search': 'https://www.thegft.org/browse.php?view=%s%s',
                     'download': 'https://www.thegft.org/%s',
        }

        self.url = self.urls['base_url']

        self.cookies = None

        self.categories = "0&c26=1&c37=1&c19=1&c47=1&c17=1&c4=1&search="

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = GFTrackerCache(self)

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        # Save cookies from response
        self.cookies = self.headers.get('Set-Cookie')

        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username or password incorrect', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urls['search'] % (self.categories, search_string)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)

                # Set cookies from response
                self.headers.update({'Cookie': self.cookies})
                # Returns top 30 results by default, expandable in user profile
                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        torrent_table = html.find("div", id="torrentBrowse")
                        torrent_rows = torrent_table.findChildren("tr") if torrent_table else []

                        # Continue only if at least one release is found
                        if len(torrent_rows) < 1:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in torrent_rows[1:]:
                            cells = result.findChildren("td")
                            title = cells[1].find("a").find_next("a")
                            link = cells[3].find("a")
                            shares = cells[8].get_text().split("/", 1)
                            torrent_size = cells[7].get_text().split("/", 1)[0]

                            try:
                                if title.has_key('title'):
                                    title = title['title']
                                else:
                                    title = cells[1].find("a")['title']

                                download_url = self.urls['download'] % (link['href'])
                                seeders = int(shares[0])
                                leechers = int(shares[1])

                                size = -1
                                if re.match(r"\d+([,\.]\d+)?\s*[KkMmGgTt]?[Bb]", torrent_size):
                                    size = self._convertSize(torrent_size.rstrip())

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode is not 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

    def _convertSize(self, sizeString):
        size = sizeString[:-2].strip()
        modifier = sizeString[-2:].upper()
        try:
            size = float(size)
            if modifier in 'KB':
                size = size * 1024
            elif modifier in 'MB':
                size = size * 1024**2
            elif modifier in 'GB':
                size = size * 1024**3
            elif modifier in 'TB':
                size = size * 1024**4
        except Exception:
            size = -1
        return int(size)

class GFTrackerCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Poll delay in minutes
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = GFTrackerProvider()
