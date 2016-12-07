# coding=utf-8
# Author: Ludovic Reenaers <ludovic.reenaers@gmail.com>
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

from __future__ import unicode_literals

import re

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class Torrent9Provider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Torrent9")

        self.public = True
        self.minseed = None
        self.minleech = None
        self.url = "http://www.torrent9.biz"

        self.proper_strings = ['PROPER', 'REPACK']
        self.cache = tvcache.TVCache(self)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                    search_url = self.url + '/search_torrent/' + search_string.replace('.', '-').replace(' ', '-') + '.html,trie-seeds-d'
                else:
                    search_url = self.url + '/torrents_series.html,trie-date-d'

                data = self.get_url(search_url, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_rows = html.tr
                    for result in torrent_rows:
                        try:
                            title = result.find('a').get_text(strip=True).replace("HDTV", "HDTV x264-Torrent9")
                            title = re.sub(r' Saison', ' Season', title, flags=re.I)
                            tmp = result.find("a")['href'].split('/')[-1].replace('.html', '.torrent').strip()
                            download_url = (self.url + '/get_torrent/{0}'.format(tmp))
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(result.find(class_="seed_ok").get_text(strip=True))
                            leechers = try_int(result.find_all('td')[3].get_text(strip=True))
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            torrent_size = result.find_all('td')[1].get_text(strip=True)

                            units = ['o', 'Ko', 'Mo', 'Go', 'To', 'Po']
                            size = convert_size(torrent_size, units=units) or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.log(u"Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                            items.append(item)
                        except StandardError:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = Torrent9Provider()
