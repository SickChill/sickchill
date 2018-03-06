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
# along with SickRage. If not, see <https://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

import validators
from requests.compat import urljoin

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class ThePirateBayProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "ThePirateBay")

        # Credentials
        self.public = True

        # Torrent Stats
        self.minseed = None
        self.minleech = None
        self.confirmed = True

        # URLs
        self.url = "https://thepiratebay.org"
        self.urls = {
            "rss": [urljoin(self.url, "browse/208/0/4/0"), urljoin(self.url, "browse/205/0/4/0")],
            "search": urljoin(self.url, "search"),
        }
        self.custom_url = None

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)  # only poll ThePirateBay every 30 minutes max

        self.magnet_regex = re.compile(r'magnet:\?xt=urn:btih:\w{32,40}(:?&dn=[\w. %+-]+)*(:?&tr=(:?tcp|https?|udp)[\w%. +-]+)*')

    @staticmethod
    def convert_url(url, params):
        # noinspection PyBroadException
        try:
            return urljoin(url, '{type}/{q}/{page}/{orderby}/{category}'.format(**params)), {}
        except Exception:
            return url.replace('search', 's/'), params

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []
        """
        205 = SD, 208 = HD, 200 = All Videos
        https://pirateproxy.pl/s/?q=Game of Thrones&type=search&orderby=7&page=0&category=200
        """
        # oder_by is 7 in browse for seeders, but 8 in search!
        search_params = {
            "q": "",
            "type": "search",
            "orderby": 8,
            "page": 0,
            "category": 200
        }

        # Units
        units = ["B", "KIB", "MIB", "GIB"]

        def process_column_header(th):
            text = ""
            if th.a:
                text = th.a.get_text(strip=True)
            if not text:
                text = th.get_text(strip=True)
            return text

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:
                search_urls = (self.urls["search"], self.urls["rss"])[mode == "RSS"]
                if not isinstance(search_urls, list):
                    search_urls = [search_urls]

                for search_url in search_urls:
                    if self.custom_url:
                        if not validators.url(self.custom_url):
                            logger.log("Invalid custom url: {0}".format(self.custom_url), logger.WARNING)
                            return results
                        search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                    if mode != "RSS":
                        search_params["q"] = search_string
                        logger.log("Search string: {}".format
                                   (search_string.decode("utf-8")), logger.DEBUG)

                        # Prevents a 302 redirect, since there is always a 301 from .se to the best mirror having an extra
                        # redirect is excessive on the provider and spams the debug log unnecessarily
                        search_url, params = self.convert_url(search_url, search_params)
                        data = self.get_url(search_url, params=params, returns="text")
                    else:
                        data = self.get_url(search_url, returns="text")

                    if not data:
                        logger.log("URL did not return data, maybe try a custom url, or a different one", logger.DEBUG)
                        continue

                    with BS4Parser(data, "html5lib") as html:
                        torrent_table = html.find("table", id="searchResult")
                        torrent_rows = torrent_table("tr") if torrent_table else []

                        # Continue only if at least one Release is found
                        if len(torrent_rows) < 2:
                            logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        labels = [process_column_header(label) for label in torrent_rows[0]("th")]

                        # Skip column headers
                        for result in torrent_rows[1:]:
                            try:
                                cells = result("td")

                                # Funky js on page messing up titles, this fixes that
                                title = result.find(class_="detLink")['title'].split('Details for ', 1)[-1]
                                download_url = result.find(title="Download this torrent using magnet")["href"] + self._custom_trackers
                                if not self.magnet_regex.match(download_url):
                                    logger.log("Got an invalid magnet: {0}".format(download_url))
                                    logger.log("Invalid ThePirateBay proxy please try another one", logger.DEBUG)
                                    continue

                                if not all([title, download_url]):
                                    continue

                                seeders = try_int(cells[labels.index("SE")].get_text(strip=True))
                                leechers = try_int(cells[labels.index("LE")].get_text(strip=True))

                                # Filter unseeded torrent
                                if seeders < self.minseed or leechers < self.minleech:
                                    if mode != "RSS":
                                        logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                                   (title, seeders, leechers), logger.DEBUG)
                                    continue

                                # Accept Torrent only from Good People for every Episode Search
                                if self.confirmed and not result.find(alt=re.compile(r"VIP|Trusted")):
                                    if mode != "RSS":
                                        logger.log("Found result: {0} but that doesn't seem like a trusted result so I'm ignoring it".format(title), logger.DEBUG)
                                    continue

                                # Convert size after all possible skip scenarios
                                torrent_size = re.sub(r".*Size ([\d.]+).+([KMGT]iB).*", r"\1 \2", result.find(class_="detDesc").get_text(strip=True))
                                size = convert_size(torrent_size, units=units) or -1

                                item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                                if mode != "RSS":
                                    logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                               (title, seeders, leechers), logger.DEBUG)

                                items.append(item)
                            except StandardError:
                                continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = ThePirateBayProvider()
