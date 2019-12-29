# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
#
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import time

import sickbeard
from sickbeard import logger, tvcache
from sickbeard.common import cpu_presets
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class RarbgProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "Rarbg")

        self.public = True
        self.minseed = None
        self.ranked = None
        self.sorting = None
        self.minleech = None
        self.token = None
        self.token_expires = None

        # Spec: https://torrentapi.org/apidocs_v2.txt
        self.url = "https://rarbg.com"
        self.urls = {"api": "http://torrentapi.org/pubapi_v2.php"}

        self.proper_strings = ["{{PROPER|REPACK}}"]

        self.cache = tvcache.TVCache(self, min_time=10)  # only poll RARBG every 10 minutes max

    def login(self):
        if self.token and self.token_expires and datetime.datetime.now() < self.token_expires:
            return True

        login_params = {
            "get_token": "get_token",
            "format": "json",
            "app_id": "sickchill"
        }

        response = self.get_url(self.urls["api"], params=login_params, returns="json")
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        self.token = response.get("token")
        self.token_expires = datetime.datetime.now() + datetime.timedelta(minutes=14) if self.token else None
        return self.token is not None

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []
        if not self.login():
            return results

        search_params = {
            "app_id": "sickchill",
            "category": "tv",
            "min_seeders": try_int(self.minseed),
            "min_leechers": try_int(self.minleech),
            "limit": 100,
            "format": "json_extended",
            "ranked": try_int(self.ranked),
            "token": self.token,
        }

        if ep_obj is not None:
            ep_indexerid = ep_obj.show.indexerid
            ep_indexer = ep_obj.show.idxr.slug
        else:
            ep_indexerid = None
            ep_indexer = None

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            if mode == "RSS":
                search_params["sort"] = "last"
                search_params["mode"] = "list"
                search_params.pop("search_string", None)
                search_params.pop("search_tvdb", None)
            else:
                search_params["sort"] = self.sorting if self.sorting else "seeders"
                search_params["mode"] = "search"

                if ep_indexer == 'tvdb' and ep_indexerid:
                    search_params["search_tvdb"] = ep_indexerid
                else:
                    search_params.pop("search_tvdb", None)

            for search_string in search_strings[mode]:
                if mode != "RSS":
                    search_params["search_string"] = search_string
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
                data = self.get_url(self.urls["api"], params=search_params, returns="json")
                if not isinstance(data, dict):
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                error = data.get("error")
                error_code = data.get("error_code")
                # Don't log when {"error":"No results found","error_code":20}
                # List of errors: https://github.com/rarbg/torrentapi/issues/1#issuecomment-114763312
                if error:
                    if try_int(error_code) != 20:
                        logger.log(error)
                    continue

                torrent_results = data.get("torrent_results")
                if not torrent_results:
                    logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue

                for item in torrent_results:
                    try:
                        title = item.pop("title")
                        download_url = item.pop("download")
                        if not all([title, download_url]):
                            continue

                        seeders = item.pop("seeders")
                        leechers = item.pop("leechers")
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.log("Discarding torrent because it doesn't meet the"
                                           " minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        torrent_size = item.pop("size", -1)
                        size = convert_size(torrent_size) or -1
                        torrent_hash = self.hash_from_magnet(download_url)

                        if mode != "RSS":
                            logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                       (title, seeders, leechers), logger.DEBUG)

                        result = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': torrent_hash}
                        items.append(result)
                    except StandardError:
                        continue

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = RarbgProvider()
