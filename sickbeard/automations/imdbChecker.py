# Author: KontiSR
# URL: https://github.com/echel0n/SickRage
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

import urllib2, urllib
import shutil
import urlparse
import os, datetime
import requests
import cookielib
import re
from urllib2 import HTTPError, URLError

import sickbeard
from sickbeard import encodingKludge as ek
from sickbeard import logger
from sickbeard import helpers
from sickbeard import search_queue
from sickbeard.common import SKIPPED, WANTED
from lib.tvdb_api.tvdb_api import *

class ImdbBase():
    def _download(self, baseurl, querystring=""):
        fullurl = baseurl + urllib.urlencode(querystring)
        
        req = urllib2.Request(fullurl)
        try:
            response = urllib2.urlopen(req)
        except HTTPError as e:
            logger.log('Could not download IMDB watchlist', logger.DEBUG)
            #print 'Error code: ', e.code
            return False
        except URLError as e:
            logger.log('Could not download IMDB watchlist', logger.DEBUG)
            #print 'Reason: ', e.reason
            return False
        
        redirurl = response.geturl()
        htmlResponse = response.read()
        
        validHtml = True#BeautifulSoup(htmlResponse, 'html.parser')
        if validHtml:
            return htmlResponse
    
        return False


class IMDB(ImdbBase):
    listOfImdbIds = []
    def __init__(self):
        self.listOfImdbIds = []
    
    def run(self, force=False):
        try:
            # add shows from trakt.tv watchlist
            if sickbeard.USE_IMDBWATCHLIST:
                self.listOfImdbIds = []  # its about to all get re-added
                self.checkWatchlist() # Check the | separated watchlists (csv) urls
                if len(self.listOfImdbIds):
                    self.updateShowsInDb() # Update the db with possible new shows
                
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)
    
    def _getTTs(self, html):
        nrAddedTTs = 0
        ### Get the tt's (shows) from the ajax html. E.a. [ tt1958961|imdb|8.1|8.1|list, tt1958961|imdb|8.1|8.1|list ]
        if not html:
            return False
        
        parsedshows = re.findall("(tt[0-9]+)\\|imdb\\|([.0-9]+)", html)
        if not parsedshows:
            return False
        
        for show in parsedshows:
            if show[0] not in [x['imdbid'] for x in self.listOfImdbIds]:
                self.listOfImdbIds.append({"imdbid" : show[0], "score" : show[1]})
                nrAddedTTs += 1
        
        if nrAddedTTs > 0:
            return nrAddedTTs
        
        return False
    
    def checkWatchlist(self):
        
        ### Get imdbListId from the csv url's
        AjaxUrls = self._getImdbAjaxUrls(sickbeard.IMDB_WATCHLISTCSV)
        
        ### Get imdbUserId from the csv url's
        for url in AjaxUrls:
            getImdbHtml = self._download(url)
            nrAdded = self._getTTs(getImdbHtml)
        
        if self.listOfImdbIds:
            return self.listOfImdbIds
        
        return False
    
    '''
    Tries to use the csvUrls as a comma separated list of imdb csv urls, 
    to retrieve a userid and listid for each of the csv url.
    For each csv url an Ajax url is created. Thats used to get the list of Tvshows.
    '''
    def _getImdbAjaxUrls(self, csvUrls):
        ajaxUrls = []
        ajaxUrlBase = u"http://www.imdb.com/list/_ajax/list_filter?"
        
        reUserId = re.compile(".*(ur[0-9]+)")
        reListId = re.compile(".*(ls[0-9]+)")
        
        #if "|" in csvUrls:
            #print "Multiple Watchlists detected"
        csvurl = csvUrls.split("|")
        for url in csvurl:
            userIdMatch = reUserId.match(url)
            listIdMatch = reListId.match(url)
            
            if userIdMatch and listIdMatch:
                query = {"list_id" : listIdMatch.groups()[0], 
                     "list_class" : "WATCHLIST", 
                     "view" : "compact", 
                     "list_type" : "Titles", 
                     "filter" : '{"title_type":["tv_series"]}', 
                     "sort_field" : "created", 
                     "sort_direction" : "desc", 
                     "user_id" : userIdMatch.groups()[0] }
                ajaxUrls.append(ajaxUrlBase + urllib.urlencode(query))
        if ajaxUrls:
            return ajaxUrls          
                
        return False
    
    def updateShowsInDb(self):
        nrOfaddedShows = 0
        # Get list with thetvdb and imdbIds from DB (tt1234324)
        
        
        # Get thetvdb indexer_id, showname from tvdb using the IMDB id. ttxxxxx
        # Use "[{listOfImdbIds}]" for updating the db, if the show isn't in it
        tvdb_instance = Tvdb(cache = True, useZip = True)
        for watchlistShow in self.listOfImdbIds:
            if watchlistShow['imdbid'] not in [x.imdbid for x in sickbeard.showList ]:
                TvdbShow = tvdb_instance.search('',imdbid=watchlistShow['imdbid'])
                if TvdbShow:
                    self._addDefaultShow(1, TvdbShow['id'], TvdbShow['seriesname'], False)
                    nrOfaddedShows += 1

        return nrOfaddedShows if nrOfaddedShows > 0 else False
        
        return False
    
    
    def _addDefaultShow(self, indexer, indexer_id, name, status):
        """
        Adds a new show with the default settings
        """
        if not helpers.findCertainShow(sickbeard.showList, int(indexer_id)):
            logger.log(u"Adding show " + str(indexer_id))
            root_dirs = sickbeard.ROOT_DIRS.split('|')

            try:
                location = root_dirs[int(root_dirs[0]) + 1]
            except:
                location = None

            if location:
                showPath = ek.ek(os.path.join, location, helpers.sanitizeFileName(name))
                dir_exists = helpers.makeDir(showPath)
                if not dir_exists:
                    logger.log(u"Unable to create the folder " + showPath + ", can't add the show", logger.ERROR)
                    return
                else:
                    helpers.chmodAsParent(showPath)

                sickbeard.showQueueScheduler.action.addShow(int(indexer), int(indexer_id), showPath, status,
                                                            int(sickbeard.QUALITY_DEFAULT),
                                                            int(sickbeard.FLATTEN_FOLDERS_DEFAULT),
                                                            paused=False, anime = False)
            else:
                logger.log(u"There was an error creating the show, no root directory setting found", logger.ERROR)
                return

# imdbWatchlistTv = "http://www.imdb.com/user/%s/watchlist?ref_=wl_ref_typ&sort=list_order,asc&mode=simple&page=%s&title_type=tvSeries"
# imdbWatchlistTv2 = "http://www.imdb.com/list/export?list_id=ls009966268&author_id=ur35235230&ref_=wl_exp"
# imdbUserId = "ur5968686"
# imdbListId = "ls005547625"
# imdbWlPage = "1"
# ajaxUrlBase = u"http://www.imdb.com/list/_ajax/list_filter?"
# ajaxUrlQueryString = u"list_id=%s&list_class=WATCHLIST&view=compact&list_type=Titles&filter={\"title_type\":[\"tv_series\"]}&sort_field=created&sort_direction=desc&user_id=%s" % (imdbListId, imdbUserId)
# 
# query = {"list_id" : imdbListId, 
#          "list_class" : "WATCHLIST", 
#          "view" : "compact", 
#          "list_type" : "Titles", 
#          "filter" : '{"title_type":["tv_series"]}', 
#          "sort_field" : "created", 
#          "sort_direction" : "desc", 
#          "user_id" : imdbUserId }
# 
# imdbwatchlistcsv = "http://www.imdb.com/list/export?list_id=ls005547625&author_id=ur5968686&ref_=wl_exp"
# imdbWatchListTvFullURL = ajaxUrlBase + urllib.urlencode(query)
# # /download("%s%s" % (baseurl, searchurl), "test.csv")
# 
# IMDBobj = IMDB()
# 
# #Test one csv
# imdbIds = IMDBobj.checkWatchlist(imdbwatchlistcsv)
# print IMDBobj.listOfImdbIds
# 
# # Test two csv's
# imdbIds = IMDBobj.checkWatchlist(imdbwatchlistcsv + "|" + imdbWatchlistTv2)
# print IMDBobj.listOfImdbIds
# 
# print imdbIds

