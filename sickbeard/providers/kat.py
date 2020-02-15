# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: http://sickchill.github.io
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

# Third Party Imports
import validators
from requests.compat import urljoin
from collections import OrderedDict
from six.moves import urllib
import traceback
import re

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class KatProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "KickAssTorrents")

        self.public = True

        self.confirmed = True
        self.minseed = None
        self.minleech = None
        self.confirmed = True

        self.mirrors = []
        self.disabled_mirrors = []

        # https://kickasskat.org/tv?field=time_add&sorder=desc
        # https://kickasskat.org/usearch/{query}/?category=tv&field=seeders&sorder=desc

        self.url = "https://kickasskat.org"
        self.urls = None

        self.custom_url = None

        self.cache = tvcache.TVCache(self)

        self.rows_selector = dict(class_=re.compile(r"even|odd"), id=re.compile(r"torrent_.*_torrents"))

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not (self.url and self.urls):
            self.find_domain()
            if not (self.url and self.urls):
                return results

        anime = (self.show and self.show.anime) or (ep_obj and ep_obj.show and ep_obj.show.anime) or False
        search_params = {
            "field": "seeders",
            "sorder": "desc",
            "category": ("tv", "anime")[anime]
        }

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:

                # search_params["q"] = (search_string, None)[mode == "RSS"]
                search_params["field"] = ("seeders", "time_add")[mode == "RSS"]

                if mode != "RSS":
                    if anime:
                        continue

                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                    search_url = self.urls["search"].format(q=search_string)
                else:
                    search_url = self.urls["rss"]

                if self.custom_url:
                    if not validators.url(self.custom_url):
                        logger.log("Invalid custom url: {0}".format(self.custom_url), logger.WARNING)
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                data = self.get_url(search_url, params=OrderedDict(sorted(search_params.items(), key=lambda x: x[0])), returns="text")
                if not data:
                    logger.log("{url} did not return any data, it may be disabled. Trying to get a new domain".format(url=self.url))
                    self.disabled_mirrors.append(self.url)
                    self.find_domain()
                    if self.url in self.disabled_mirrors:
                        logger.log("Could not find a better mirror to try.")
                        logger.log("The search did not return data, if the results are on the site maybe try a custom url, or a different one", logger.INFO)
                        return results

                    # This will recurse a few times until all of the mirrors are exhausted if none of them work.
                    return self.search(search_strings, age, ep_obj)

                with BS4Parser(data, "html5lib") as html:
                    labels = [cell.get_text() for cell in html.find(class_="firstr")("th")]
                    logger.log("Found {} results".format(len(html("tr", **self.rows_selector))))
                    for result in html("tr", **self.rows_selector):
                        try:
                            download_url = urllib.parse.unquote_plus(result.find(title="Torrent magnet link")["href"].split("url=")[1]) + self._custom_trackers
                            parsed_magnet = urllib.parse.parse_qs(download_url)
                            torrent_hash = self.hash_from_magnet(download_url)
                            title = result.find(class_="torrentname").find(class_="cellMainLink").get_text(strip=True)
                            if title.endswith("..."):
                                title = parsed_magnet['dn'][0]

                            if not (title and download_url):
                                if mode != "RSS":
                                    logger.log("Discarding torrent because We could not parse the title and url", logger.DEBUG)
                                continue

                            seeders = try_int(result.find(class_="green").get_text(strip=True))
                            leechers = try_int(result.find(class_="red").get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            if self.confirmed and not result.find(class_="ka-green"):
                                if mode != "RSS":
                                    logger.log("Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it", logger.DEBUG)
                                continue

                            torrent_size = result("td")[labels.index("size")].get_text(strip=True)
                            size = convert_size(torrent_size) or -1

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

    def find_domain(self):
        data = self.get_url("https://kickass.help")
        if data:
            with BS4Parser(data, "html5lib") as html:
                mirrors = html(class_='domainLink')
                if mirrors:
                    self.mirrors = []
                for mirror in mirrors:
                    domain = mirror["href"]
                    if domain not in self.disabled_mirrors:
                        self.mirrors.append(mirror["href"])

        if self.mirrors:
            self.url = self.mirrors[0]
            logger.log("Setting mirror to use to {url}".format(url=self.url))
        else:
            logger.log("Unable to get a working mirror for kickasstorrents, you might need to enable another provider and disable KAT until KAT starts working "
                       "again.", logger.WARNING)

        self.urls = {"search": urljoin(self.url, "/usearch/{q}/"), "rss": urljoin(self.url, "/tv/")}

        return self.url


provider = KatProvider()
