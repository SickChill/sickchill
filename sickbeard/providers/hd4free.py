# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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

from requests.compat import urlencode

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class HD4FreeProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "HD4Free")

        self.url = 'https://hd4free.xyz'
        self.urls = {'search': self.url + '/searchapi.php'}

        self.freeleech = None
        self.username = None
        self.api_key = None
        self.minseed = None
        self.minleech = None
        self.ratio = 0

        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll HD4Free every 10 minutes max

    def _check_auth(self):
        if self.username and self.api_key:
            return True

        logger.log('Your authentication credentials for %s are missing, check your config.' % self.name, logger.WARNING)
        return False

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if not self._check_auth:
            return results

        search_params = {
            'tv': 'true',
            'username': self.username,
            'apikey': self.api_key
        }

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: {}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if self.freeleech:
                    search_params['fl'] = 'true'
                else:
                    search_params.pop('fl', '')

                if mode != 'RSS':
                    logger.log(u"Search string: " + search_string.strip(), logger.DEBUG)
                    search_params['search'] = search_string
                else:
                    search_params.pop('search', '')

                search_url = self.urls['search'] + "?" + urlencode(search_params)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                jdata = self.get_url(search_url, json=True)
                if not jdata:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                try:
                    if jdata['0']['total_results'] == 0:
                        logger.log(u"Provider has no results for this search", logger.DEBUG)
                        continue
                except StandardError:
                    continue

                for i in jdata:
                    try:
                        title = jdata[i]["release_name"]
                        download_url = jdata[i]["download_url"]
                        if not all([title, download_url]):
                            continue

                        seeders = jdata[i]["seeders"]
                        leechers = jdata[i]["leechers"]
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {} (S:{} L:{})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        torrent_size = str(jdata[i]["size"]) + ' MB'
                        size = convert_size(torrent_size) or -1
                        item = title, download_url, size, seeders, leechers

                        if mode != 'RSS':
                            logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                        items.append(item)
                    except StandardError:
                        continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = HD4FreeProvider()
