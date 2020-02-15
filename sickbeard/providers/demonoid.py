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

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
from requests.compat import urljoin
import time
import traceback

# First Party Imports
import sickbeard
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickbeard.common import cpu_presets
from sickchill.helper.common import convert_size, try_int
from requests.utils import add_dict_to_cookiejar
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class DemonoidProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Demonoid")

        self.public = True
        self.minseed = None
        self.sorting = None
        self.minleech = None

        self.url = "https://demonoid.is"
        self.urls = {"RSS": urljoin(self.url, 'rss.php'), 'search': urljoin(self.url, 'files/')}

        self.proper_strings = ["PROPER|REPACK"]

        self.cache_rss_params = {
            "category": 12, "quality": 58, "seeded": 0, "external": 2, "sort": "added", "order": "desc"
        }

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        # https://demonoid.is/files/?category=12&quality=58&seeded=0&external=2&sort=seeders&order=desc&query=SEARCH_STRING
        search_params = {
            "category": "12",  # 12: TV
            "seeded": 0,  # 0: True
            "external": 2,  # 0: Demonoid (Only works if logged in), 1: External, 2: Both
            "order": "desc",
            "sort": self.sorting or "seeders"
        }

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            if mode == "RSS":
                raise Exception('This should be calling the cache, not the search method for RSS/Daily searches')

            for search_string in search_strings[mode]:
                search_params["query"] = search_string
                logger.log("Search string: {0}".format
                           (search_string.decode("utf-8")), logger.DEBUG)

                time.sleep(cpu_presets[sickbeard.CPU_PRESET])

                data = self.get_url(self.urls['search'], params=search_params)
                if not data:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                with BS4Parser(data, "html5lib") as html:
                    for result in html("img", alt="Download torrent"):
                        try:
                            title = result.parent['title']
                            details_url = result.parent['href']

                            if not (title and details_url):
                                if mode != "RSS":
                                    logger.log("Discarding torrent because We could not parse the title and details", logger.DEBUG)
                                continue

                            info = result.parent.parent.find_next_siblings("td")
                            size = convert_size(info[0].get_text(strip=True)) or -1
                            seeders = try_int(info[3].get_text(strip=True))
                            leechers = try_int(info[4].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            download_url, magnet, torrent_hash = self.get_details(details_url)
                            if not all([download_url, magnet, torrent_hash]):
                                logger.log("Failed to get all required information from the details page. url:{}, magnet:{}, hash:{}".format(
                                    bool(download_url), bool(magnet), bool(torrent_hash))
                                )
                                continue

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': torrent_hash}
                            if mode != "RSS":
                                logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                            items.append(item)

                        except (AttributeError, TypeError, KeyError, ValueError, Exception) as e:
                            logger.log(traceback.format_exc(e))
                            continue

                            # For each search mode sort all the items by seeders if available
                items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

                results += items

            return results

    def get_details(self, url):
        download = magnet = torrent_hash = None
        details_data = self.get_url(urljoin(self.url, url))
        if not details_data:
            logger.log("No data returned from details page for result", logger.DEBUG)
            return download, magnet, torrent_hash

        with BS4Parser(details_data, "html5lib") as html:
            magnet = html.find("img", src="/images/orange.png").parent['href'] + self._custom_trackers
            download = html.find("img", src="/images/blue.png").parent['href']
            torrent_hash = self.hash_from_magnet(magnet)

        return download, magnet, torrent_hash


class DemonoidCache(tvcache.TVCache):
    def _get_rss_data(self):
        if self.provider.cookies:
            add_dict_to_cookiejar(self.provider.session.cookies, dict(x.rsplit('=', 1) for x in self.provider.cookies.split(';')))

        return self.get_rss_feed(self.provider.urls['RSS'], self.provider.cache_rss_params)


provider = DemonoidProvider()
