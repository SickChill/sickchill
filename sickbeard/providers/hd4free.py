# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
#
# URL: https://sick-rage.github.io
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

from __future__ import print_function, unicode_literals

from requests.compat import urljoin

from sickbeard import logger, tvcache
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class HD4FreeProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "HD4Free")

        self.url = 'https://hd4free.xyz'
        self.urls = {'search': urljoin(self.url, '/searchapi.php')}

        self.freeleech = None
        self.username = None
        self.api_key = None
        self.minseed = None
        self.minleech = None

        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll HD4Free every 10 minutes max

    def _check_auth(self):
        if self.username and self.api_key:
            return True

        logger.log('Your authentication credentials for {0} are missing, check your config.'.format(self.name), logger.WARNING)
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
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if self.freeleech:
                    search_params['fl'] = 'true'
                else:
                    search_params.pop('fl', '')

                if mode != 'RSS':
                    logger.log("Search string: " + search_string.strip(), logger.DEBUG)
                    search_params['search'] = search_string
                else:
                    search_params.pop('search', '')

                try:
                    jdata = self.get_url(self.urls['search'], params=search_params, returns='json')
                except ValueError:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                if not jdata:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                error = jdata.get('error')
                if error:
                    logger.log("{}".format(error), logger.DEBUG)
                    return results

                try:
                    if jdata['0']['total_results'] == 0:
                        logger.log("Provider has no results for this search", logger.DEBUG)
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
                                logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        torrent_size = str(jdata[i]["size"]) + ' MB'
                        size = convert_size(torrent_size) or -1
                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}

                        if mode != 'RSS':
                            logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                        items.append(item)
                    except StandardError:
                        continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results


provider = HD4FreeProvider()
