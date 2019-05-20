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

from __future__ import print_function, unicode_literals

import re

import validators

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Torrent9Provider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Torrent9")

        self.public = True
        self.minseed = None
        self.minleech = None
        self._original_url = "https://ww1.torrent9.nz/"
        # self._original_url = "https://www.torrents9.pw"
        self._custom_url = None
        self._used_url = None
        self._recheck_url = True

        self.proper_strings = ['PROPER', 'REPACK']
        self.cache = tvcache.TVCache(self)

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

    def _get_custom_url(self):
        return self._custom_url

    def _set_custom_url(self, url):
        if self._custom_url != url:
            self._custom_url = url
            self._recheck_url = True

    def _get_provider_url(self):
        if self._recheck_url:
            if self.custom_url:
                if validators.url(self.custom_url):
                    self._used_url = self.custom_url
                else:
                    logger.log("Invalid custom url set, please check your settings", logger.WARNING)

            self._used_url = self._original_url

        return self._used_url

    def _set_provider_url(self, url):
        self._used_url = url

    url = property(_get_provider_url, _set_provider_url)
    custom_url = property(_get_custom_url, _set_custom_url)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode == 'Season':
                    search_string = re.sub(r'(.*)S0?', r'\1Saison ', search_string)

                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                    search_url = self.url
                    post_data = {'torrentSearch': search_string}
                else:
                    search_url = self.url + '/torrents_series.html'
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
                            download_url = self._retrieve_dllink_from_url(self.url + tmp)
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(result.find(class_="seed_ok").get_text(strip=True))
                            leechers = try_int(result.find_all('td')[3].get_text(strip=True))
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            torrent_size = result.find_all('td')[1].get_text(strip=True)

                            units = ['o', 'Ko', 'Mo', 'Go', 'To', 'Po']
                            size = convert_size(torrent_size, units=units) or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = Torrent9Provider()
