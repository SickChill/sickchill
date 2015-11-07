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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import re
import traceback
from urllib import urlencode

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser
from sickbeard.providers import generic
from sickrage.helper.exceptions import AuthException


class TransmitTheNetProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "TransmitTheNet")

        self.urls = {
            'base_url': 'https://transmithe.net/',
            'index': 'https://transmithe.net/index.php',
        }

        self.url = self.urls['base_url']

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = TransmitTheNetCache(self)

        self.search_params = {
            "page": 'torrents',
            "category": 0,
            "active": 1
        }

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):

        login_params = {
            'uid': self.username,
            'pwd': self.password,
            'remember_me': 'on',
            'login': 'submit'
        }

        response = self.getURL(self.urls['index'], params={'page': 'login'}, post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username Incorrect', response) or re.search('Password Incorrect', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                data = self.getURL(self.urls['index'], params=self.search_params)
                searchURL = self.urls['index'] + "?" + urlencode(self.search_params)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)

                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                try:
                    with BS4Parser(data) as html:

                        torrent_rows = []

                        down_elems = html.findAll("img", {"alt": "Download Torrent"})
                        for down_elem in down_elems:
                            if down_elem:
                                torr_row = down_elem.findParent('tr')
                                if torr_row:
                                    torrent_rows.append(torr_row)

                        # Continue only if one Release is found
                        if len(torrent_rows) < 1:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for torrent_row in torrent_rows:

                            title = torrent_row.find('a', {"data-src": True})['data-src'].rsplit('.', 1)[0]
                            download_href = torrent_row.find('img', {"alt": 'Download Torrent'}).findParent()['href']
                            seeders = int(torrent_row.findAll('a', {'title': 'Click here to view peers details'})[0].text.strip())
                            leechers = int(torrent_row.findAll('a', {'title': 'Click here to view peers details'})[1].text.strip())
                            download_url = self.urls['base_url'] + download_href
                            # FIXME
                            size = -1

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

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class TransmitTheNetCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll TransmitTheNet every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}


provider = TransmitTheNetProvider()
