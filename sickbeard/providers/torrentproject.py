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

import posixpath  # Must use posixpath
from urllib import quote_plus

from sickbeard import logger, tvcache
from sickbeard.common import USER_AGENT

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TorrentProjectProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "TorrentProject")

        self.public = True
        self.ratio = 0
        self.urls = {'api': u'https://torrentproject.se/', }
        self.url = self.urls['api']
        self.custom_url = None
        self.headers.update({'User-Agent': USER_AGENT})
        self.minseed = None
        self.minleech = None
        self.cache = tvcache.TVCache(self, search_params={'RSS': ['0day']})

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:  # Mode = RSS, Season, Episode
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                search_url = self.urls['api'] + "?s=%s&out=json&filter=2101&num=150" % quote_plus(search_string.encode('utf-8'))
                if self.custom_url:
                    search_url = posixpath.join(self.custom_url, search_url.split(self.url)[1].lstrip('/')) # Must use posixpath

                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)
                torrents = self.get_url(search_url, json=True)
                if not (torrents and "total_found" in torrents and int(torrents["total_found"]) > 0):
                    logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue

                del torrents["total_found"]

                results = []
                for i in torrents:
                    title = torrents[i]["title"]
                    seeders = try_int(torrents[i]["seeds"], 1)
                    leechers = try_int(torrents[i]["leechs"], 0)
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log(u"Torrent doesn't meet minimum seeds & leechers not selecting : %s" % title, logger.DEBUG)
                        continue

                    t_hash = torrents[i]["torrent_hash"]
                    torrent_size = torrents[i]["torrent_size"]
                    size = convert_size(torrent_size) or -1

                    try:
                        assert seeders < 10
                        assert mode != 'RSS'
                        logger.log(u"Torrent has less than 10 seeds getting dyn trackers: " + title, logger.DEBUG)
                        trackerUrl = self.urls['api'] + "" + t_hash + "/trackers_json"
                        if self.custom_url:
                            search_url = posixpath.join(self.custom_url, search_url.split(self.url)[1].lstrip('/')) # Must use posixpath
                        jdata = self.get_url(trackerUrl, json=True)
                        assert jdata != "maintenance"
                        download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "".join(["&tr=" + s for s in jdata])
                    except (Exception, AssertionError):
                        download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + self._custom_trackers

                    if not all([title, download_url]):
                        continue

                    item = title, download_url, size, seeders, leechers

                    if mode != 'RSS':
                        logger.log(u"Found result: %s" % title, logger.DEBUG)

                    items.append(item)

            # For each search mode sort all the items by seeders
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = TorrentProjectProvider()
