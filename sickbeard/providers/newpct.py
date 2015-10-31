# Author: CristianBB
# Greetings to Mr. Pine-apple
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.common import USER_AGENT
from sickbeard.bs4_parser import BS4Parser
from sickbeard import scene_exceptions


class newpctProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "Newpct_(Spanish)")

        self.search_mode_eponly = True 
        self.supportsBacklog = True
        self.onlyspasearch = None
        self.append_identifier = None
        self.cache = newpctCache(self)

        self.urls = {
            'base_url': 'http://www.newpct.com',
            'search': 'http://www.newpct.com/buscar-descargas/'
        }

        self.url = self.urls['base_url']
        self.headers.update({'User-Agent': USER_AGENT})

        """
        Search query: 
        http://www.newpct.com/buscar-descargas/cID=0&tLang=0&oBy=0&oMode=0&category_=767&subcategory_=All&idioma_=1&calidad_=All&oByAux=0&oModeAux=0&size_=0&btnb=Filtrar+Busqueda&q=the+strain
        
        category_=767 => Category Shows
        idioma_=1 => Language Spanish
        calidad_=All=> Quality ALL
        q => Search show
        """
        
        self.search_params = {
            'cID': 0,
            'tLang': 0,
            'oBy': 0,
            'oMode': 0,
            'category_': 767,
            'subcategory_': 'All',
            'idioma_': 1,
            'calidad_': 'All',
            'oByAux': 0,
            'oModeAux': 0,
            'size_': 0,
            'btnb': 'Filtrar+Busqueda',
            'q': ''
        }

        
    def isEnabled(self):
        return self.enabled
    
    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}
        
        if epObj != None:
            lang_info = epObj.show.lang 
        else:
            lang_info = ''
            
        #Only search if user conditions are true
        if (self.onlyspasearch and lang_info == 'es') or ( not self.onlyspasearch ):
            
            for mode in search_strings.keys():
                logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
                
                for search_string in search_strings[mode]:
                    self.search_params.update({'q': search_string.strip()})
    
                    logger.log(u"Search string: " + search_string, logger.DEBUG)
                    
                    searchURL = self.urls['search']
                    logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                    logger.log(u"Params: %s" %self.search_params, logger.DEBUG)
                    
                    data = self.getURL(searchURL, post_data=self.search_params, timeout=30)
                    if not data:
                        continue
            
                    try:
                        with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                            torrent_tbody = html.find('tbody')
                            
                            if len(torrent_tbody) < 1:
                                logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                                continue
                                
                            torrent_table = torrent_tbody.findAll('tr')
                            num_results = len(torrent_table) - 1                              
                            
                            iteration = 0
                            for row in torrent_table:
                                try:
                                    if iteration < num_results:
                                        torrent_row = row.findAll('a')[1]
                                             
                                        download_url = torrent_row.get('href')
                                        title_raw = torrent_row.get('title')
                                        
                                        title = self._processTittle(title_raw)
                                        
                                        item = title, download_url
                                        logger.log(u"Found result: %s " % title, logger.DEBUG)
        
                                        items[mode].append(item)
                                        iteration += 1
                                    
                                except (AttributeError, TypeError):
                                    continue
                        
                    except Exception:
                        logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.WARNING)
    
                results += items[mode]
        else:
            logger.log(u"Show info is not spanish, skipping provider search", logger.DEBUG)
        
        return results

    def _processTittle(self, title):
        
        title = title.replace('Descargar ', '')
        
        #Show title
        show_name = title[0:title.find(' - ')]
        
        #episode numbers in format 212 (season 2, ep. number 12)
        ini_str = title.find('[Cap.') + 5
        end_str = title.find(']', ini_str)
        
        ini_epnumber = end_str - 2
        end_epnumber = end_str 
        epnumber = title[ini_epnumber:end_epnumber]
        
        ini_season = ini_str
        end_season = ini_epnumber
        season = title[ini_season:end_season]
        
        #Quality
        if title.find('[HDTV 1080p]') > 0:
            quality = '1080p HDTV x264'
        elif title.find('HDTV') > 0:
            quality = '720p HDTV x264'
        elif title.find('DVD') > 0 or title.find('BDrip') > 0:
            quality = 'HDTV'
        else:
            quality = 'Unknown'
                    
        title = show_name + ' - ' + season + 'x' + epnumber + ' (' + quality + ') ' + self.append_identifier
               
        return title 



class newpctCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 30
        


provider = newpctProvider()
