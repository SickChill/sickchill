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
import re

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.providers.TorrentProvider import TorrentProvider


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

    def search(self, search_params, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)
                if mode != 'RSS':
                    searchURL = self.url + '/recherche/' + search_string.replace('.', '-') + '.html'
                else:
                    searchURL = self.url + '/view_cat.php?categorie=series'

                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                data = self.get_url(searchURL)

                if not data:
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        lin = erlin = 0
                        resultdiv = []
                        while erlin == 0:
                            try:
                                classlin = 'ligne' + str(lin)
                                resultlin = html.findAll(attrs={'class': [classlin]})
                                if resultlin:
                                    for ele in resultlin:
                                        resultdiv.append(ele)
                                    lin += 1
                                else:
                                    erlin = 1
                            except Exception:
                                erlin = 1

                        for torrent in resultdiv:
                            try:
                                title = torrent.findAll(attrs={'class': ["titre"]})[0].text.replace("HDTV", "HDTV x264-CPasBien")
                                detail_url = torrent.find("a")['href']
                                tmp = detail_url.split('/')[-1].replace('.html', '.torrent')
                                download_url = (self.url + '/telechargement/%s' % tmp)
                                torrent_size = (str(torrent.findAll(attrs={'class': ["poid"]})[0].text).rstrip('&nbsp;')).rstrip()
                                size = -1
                                if re.match(r"\d+([,\.]\d+)?\s*[KkMmGgTt]?[Oo]", torrent_size):
                                    size = self._convertSize(torrent_size.rstrip())
                                seeders = torrent.findAll(attrs={'class': ["seed_ok"]})[0].text
                                leechers = torrent.findAll(attrs={'class': ["down"]})[0].text

                            except (AttributeError, TypeError):
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

    def _convertSize(self, sizeString):
        size = sizeString[:-2].strip()
        modifier = sizeString[-2:].upper()
        try:
            size = float(size)
            if modifier in 'KO':
                size *= 1024 ** 1
            elif modifier in 'MO':
                size *= 1024 ** 2
            elif modifier in 'GO':
                size *= 1024 ** 3
            elif modifier in 'TO':
                size *= 1024 ** 4
        except Exception:
            size = -1
        return long(size)


class CpasbienCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}

provider = CpasbienProvider()
