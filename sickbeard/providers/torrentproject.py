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

from requests.compat import urljoin
import validators

from sickbeard import logger, tvcache
from sickbeard.common import USER_AGENT

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TorrentProjectProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "TorrentProject")

        # Credentials
        self.public = True

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # URLs
        self.url = 'https://torrentproject.se/'

        self.custom_url = None
        self.headers.update({'User-Agent': USER_AGENT})

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self, search_params={'RSS': ['0day']})

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []

        search_params = {
            'out': 'json',
            'filter': 2101,
            'num': 150
        }

        for mode in search_strings:  # Mode = RSS, Season, Episode
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_params['s'] = search_string

                if self.custom_url:
                    if not validators.url(self.custom_url):
                        logger.log("Invalid custom url set, please check your settings", logger.WARNING)
                        return results
                    search_url = self.custom_url
                else:
                    search_url = self.url

                torrents = self.get_url(search_url, params=search_params, returns='json')
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
                            logger.log(u"Torrent doesn't meet minimum seeds & leechers not selecting : {0}".format(title), logger.DEBUG)
                        continue

                    t_hash = torrents[i]["torrent_hash"]
                    torrent_size = torrents[i]["torrent_size"]
                    size = convert_size(torrent_size) or -1

                    try:
                        assert seeders < 10
                        assert mode != 'RSS'
                        logger.log(u"Torrent has less than 10 seeds getting dyn trackers: " + title, logger.DEBUG)

                        if self.custom_url:
                            if not validators.url(self.custom_url):
                                logger.log("Invalid custom url set, please check your settings", logger.WARNING)
                                return results
                            trackers_url = self.custom_url
                        else:
                            trackers_url = self.url

                        trackers_url = urljoin(trackers_url, t_hash)
                        trackers_url = urljoin(trackers_url, "/trackers_json")
                        jdata = self.get_url(trackers_url, returns='json')

                        assert jdata != "maintenance"
                        download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "".join(["&tr=" + s for s in jdata])
                    except (Exception, AssertionError):
                        download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + self._custom_trackers

                    if not all([title, download_url]):
                        continue

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': t_hash}

                    if mode != 'RSS':
                        logger.log(u"Found result: {0} with {1} seeders and {2} leechers".format
                                   (title, seeders, leechers), logger.DEBUG)

                    items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = TorrentProjectProvider()
