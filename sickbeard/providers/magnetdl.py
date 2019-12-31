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
from slugify import slugify

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class MagnetDLProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        super(MagnetDLProvider, self).__init__("MagnetDL")

        self.minseed = None
        self.minleech = None

        self.url = "http://www.magnetdl.com"
        self.urls = {
            "rss": urljoin(self.url, "download/tv/age/desc/")
        }

        self.custom_url = None
        self.headers.update({'Accept': 'application/html'})

        self.cache = tvcache.TVCache(self)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != "RSS":
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)
                    search = slugify(search_string.decode("utf-8"))
                    search_url = urljoin(self.url, '{}/{}/'.format(search[0], search))
                else:
                    search_url = self.urls['rss']

                if self.custom_url:
                    if not validators.url(self.custom_url):
                        logger.log("Invalid custom url: {0}".format(self.custom_url), logger.WARNING)
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                data = self.get_url(search_url, returns="text")
                if not data:
                    logger.log("URL did not return results/data, if the results are on the site maybe try a custom url, or a different one", logger.DEBUG)
                    continue

                with BS4Parser(data, "html5lib") as html:
                    torrent_table = html.find("table", class_="download")
                    torrent_body = torrent_table.find('tbody') if torrent_table else []
                    torrent_rows = torrent_body("tr") if torrent_body else []

                    # Continue only if at least one Release is found
                    if not torrent_rows:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    labels = [x.get_text(strip=True) for x in torrent_table.find('thead').find('tr')('th')]

                    # Skip column headers
                    for result in torrent_rows[0:-1:2]:
                        try:
                            if len(result("td")) < len(labels):
                                continue

                            title = result.find("td", class_="n").find("a")['title']
                            magnet = result.find("td", class_="m").find("a")['href']
                            seeders = try_int(result.find("td", class_="s").get_text(strip=True))
                            leechers = try_int(result.find("td", class_="l").get_text(strip=True))
                            size = convert_size(result("td")[labels.index('Size')].get_text(strip=True) or '') or -1

                            if not all([title, magnet]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.log("Discarding torrent because it doesn't meet the"
                                               " minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            item = {'title': title, 'link': magnet + self._custom_trackers, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != "RSS":
                                logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                           (title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError as e:
                            continue

                # For each search mode sort all the items by seeders if available
                items.sort(key=lambda d: d.get('seeders', 0), reverse=True)
                results += items

            return results


provider = MagnetDLProvider()
