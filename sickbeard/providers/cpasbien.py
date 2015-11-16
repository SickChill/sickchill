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
from sickbeard.providers import generic
from sickbeard.bs4_parser import BS4Parser


class CpasbienProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "Cpasbien")

        self.supportsBacklog = True
        self.public = True
        self.ratio = None
        self.url = "http://www.cpasbien.io"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = CpasbienCache(self)

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.url + '/recherche/'+search_string.replace('.', '-') + '.html'
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                data = self.getURL(searchURL)

                if not data:
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        lin = erlin = 0
                        resultdiv = []
                        while erlin == 0:
                            try:
                                classlin = 'ligne' + str(lin)
                                resultlin = html.findAll(attrs={'class' : [classlin]})
                                if resultlin:
                                    for ele in resultlin:
                                        resultdiv.append(ele)
                                    lin += 1
                                else:
                                    erlin = 1
                            except Exception:
                                erlin = 1

                        for row in resultdiv:
                            try:
                                link = row.find("a", title=True)
                                title = link.text.lower().strip()
                                pageURL = link['href']

                                # downloadTorrentLink = torrentSoup.find("a", title.startswith('Cliquer'))
                                tmp = pageURL.split('/')[-1].replace('.html', '.torrent')

                                downloadTorrentLink = ('http://www.cpasbien.io/telechargement/%s' % tmp)

                                if downloadTorrentLink:
                                    download_url = downloadTorrentLink
                                    # FIXME
                                    size = -1
                                    seeders = 1
                                    leechers = 0

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

class CpasbienCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        # search_strings = {'RSS': ['']}
        return {'entries': {}}

provider = CpasbienProvider()
