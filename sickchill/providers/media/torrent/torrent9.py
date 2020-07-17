# coding=utf-8
# Author: Ludovic Reenaers <ludovic.reenaers@gmail.com>
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
# Stdlib Imports
import re

# Third Party Imports
import validators
from requests.compat import urljoin

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.media.torrent import TorrentProvider


class Torrent9Provider(TorrentProvider):

    def __init__(self):

        super().__init__('Torrent9', extra_options=tuple([]))

        self.url = "https://www.torrent9.ac/"

        self.proper_strings = ['PROPER', 'REPACK']

    def search(self, search_strings, ep_obj=None) -> list:
        results = []
        for mode in search_strings:
            items = []
            logger.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if mode == 'Season':
                    search_string = re.sub(r'(.*)S0?', r'\1Saison ', search_string)

                search_url = self.url
                if self.config('custom_url'):
                    if not validators.url(self.config('custom_url')):
                        logger.warning("Invalid custom url set, please check your settings")
                        return results
                    search_url = self.config('custom_url')

                if mode != 'RSS':
                    logger.debug("Search string: {0}".format(search_string))
                    post_data = {'torrentSearch': search_string}
                else:
                    search_url += '/torrents_series.html'
                    post_data = None

                data = self.get_url(search_url, post_data, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('div', {'class': 'table-responsive'})
                    if torrent_table:
                        torrent_rows = torrent_table.findAll('tr')
                    else:
                        torrent_rows = None

                    if not torrent_rows:
                        continue
                    for result in torrent_rows:
                        try:
                            title = result.find('a').get_text(strip=False).replace("HDTV", "HDTV x264-Torrent9")
                            title = re.sub(r' Saison', ' Season', title, flags=re.I)
                            tmp = result.find("a")['href']
                            download_url = urljoin(self.url, self._retrieve_dllink_from_url(urljoin(self.url, tmp)))
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(result.find(class_="seed_ok").get_text(strip=True))
                            leechers = try_int(result.find_all('td')[3].get_text(strip=True))
                            if seeders < self.config('minseed') or leechers < self.config('minleech'):
                                if mode != 'RSS':
                                    logger.debug("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers))
                                continue

                            torrent_size = result.find_all('td')[1].get_text(strip=True)

                            units = ['o', 'Ko', 'Mo', 'Go', 'To', 'Po']
                            size = convert_size(torrent_size, units=units) or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)
                        except Exception:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results

    def _retrieve_dllink_from_url(self, inner_url, _type="torrent"):
        data = self.get_url(inner_url, returns='text')
        res = {
            "torrent": "",
            "magnet": "",
        }
        with BS4Parser(data, 'html5lib') as html:
            download_btns = html.findAll("div", {"class": "download-btn"})
            for btn in download_btns:
                link = btn.find('a')["href"]
                if link.startswith("magnet"):
                    res["magnet"] = link
                else:
                    res["torrent"] = link
        return res[_type]



