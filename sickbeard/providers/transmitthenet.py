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
from sickrage.helper.common import try_int

class TransmitTheNetProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "TransmitTheNet")

        self.urls = {
            'base_url': 'https://transmithe.net/',
            'login': 'https://transmithe.net/login.php',
            'search': 'https://transmithe.net/torrents.php',
        }

        self.url = self.urls['base_url']

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = None

        self.cache = TransmitTheNetCache(self)

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):

        login_params = {
            'username': self.username,
            'password': self.password,
            'keeplogged': 'on',
            'login': 'Login'
        }

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
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

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                search_params = {
                    'searchtext': search_string,
                    'filter_freeleech': (0, 1)[self.freeleech is True],
                    'order_by': ('seeders', 'time')[mode == 'RSS'],
                    "order_way": "desc"
                }

                if not search_string:
                    del search_params['searchtext']

                searchURL = self.urls['search'] + "?" + urlencode(search_params)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)

                data = self.getURL(self.urls['search'], params=search_params)
                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        torrent_table = html.find('table', {'id':'torrent_table'})
                        torrent_rows = torrent_table.findAll('tr', {'class':'torrent'})
                        # Continue only if one Release is found
                        if not torrent_rows:
                            logger.log(u"Data returned from %s does not contain any torrents" % self.name, logger.DEBUG)
                            continue

                        for torrent_row in torrent_rows:
                            freeleech = torrent_row.find('img', alt="Freeleech") is not None
                            if self.freeleech and not freeleech:
                                continue

                            download_url = self.urls['base_url'] + torrent_row.find('a', {"title": 'Download Torrent'})['href']

                            temp_anchor = torrent_row.find('a', {"data-src": True})
                            title = temp_anchor['data-src'].rsplit('.', 1)[0]
                            size = try_int(temp_anchor['data-filesize'])

                            temp_anchor = torrent_row.find('span', class_='time').parent.find_next_sibling()
                            seeders = try_int(temp_anchor.text.strip())
                            leechers = try_int(temp_anchor.find_next_sibling().text.strip())


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
