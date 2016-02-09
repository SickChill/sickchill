# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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

from urllib import urlencode
from urlparse import urljoin

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class BitCannonProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "BitCannon")

        self.minseed = None
        self.minleech = None
        self.ratio = 0
        self.custom_url = None
        self.api_key = None

        self.cache = tvcache.TVCache(self, search_params={'RSS': ['tv', 'anime']})

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals
        results = []

        url = self.make_url()
        if not url:
            return results

        search_params = {}

        anime = ep_obj and ep_obj.show and ep_obj.show.anime
        search_params['category'] = ('tv', 'anime')[bool(anime)]

        if self.api_key:
            search_params['apiKey'] = self.api_key

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: {}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                search_params['q'] = search_string.encode('utf-8')
                if mode != 'RSS':
                    logger.log(u"Search string: {}".format(search_string), logger.DEBUG)

                search_url = urljoin(url, "api/search")
                logger.log(u"Search URL: {}?{}".format
                           (search_url, urlencode(search_params)), logger.DEBUG)

                parsed_json = self.get_url(search_url, params=search_params, json=True)
                if not parsed_json:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                if not self._check_auth_from_data(parsed_json):
                    return results

                for result in parsed_json.pop('torrents', {}):
                    try:
                        title = result.pop('title', '')

                        info_hash = result.pop('infoHash', '')
                        download_url = "magnet:?xt=urn:btih:" + info_hash
                        if not all([title, download_url, info_hash]):
                            continue

                        swarm = result.pop('swarm', None)
                        if swarm:
                            seeders = try_int(swarm.pop('seeders', 0))
                            leechers = try_int(swarm.pop('leechers', 0))
                        else:
                            seeders = leechers = 0

                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the "
                                           "minimum seeders or leechers: {} (S:{} L:{})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        size = convert_size(result.pop('size', -1)) or -1
                        item = title, download_url, size, seeders, leechers
                        if mode != 'RSS':
                            logger.log(u"Found result: {} with {} seeders and {} leechers".format
                                       (title, seeders, leechers), logger.DEBUG)

                        items.append(item)
                    except (AttributeError, TypeError, KeyError, ValueError):
                        continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)
            results += items

        return results

    def seed_ratio(self):
        return self.ratio

    def make_url(self):
        url = 'http://localhost:3000/'
        if self.custom_url:
            if not self.custom_url.lower().startswith('http'):
                logger.log(u"Invalid custom url set for BitCannon, please check your settings", logger.WARNING)
                return ''

            url = self.custom_url
            if not url.endswith('/'):
                url += '/'

        return url

    @staticmethod
    def _check_auth_from_data(data):
        if not all([isinstance(data, dict),
                    data.pop('status', 200) != 401,
                    data.pop('message', '') != 'Invalid API key']):

            logger.log(u"Invalid api key. Check your settings", logger.WARNING)
            return False

        return True

provider = BitCannonProvider()
