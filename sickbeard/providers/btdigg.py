# coding=utf-8
# Author: Jodi Jones <venom@gen-x.co.nz>
# Rewrite: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class BTDiggProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "BTDigg")

        self.public = True
        self.url = "https://btdigg.org"
        self.urls = {"api": "https://api.btdigg.org/api/private-341ada3245790954/s02"}

        self.proper_strings = ["PROPER", "REPACK"]

        # Use this hacky way for RSS search since most results will use this codecs
        cache_params = {"RSS": ["x264", "x264.HDTV", "720.HDTV.x264"]}

        # Only poll BTDigg every 30 minutes max, since BTDigg takes some time to crawl
        self.cache = tvcache.TVCache(self, min_time=30, search_params=cache_params)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        search_params = {"p": 0}
        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                search_params["q"] = search_string
                if mode != "RSS":
                    search_params["order"] = 0
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)
                else:
                    search_params["order"] = 2

                jdata = self.get_url(self.urls["api"], params=search_params, returns="json")
                if not jdata:
                    logger.log("Provider did not return data", logger.DEBUG)
                    continue

                for torrent in jdata:
                    try:
                        title = torrent.pop("name", "")
                        download_url = torrent.pop("magnet") + self._custom_trackers if torrent["magnet"] else None
                        if not all([title, download_url]):
                            continue

                        if float(torrent.pop("ff")):
                            logger.log("Ignoring result for {0} since it's been reported as fake (level = {1})".format
                                       (title, torrent["ff"]), logger.DEBUG)
                            continue

                        if not int(torrent.pop("files")):
                            logger.log("Ignoring result for {0} because it has no files".format
                                       (title), logger.DEBUG)
                            continue

                        # Provider doesn't provide seeders/leechers
                        seeders = 1
                        leechers = 0

                        torrent_size = torrent.pop("size")
                        size = convert_size(torrent_size) or -1

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': None}
                        if mode != "RSS":
                            logger.log("Found result: {0!s} ".format(title), logger.DEBUG)

                        items.append(item)

                    except StandardError:
                        continue

            results += items

        return results


provider = BTDiggProvider()
