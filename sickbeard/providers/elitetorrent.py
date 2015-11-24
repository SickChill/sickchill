# coding=utf-8
# Author: CristianBB
#
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import traceback
import re
from six.moves import urllib

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.bs4_parser import BS4Parser


class elitetorrentProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "EliteTorrent")

        self.supportsBacklog = True
        self.onlyspasearch = None
        self.minseed = None
        self.minleech = None
        self.cache = elitetorrentCache(self)

        self.urls = {
            'base_url': 'http://www.elitetorrent.net',
            'search': 'http://www.elitetorrent.net/torrents.php'
        }

        self.url = self.urls['base_url']

        """
        Search query:
        http://www.elitetorrent.net/torrents.php?cat=4&modo=listado&orden=fecha&pag=1&buscar=fringe
        
        cat = 4 => Shows
        modo = listado => display results mode
        orden = fecha => order
        buscar => Search show
        pag = 1 => page number
        """

        self.search_params = {
            'cat': 4,
            'modo': 'listado',
            'orden': 'fecha',
            'pag': 1,
            'buscar': ''

        }
        
    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        lang_info = '' if not epObj or not epObj.show else epObj.show.lang
        
        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            
            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != 'es' and mode is not 'RSS':
                logger.log(u"Show info is not spanish, skipping provider search", logger.DEBUG)
                continue

            for search_string in search_strings[mode]:
                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)
                
                search_string = re.sub(r'S0*(\d*)E(\d*)', r'\1x\2', search_string)
                self.search_params['buscar'] = search_string.strip() if mode is not 'RSS' else ''
                
                searchURL = self.urls['search'] + '?' + urllib.parse.urlencode(self.search_params)
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                
                data = self.getURL(searchURL, timeout=30)
                
                if not data:
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        torrent_table = html.find('table', class_='fichas-listado')

                        if torrent_table is None:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrent_rows = torrent_table.findAll('tr')
                        if torrent_rows is None:
                            logger.log(u"Torrent table does not have any rows", logger.DEBUG)
                            continue

                        for row in torrent_rows[1:]:
                            try:
                                seeders_raw = row.find('td', class_='semillas').text
                                leechers_raw = row.find('td', class_='clientes').text 

                                download_url = self.urls['base_url'] + row.findAll('a')[0].get('href', '')
                                title = self._processTitle(row.findAll('a')[1].text)
                                seeders = seeders_raw if seeders_raw.isnumeric() else 0
                                leechers = leechers_raw if leechers_raw.isnumeric() else 0
                                                                
                                # FIXME: Provider does not provide size
                                size = 0

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode is not 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.WARNING)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

   
    @staticmethod
    def _processTitle(title):

        # Quality, if no literal is defined it's HDTV
        if 'calidad' not in title:
            title += ' [720p HDTV x264]'
            
        title = title.replace('(Buena calidad)', '[720p HDTV x264]')
        title = title.replace('(Alta calidad)', '[720p HDTV x264]')
        title = title.replace('(calidad regular)', '[DVDrip x264]')
        title = title.replace('(calidad media)', '[DVDrip x264]')
                    
        #Language, all results from this provider have spanish audio, we append it to title (avoid to download undesired torrents)
        title += ' [Spanish Audio]'
        
        return title.strip()


class elitetorrentCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = elitetorrentProvider()