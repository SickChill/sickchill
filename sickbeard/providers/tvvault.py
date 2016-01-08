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
from sickbeard import show_name_helpers
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.exceptions import AuthException
from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TvVaultProvider(TorrentProvider):
    def __init__(self):

        TorrentProvider.__init__(self, "TV-Vault")

        self.urls = {
            'base_url': 'http://tv-vault.me/',
            'login': 'http://tv-vault.me/login.php',
            'search': 'http://tv-vault.me/torrents.php',
        }

        self.url = self.urls['base_url']

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = None

        self.cache = TvVaultCache(self)

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):

        login_params = {
            'username': self.username,
            'password': self.password,
            'keeplogged': 'on',
            'login': 'Login'
        }

        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username Incorrect', response) or re.search('Password Incorrect', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True


    def search(self, search_strings, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self.login():
            return results

        for mode in search_strings.keys():
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)
 #http://tv-vault.me/torrents.php?searchstr=&searchtags=&tags_type=1&groupdesc=
 #&torrentname=&filelist=&container=notselected&format=notselected&aformat=notselected
 #&media=notselected&excludecontainer=notselected&order_by=s3&order_way=desc&disablegrouping=1
 
                seasonname = "Season " + str(ep_obj.scene_season)

                search_params = {
                    'searchstr': show_name_helpers.allPossibleShowNames(self.show),
                    'filter_freeleech': (0, 1)[self.freeleech is True],
                    'order_by': ('seeders', 'time')[mode == 'RSS'],
                    "tags_type": 1,
                    "order_way": "desc",
                    "order_way": "desc",
                    "filelist": seasonname,
                    "disablegrouping": 1
                }

                if not search_string:
                    del search_params['searchstr']

                search_url = self.urls['search'] + "?" + urlencode(search_params)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                data = self.get_url(self.urls['search'], params=search_params)
                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        torrent_table = html.find('table', {'id': 'torrent_table'})
                        if not torrent_table:
                            logger.log(u"Data returned from %s does not contain any torrents" % self.name, logger.DEBUG)
                            continue

                        torrent_rows = torrent_table.findAll('tr', {'class': 'torrent'})
                        # Continue only if one Release is found
                        if not torrent_rows:
                            logger.log(u"Data returned from %s does not contain any torrents" % self.name, logger.DEBUG)
                            continue

                        for torrent_row in torrent_rows:

                            title = torrent_row.find_all('td')[1].find_all('a')[1].text
                            title = re.sub('- Season ', 'S', title, flags=re.IGNORECASE)
                            # title2 = torrent_row.find_all('td')[1].string
                            url = torrent_row.find_all('td')[1].find_all('a')[0]
                            download_url = self.urls['base_url'] + url['href']
                            seeders = torrent_row.find_all('td')[6].text
                            leechers = torrent_row.find_all('td')[7].text

                            torrent_size = torrent_row.find('td', {'class': 'nobr'}).findNext('td', {'class': 'nobr'}).text
                            torrent_size = torrent_size.split('(')[0]  # Remove everything after the units, e.g.: 9.5974 GB(42)
                            size = convert_size(torrent_size) or -1

                            # if not all([title, download_url]):
                            #     continue
                            #
                            # # Filter unseeded torrent
                            # if seeders < self.minseed or leechers < self.minleech:
                            #     if mode != 'RSS':
                            #         logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            #     continue

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

    def seed_ratio(self):
        return self.ratio


class TvVaultCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll TransmitTheNet every 20 minutes max
        self.minTime = 0.5

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}


provider = TvVaultProvider()
