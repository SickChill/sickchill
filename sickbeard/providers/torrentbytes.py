# coding=utf-8
# Author: Idan Gutman
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
import re

# Third Party Imports
from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class TorrentBytesProvider(TorrentProvider):

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "TorrentBytes")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None
        self.freeleech = False

        # URLs
        self.url = "https://www.torrentbytes.net"
        self.urls = {
            "login": urljoin(self.url, "takelogin.php"),
            "search": urljoin(self.url, "browse.php")
        }

        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK"]

        # Cache
        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {"username": self.username,
                        "password": self.password,
                        "login": "Log in!"}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        if re.search("Username or password incorrect", response):
            logger.log("Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        search_params = {
            "Episode": {"c33": 1, "c38": 1, "c32": 1, "c37": 1},
            "Season": {"c41": 1}
        }

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != "RSS":
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_params[mode]["search"] = search_string
                data = self.get_url(self.urls["search"], params=search_params[mode], returns="text")
                if not data:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                with BS4Parser(data, "html5lib") as html:
                    torrent_table = html.find("table", border="1")
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    # "Type", "Name", Files", "Comm.", "Added", "TTL", "Size", "Snatched", "Seeders", "Leechers"
                    labels = [label.get_text(strip=True) for label in torrent_rows[0]("td")]

                    for result in torrent_rows[1:]:
                        try:
                            cells = result("td")

                            download_url = urljoin(self.url, cells[labels.index("Name")].find("a", href=re.compile(r"download.php\?id="))["href"])
                            title_element = cells[labels.index("Name")].find("a", href=re.compile(r"details.php\?id="))
                            title = title_element.get("title", "") or title_element.get_text(strip=True)
                            if not all([title, download_url]):
                                continue

                            if self.freeleech:
                                # Free leech torrents are marked with green [F L] in the title (i.e. <font color=green>[F&nbsp;L]</font>)
                                freeleech = cells[labels.index("Name")].find("font", color="green")
                                if not freeleech or freeleech.get_text(strip=True) != "[F\xa0L]":
                                    continue

                            seeders = try_int(cells[labels.index("Seeders")].get_text(strip=True))
                            leechers = try_int(cells[labels.index("Leechers")].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            # Need size for failed downloads handling
                            torrent_size = cells[labels.index("Size")].get_text(strip=True)
                            size = convert_size(torrent_size) or -1
                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}

                            if mode != "RSS":
                                logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except (AttributeError, TypeError, ValueError):
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = TorrentBytesProvider()
