# Author: Mr_Orange
# URL: https://github.com/mr-orange/Sick-Beard
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import re

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic


class SpeedCDProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "Speedcd")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.urls = {'base_url': 'http://speed.cd/',
                     'login': 'http://speed.cd/take_login.php',
                     'detail': 'http://speed.cd/t/%s',
                     'search': 'http://speed.cd/V3/API/API.php',
                     'download': 'http://speed.cd/download.php?torrent=%s'}

        self.url = self.urls['base_url']

        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c49': 1}, 'RSS': {'c14': 1, 'c2': 1, 'c49': 1}}

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = SpeedCDCache(self)

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Incorrect username or Password. Please try again.', response):
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

                search_string = '+'.join(search_string.split())

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 4, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                parsedJSON = self.getURL(self.urls['search'], post_data=post_data, json=True)
                if not parsedJSON:
                    continue

                try:
                    torrents = parsedJSON.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
                except Exception:
                    continue

                for torrent in torrents:

                    if self.freeleech and not torrent['free']:
                        continue

                    title = re.sub('<[^>]*>', '', torrent['name'])
                    download_url = self.urls['download'] % (torrent['id'])
                    seeders = int(torrent['seed'])
                    leechers = int(torrent['leech'])
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

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class SpeedCDCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll Speedcd every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = SpeedCDProvider()
