# coding=utf-8
# Author: Guillaume Serre <guillaume.serre@gmail.com>
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

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.media.torrent import TorrentProvider


class CpasbienProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Cpasbien")

        self.url = "http://www.cpasbien.cx"

        self.proper_strings = ['PROPER', 'REPACK']
        self.cache = tvcache.TVCache(self)
        self.ability_status = self.PROVIDER_BACKLOG
        self.supported_options = ('public', 'minseed', 'minleech')

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:
            items = []
            logger.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:

                if mode == 'Season':
                    search_string = re.sub(r'(.*)S0?', r'\1Saison ', search_string)

                if mode != 'RSS':
                    logger.debug("Search string: {0}".format
                               (search_string))

                    search_url = self.url + '/recherche/' + search_string.replace('.', '-').replace(' ', '-') + '.html,trie-seeds-d'
                else:
                    search_url = self.url + '/view_cat.php?categorie=series&trie=date-d'

                data = self.get_url(search_url, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_rows = html(class_=re.compile('ligne[01]'))
                    for result in torrent_rows:
                        try:
                            title = result.find(class_="titre").get_text(strip=True).replace("HDTV", "HDTV x264-CPasBien")
                            title = re.sub(r' Saison', ' Season', title, flags=re.I)
                            tmp = result.find("a")['href'].split('/')[-1].replace('.html', '.torrent').strip()
                            download_url = (self.url + '/telechargement/{0}'.format(tmp))
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(result.find(class_="up").get_text(strip=True))
                            leechers = try_int(result.find(class_="down").get_text(strip=True))
                            if seeders < self.config('minseed') or leechers < self.config('minleech'):
                                if mode != 'RSS':
                                    logger.debug("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers))
                                continue

                            torrent_size = result.find(class_="poid").get_text(strip=True)

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



