# -*- coding: latin-1 -*-
# Author: raver2046 <raver2046@gmail.com> from djoole <bobby.djoole@gmail.com>  
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import traceback
import re
import datetime
import time
from requests.auth import AuthBase
import sickbeard
import generic
import urllib
import requests
from requests import exceptions
from sickbeard.bs4_parser import BS4Parser
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard import helpers
from sickbeard import classes
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName
from sickbeard.exceptions import ex


class FNTProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "FNT")

        self.supportsBacklog = True
        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None        
        self.minseed = None
        self.minleech = None

        self.cache = FNTCache(self)

        self.urls = {'base_url': 'https://fnt.nu',
                     'search': 'https://www.fnt.nu/torrents/recherche/?afficher=1&recherche=%s%s',
                     'login': 'https://fnt.nu/account-login.php',
                     'download': 'https://fnt.nu/download.php?id=%s&dl=oui',
        }

        self.url = self.urls['base_url']
        self.categories = "&afficher=1&c118=1&c129=1&c119=1&c120=1&c121=1&c126=1&c137=1&c138=1&c146=1&c122=1&c110=1&c109=1&c135=1&c148=1&c153=1&c149=1&c150=1&c154=1&c155=1&c156=1&c114=1&visible=1&freeleech=0&nuke=1&3D=0&sort=size&order=desc"

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'FNT.png'

    def getQuality(self, item, anime=False):
        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _doLogin(self):      


        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                            'password': self.password,
                            'submit' : 'Se loguer'
        }

        if not self.session:
            self.session = requests.Session()

        logger.log('Performing authentication to FNT', logger.DEBUG)
        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
            return False

        if re.search('/account-logout.php', response.text):
            logger.log(u'Login to ' + self.name + ' was successful.', logger.DEBUG)
            return True                
        else:
            logger.log(u'Login to ' + self.name + ' was unsuccessful.', logger.DEBUG)                
            return False

        return True

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + '.' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + '.' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + '.S%02d' % int(ep_obj.scene_season)  # 1) showName.SXX

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) + '.' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string

                search_string['Episode'].append(re.sub('\s+', '.', ep_string))

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        logger.log(u"_doSearch started with ..." + str(search_params), logger.DEBUG)

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            
		
            for search_string in search_params[mode]:

                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                
                searchURL = self.urls['search'] % (urllib.quote(search_string), self.categories)

                logger.log(u"Search string: " + searchURL, logger.DEBUG)
                   
                
                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        result_table = html.find('table', {'id': 'tablealign3bis'})
        
                        if not result_table:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.DEBUG)
                            continue
                        
                        if result_table:
                            rows = result_table.findAll("tr" , {"class" : "ligntorrent"} )
        
                            for row in rows:
                                link = row.findAll('td')[1].find("a" , href=re.compile("fiche_film") )                                                         
                                  
                                if link:               
                                   
                                   try:                                                                       
                                      title = link.text
                                      logger.log(u"FNT TITLE : " + title, logger.DEBUG)                                                                                               
                                      download_url = self.urls['base_url'] + "/" + row.find("a",href=re.compile("download\.php"))['href']                                                                     
                                   except (AttributeError, TypeError):
                                      continue

                                   if not title or not download_url:
                                      continue
                                      
                                   try:                                       
                                      id = download_url.replace(self.urls['base_url'] + "/" + 'download.php?id=', '').replace('&amp;dl=oui', '').replace('&dl=oui', '')    
                                      logger.log(u"FNT id du torrent  " + str(id), logger.DEBUG)            
                                      defailseedleech = link['mtcontent']                                                                                                                
                                      seeders =  int(defailseedleech.split("<font color='#00b72e'>")[1].split("</font>")[0]) 
                                      logger.log(u"FNT seeders :  " + str(seeders), logger.DEBUG)
                                      leechers = int(defailseedleech.split("<font color='red'>")[1].split("</font>")[0]) 
                                      logger.log(u"FNT leechers :  " + str(leechers), logger.DEBUG)                                                                                                     
                                   except:
                                      logger.log(u"Unable to parse torrent id & seeders leechers  " + self.name + " Traceback: " + traceback.format_exc(), logger.DEBUG)
                                      continue
                                   
                                   #Filter unseeded torrent
                                   if mode != 'RSS' and (seeders < self.minseed or leechers < self.minleech):
                                      continue
                                 
                                   item = title, download_url , id, seeders, leechers
                                   logger.log(u"Found result: " + title.replace(' ','.') + " (" + download_url + ")", logger.DEBUG)

                                   items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(), logger.ERROR)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):
        
        title, url, id, seeders, leechers = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = str(url).replace('&amp;', '&')

        return title, url

    def findPropers(self, search_date=datetime.datetime.today()):

        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
            ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
            ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
            ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
            ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
        )

        if not sqlResults:
            return []

        for sqlshow in sqlResults:
            self.show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if self.show:
                curEp = self.show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))
                searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

                for item in self._doSearch(searchString[0]):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio


class FNTAuth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        return r


class FNTCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # Only poll FNT every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = FNTProvider()
