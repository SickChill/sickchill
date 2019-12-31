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

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# Third Party Imports
import validators
from requests.compat import urljoin

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class SkyTorrents(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "SkyTorrents")

        self.public = True

        self.minseed = None
        self.minleech = None

        self.url = "https://www.skytorrents.lol"
        # https://www.skytorrents.lol/rss?query=game+of+thrones&type=video&sort=seeders
        self.urls = {"search": urljoin(self.url, "/rss")}

        self.custom_url = None

        self.cache = tvcache.TVCache(self, search_params={"RSS": [""]})

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []
        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != "RSS":
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_url = self.urls["search"]
                if self.custom_url:
                    if not validators.url(self.custom_url):
                        logger.log("Invalid custom url: {0}".format(self.custom_url), logger.WARNING)
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                search_params = {'query': search_string, 'sort': ('seeders', 'created')[mode == 'RSS'], 'type': 'video', 'tag': 'hd'}
                data = self.get_url(search_url, params=search_params, returns='text')
                if not data:
                    logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    for item in html('item'):
                        try:
                            title = item.title.get_text(strip=True)
                            download_url = item.magneturl.get_text(strip=True)
                            if not (title and download_url):
                                continue

                            size = try_int(item.size.get_text(strip=True))
                            seeders = leechers = 0
                            info_hash = None

                            for attr in item.find_all(['newznab:attr', 'torznab:attr']):
                                seeders = try_int(attr['value']) if attr['name'] == 'seeders' else seeders
                                leechers = try_int(attr['value']) if attr['name'] == 'peers' else leechers
                                info_hash = attr['value'] if attr['name'] == 'infohash' else info_hash

                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': info_hash}
                            if mode != "RSS":
                                logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers),
                                           logger.DEBUG)

                            items.append(item)

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results

provider = SkyTorrents()
