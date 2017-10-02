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

from __future__ import unicode_literals

import validators
from requests.compat import urljoin

from sickbeard import logger, tvcache
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class BitCannonProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "BitCannon")

        self.minseed = None
        self.minleech = None
        self.custom_url = None
        self.api_key = None

        self.cache = tvcache.TVCache(self, search_params={"RSS": ["tv", "anime"]})

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals
        results = []

        url = "http://localhost:3000/"
        if self.custom_url:
            if not validators.url(self.custom_url, require_tld=False):
                logger.log("Invalid custom url set, please check your settings", logger.WARNING)
                return results
            url = self.custom_url

        search_params = {}

        anime = ep_obj and ep_obj.show and ep_obj.show.anime
        search_params["category"] = ("tv", "anime")[bool(anime)]

        if self.api_key:
            search_params["apiKey"] = self.api_key

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                search_params["q"] = search_string
                if mode != "RSS":
                    logger.log("Search string: {0}".format
                               (search_string.decode('utf-8')), logger.DEBUG)

                search_url = urljoin(url, "api/search")
                parsed_json = self.get_url(search_url, params=search_params, returns="json")
                if not parsed_json:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                if not self._check_auth_from_data(parsed_json):
                    return results

                for result in parsed_json.pop("torrents", {}):
                    try:
                        title = result.pop("title", "")

                        info_hash = result.pop("infoHash", "")
                        download_url = "magnet:?xt=urn:btih:" + info_hash
                        if not all([title, download_url, info_hash]):
                            continue

                        swarm = result.pop("swarm", None)
                        if swarm:
                            seeders = try_int(swarm.pop("seeders", 0))
                            leechers = try_int(swarm.pop("leechers", 0))
                        else:
                            seeders = leechers = 0

                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.log("Discarding torrent because it doesn't meet the "
                                           "minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        size = convert_size(result.pop("size", -1)) or -1
                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                        if mode != "RSS":
                            logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                       (title, seeders, leechers), logger.DEBUG)

                        items.append(item)
                    except (AttributeError, TypeError, KeyError, ValueError):
                        continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results

    @staticmethod
    def _check_auth_from_data(data):
        if not all([isinstance(data, dict),
                    data.pop("status", 200) != 401,
                    data.pop("message", "") != "Invalid API key"]):

            logger.log("Invalid api key. Check your settings", logger.WARNING)
            return False

        return True

provider = BitCannonProvider()
