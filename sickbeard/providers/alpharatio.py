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

from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class AlphaRatioProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "AlphaRatio")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # URLs
        self.url = "https://alpharatio.cc"
        self.urls = {
            "login": urljoin(self.url, "login.php"),
            "search": urljoin(self.url, "torrents.php"),
        }

        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK"]

        # Cache
        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            "username": self.username,
            "password": self.password,
            "login": "submit",
            "remember_me": "on",
        }

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        if re.search("Invalid Username/password", response) \
                or re.search("<title>Login :: AlphaRatio.cc</title>", response):
            logger.log("Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            "searchstr": "",
            "filter_cat[1]": 1,
            "filter_cat[2]": 1,
            "filter_cat[3]": 1,
            "filter_cat[4]": 1,
            "filter_cat[5]": 1
        }

        # Units
        units = ["B", "KB", "MB", "GB", "TB", "PB"]

        def process_column_header(td):
            result = ""
            if td.a and td.a.img:
                result = td.a.img.get("title", td.a.get_text(strip=True))
            if not result:
                result = td.get_text(strip=True)
            return result

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:
                if mode != "RSS":
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_params["searchstr"] = search_string
                search_url = self.urls["search"]
                data = self.get_url(search_url, params=search_params, returns="text")
                if not data:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                with BS4Parser(data, "html5lib") as html:
                    torrent_table = html.find("table", id="torrent_table")
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    # "", "", "Name /Year", "Files", "Time", "Size", "Snatches", "Seeders", "Leechers"
                    labels = [process_column_header(label) for label in torrent_rows[0]("td")]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        cells = result("td")
                        if len(cells) < len(labels):
                            continue

                        try:
                            title = cells[labels.index("Name /Year")].find("a", dir="ltr").get_text(strip=True)
                            download_url = urljoin(self.url, cells[labels.index("Name /Year")].find("a", title="Download")["href"])
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index("Seeders")].get_text(strip=True))
                            leechers = try_int(cells[labels.index("Leechers")].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.log("Discarding torrent because it doesn't meet the"
                                               " minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            torrent_size = cells[labels.index("Size")].get_text(strip=True)
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


provider = AlphaRatioProvider()
