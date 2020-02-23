# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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
import traceback

# Third Party Imports
from bs4 import BeautifulSoup

# First Party Imports
import sickbeard
from sickbeard import logger, tvcache
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class LimeTorrentsProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "LimeTorrents")

        self.urls = {
            'index': 'https://www.limetorrents.info/',
            'search': 'https://www.limetorrents.info/searchrss/',
            'rss': 'https://www.limetorrents.info/rss/tv/'
        }

        self.url = self.urls['index']

        self.public = True
        self.minseed = None
        self.minleech = None

        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        self.cache = tvcache.TVCache(self, search_params={'RSS': ['rss']})

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                try:
                    search_url = (self.urls['rss'], self.urls['search'] + search_string + '/')[mode != 'RSS']

                    data = self.get_url(search_url, returns='text')
                    if not data:
                        logger.log("No data returned from provider", logger.DEBUG)
                        continue

                    if not data.startswith('<?xml'):
                        logger.log('Expected xml but got something else, is your mirror failing?', logger.INFO)
                        continue

                    data = BeautifulSoup(data, 'html5lib')

                    entries = data('item')
                    if not entries:
                        logger.log('Returned xml contained no results', logger.INFO)
                        continue

                    for item in entries:
                        try:
                            title = item.title.text
                            # Use the itorrents link limetorrents provides,
                            # unless it is not itorrents or we are not using blackhole
                            # because we want to use magnets if connecting direct to client
                            # so that proxies work.
                            download_url = item.enclosure['url']
                            if sickbeard.TORRENT_METHOD != "blackhole" or 'itorrents' not in download_url:
                                download_url = item.enclosure['url']
                                # http://itorrents.org/torrent/C7203982B6F000393B1CE3A013504E5F87A46A7F.torrent?title=The-Night-of-the-Generals-(1967)[BRRip-1080p-x264-by-alE13-DTS-AC3][Lektor-i-Napisy-PL-Eng][Eng]
                                # Keep the hash a separate string for when its needed for failed
                                torrent_hash = re.match(r"(.*)([A-F0-9]{40})(.*)", download_url, re.I).group(2)
                                download_url = "magnet:?xt=urn:btih:" + torrent_hash + "&dn=" + title + self._custom_trackers

                            if not (title and download_url):
                                continue
                            # seeders and leechers are presented diferently when doing a search and when looking for newly added
                            if mode == 'RSS':
                                # <![CDATA[
                                # Category: <a href="http://www.limetorrents.info/browse-torrents/TV-shows/">TV shows</a><br /> Seeds: 1<br />Leechers: 0<br />Size: 7.71 GB<br /><br /><a href="http://www.limetorrents.info/Owen-Hart-of-Gold-Djon91-torrent-7180661.html">More @ limetorrents.info</a><br />
                                # ]]>
                                description = item.find('description')
                                seeders = try_int(description('br')[0].next_sibling.strip().lstrip('Seeds: '))
                                leechers = try_int(description('br')[1].next_sibling.strip().lstrip('Leechers: '))
                            else:
                                # <description>Seeds: 6982 , Leechers 734</description>
                                description = item.find('description').text.partition(',')
                                seeders = try_int(description[0].lstrip('Seeds: ').strip())
                                leechers = try_int(description[2].lstrip('Leechers ').strip())

                            torrent_size = item.find('size').text

                            size = convert_size(torrent_size) or -1

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

                            # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                        if mode != 'RSS':
                            logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                        items.append(item)

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.log("Failed parsing provider. Traceback: {0!r}".format(traceback.format_exc()), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results


provider = LimeTorrentsProvider()
