# -*- coding: latin-1 -*-
# Author: Guillaume Serre <guillaume.serre@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import traceback

from sickbeard import logger
from sickbeard import tvcache
from sickrage.helper.common import try_int, convert_size
from sickbeard.bs4_parser import BS4Parser
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class CpasbienProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Cpasbien")

        self.public = True
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.url = "http://www.cpasbien.io"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = CpasbienCache(self)

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)
                    searchURL = self.url + '/recherche/' + search_string.replace('.', '-').replace(' ', '-') + '.html'
                else:
                    searchURL = self.url + '/view_cat.php?categorie=series&trie=date-d'

                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                data = self.get_url(searchURL)

                if not data:
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        line = 0
                        torrents = []
                        while True:
                            resultlin = html.findAll(class_='ligne%i' % line)
                            if not resultlin:
                                break

                            torrents += resultlin
                            line += 1

                        for torrent in torrents:
                            try:
                                title = torrent.find(class_="titre").get_text(strip=True).replace("HDTV", "HDTV x264-CPasBien")
                                tmp = torrent.find("a")['href'].split('/')[-1].replace('.html', '.torrent').strip()
                                download_url = (self.url + '/telechargement/%s' % tmp)
                                seeders = try_int(torrent.find(class_="up").get_text(strip=True))
                                leechers = try_int(torrent.find(class_="down").get_text(strip=True))
                                torrent_size = torrent.find(class_="poid").get_text()

                                size = convert_size(torrent_size) or -1
                            except (AttributeError, TypeError, KeyError, IndexError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio


class CpasbienCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}

provider = CpasbienProvider()
