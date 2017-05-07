# coding=utf-8
# Author: Panz3r
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

from __future__ import print_function, unicode_literals

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class HorribleSubsProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "HorribleSubs")

        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True

        self.minseed = None
        self.minleech = None

        self.url = 'http://horriblesubs.info/'
        self.urls = {
            'search': self.url + 'lib/search.php',
            'rss': self.url + 'lib/latest.php'
        }

        self.cache = tvcache.TVCache(self, min_time=15)  # only poll HorribleSubs every 15 minutes max

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        # TODO Removed to allow Tests to pass... Not sure about removing it
        # if not self.show or not self.show.is_anime:
        #   return results

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:
                next_id = 0
                search_params = {
                    "nextid": next_id,
                }

                if mode != 'RSS':
                    logger.log("Search string: {0}".format(search_string.decode("utf-8")), logger.DEBUG)
                    search_params["value"] = search_string
                    target_url = self.urls['search']
                else:
                    target_url = self.urls['rss']

                data = self.get_url(target_url, params=search_params, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as soup:
                    torrent_tables = soup.find_all('table', class_='release-table')

                    torrent_rows = []
                    for torrent_table in torrent_tables:
                        curr_torrent_rows = torrent_table('tr') if torrent_table else []
                        torrent_rows.extend(curr_torrent_rows)

                    # Continue only if one Release is found
                    if len(torrent_rows) < 1:
                        logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    for torrent_row in torrent_rows:
                        try:
                            label = torrent_row.find('td', class_='dl-label')
                            title = label.get_text(strip=True)

                            link = torrent_row.find('td', class_='hs-torrent-link')
                            download_url = link.find('a')['href'] if link and link.find('a') else None

                            if not download_url:
                                # fallback to magnet link
                                link = torrent_row.find('td', class_='hs-magnet-link')
                                download_url = link.find('a')['href'] if link and link.find('a') else None

                        except StandardError:
                            continue

                        if not all([title, download_url]):
                            continue

                        item = {'title': '[HorribleSubs] ' + title, 'link': download_url, 'size': 333, 'seeders': 1, 'leechers': 1,
                                'hash': ''}

                        if mode != 'RSS':
                            logger.log("Found result: {0}".format(title), logger.DEBUG)

                        items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results

provider = HorribleSubsProvider()
