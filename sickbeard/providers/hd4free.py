# coding=utf-8
# Author: Gonçalo (aka duramato) <matigonkas@outlook.com>
# URL: https://github.com/SickRage/SickRage
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

from urllib import urlencode
from sickbeard import logger
from sickbeard import tvcache
from sickrage.providers.TorrentProvider import TorrentProvider


class HD4FREEProvider(TorrentProvider):

    def __init__(self):
        TorrentProvider.__init__(self, "HD4Free")

        self.public = True
        self.url = 'https://hd4free.xyz'
        self.ratio = 0
        self.cache = HD4FREECache(self)
        self.minseed, self.minleech = 2 * [None]
        self.username = None
        self.api_key = None
        self.freeleech = None
		

			
    def _check_auth(self):
        if self.username and self.api_key:
            return True

        raise AuthException('Your authentication credentials for ' + self.name + ' are missing, check your config.')

    def search(self, search_strings, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}
        search_params = {
            'tv': 'true',
            'username': self.username,
            'apikey': self.api_key}
        for mode in search_strings.keys():  # Mode = RSS, Season, Episode
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    search_params['search'] = search_string.encode('utf-8')
                self.search_params['fl'] = 'true' if self.freeleech else 'false'
                if mode != 'RSS':
                    logger.log(u"Search string: " + search_string.strip(), logger.DEBUG)

                searchURL = self.url + "/searchapi.php?" + urlencode(search_params)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                jdata = self.get_url(searchURL, json=True)
                if not jdata:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    return []
					
                results = []
                for i in jdata:
                    seeders = jdata[i]["seeders"]
                    leechers = jdata[i]["leechers"]
                    title = jdata[i]["release_name"]
                    size = jdata[i]["size"]
                    download_url = jdata[i]["download_url"]

                    if not all([title, download_url]):
                        continue

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        continue

                    if mode != 'RSS':
                        logger.log(u"Found result: %s " % title, logger.DEBUG)

                    item = title, download_url, size, seeders, leechers
                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio


class HD4FREECache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Cache results for 10 min
        self.minTime = 10

    def _getRSSData(self):

        search_params = {'RSS': ['']}
        return {'entries': self.provider.search(search_params)}

provider = HD4FREEProvider()
