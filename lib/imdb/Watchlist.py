"""
Person module (imdb package).

This module provides the Person class, used to store information about
a given person.

Copyright 2004-2010 Davide Alberani <da@erlug.linux.it>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import re
import requests
import sickbeard
from sickbeard import helpers, logger, db
from sickbeard import encodingKludge as ek
import os
import traceback
import datetime
import json
from lib.imdb._exceptions import IMDbError
from lib.libtrakt import TraktAPI
from lib.libtrakt.exceptions import TraktException
'''
'''
class WatchlistItem():
    def __init__(self,imdbid,indexer=1,indexer_id=None,watchlist_id=None,show_id=None,score=None,title=None):
        self.imdbid = imdbid
        self.indexer = indexer
        self.indexer_id = indexer_id
        self.watchlist_id = watchlist_id
        self.show_id = show_id
        self.score = score
        self.title = title
        
    def addDefaults(self):
        """
        Adds a new show with the default settings
        """
        if not helpers.findCertainShow(sickbeard.showList, int(self.indexer_id)):
            logger.log(u"Adding show " + str(self.indexer_id))
            root_dirs = sickbeard.ROOT_DIRS.split('|')

            try:
                root_dir_index = sickbeard.IMDB_WL_ROOT_DIR_DEFAULT -1 if sickbeard.IMDB_WL_USE_CUSTOM_DEFAULTS and sickbeard.IMDB_WL_ROOT_DIR_DEFAULT else 0
                location = root_dirs[int(root_dirs[root_dir_index]) + 1]
            except:
                location = None

            if location:
                showPath = ek.ek(os.path.join, location, helpers.sanitizeFileName(self.title))
                dir_exists = helpers.makeDir(showPath)
                if not dir_exists:
                    logger.log(u"Unable to create the folder " + showPath + ", can't add the show", logger.ERROR)
                    return
                else:
                    helpers.chmodAsParent(showPath)
                
                # Set defaults
                quality = int(sickbeard.QUALITY_DEFAULT)
                status = int(sickbeard.STATUS_DEFAULT)
                wanted_begin = int(sickbeard.WANTED_BEGIN_DEFAULT)
                wanted_latest = int(sickbeard.WANTED_LATEST_DEFAULT)
                flatten_folders = int(sickbeard.FLATTEN_FOLDERS_DEFAULT)
                subtitles = int(sickbeard.SUBTITLES_DEFAULT)
                anime = int(sickbeard.ANIME_DEFAULT)
                indexer = sickbeard.INDEXER_DEFAULT
                
                if sickbeard.IMDB_WL_USE_CUSTOM_DEFAULTS:
                    quality = int(sickbeard.IMDB_WL_QUALITY_DEFAULT)
                    status = int(sickbeard.IMDB_WL_STATUS_DEFAULT)
                    wanted_begin = int(sickbeard.IMDB_WL_WANTED_BEGIN_DEFAULT)
                    wanted_latest = int(sickbeard.IMDB_WL_WANTED_LATEST_DEFAULT)
                    flatten_folders = int(sickbeard.IMDB_WL_FLATTEN_FOLDERS_DEFAULT)
                    subtitles = int(sickbeard.IMDB_WL_SUBTITLES_DEFAULT)
                    indexer = 1 #int(sickbeard.IMDB_WL_INDEXER_DEFAULT) # fixed to tvdb for now
                    #IMDB_WL_INDEXER_TIMEOUT = None
                    #IMDB_WL_SCENE_DEFAULT = False
                    anime = sickbeard.IMDB_WL_ANIME_DEFAULT
                    #IMDB_WL_USE_IMDB_INFO = True

                
                sickbeard.showQueueScheduler.action.addShow(int(indexer), int(self.indexer_id), showPath, status,
                                                            quality, flatten_folders, wanted_begin=wanted_begin, 
                                                            wanted_latest=wanted_latest, 
                                                            subtitles=subtitles, anime=anime)
            else:
                logger.log(u"There was an error creating the show, no root directory setting found", logger.ERROR)
                return
            
    def getIdFromTrakt(self):
        try:
            search_id = re.search(r'(?m)((?:tt\d{4,})|^\d{4,}$)', self.imdbid).group(1)
            
            url = '/search?id_type=%s&id=%s' % (('tvdb', 'imdb')['tt' in search_id], search_id)
            filtered = []
            try:
                resp = TraktAPI(timeout=sickbeard.TRAKT_TIMEOUT).trakt_request(url)
                if len(resp):
                    filtered = resp
            except TraktException as e:
                logger.log(u'Could not connect to Trakt service: %s' % ex(e), logger.WARNING)
            
            # Use first returend show. Sometimes a single IMDB id can have multiple tvdb id's. Like for example with Star trek: renagades
            for result in resp:
                if result['type'] == "show":
                    self.title = result['show']['title']
                    self.indexer_id = result['show']['ids']['tvdb']
                    # As where default setting the tvdb indexer_id, might as well keep it static for now.
                    self.indexer = 1
                    return True

        except Exception, e:
            logger.log(u"Could not get TVDBid from Trakt using id_type imdb", logger.WARNING)
            return False
    
class IMDBWatchlistApi(object):
    def __init__(self, timeout=None):
        self.session = requests.Session()
        #self.verify = ssl_verify and sickbeard.TRAKT_VERIFY and certifi.where()
        self.timeout = timeout or sickbeard.IMDB_WL_TIMEOUT
        self.headers = {
            'Content-Type': 'application/json',
        }
        self.WATCHLIST_URL = u"http://www.imdb.com/list/_ajax/list_filter?"
        
    def watchlist_request(self, data=None, headers=None, url=None, method='GET', count=0, conttype='application/json', params=None):
        if not url:
            url = self.WATCHLIST_URL
        
        try:
            resp = self.session.request(method, url, headers=self.headers, timeout=self.timeout,
                                        params=params if params else [], verify=False)
            
            # check for http errors and raise if any are present
            resp.raise_for_status()
            
            if conttype == 'application/json':
                resp = resp.json()
        except requests.RequestException as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                if 'timed out' in e:
                    logger.log(u'Timeout connecting to Trakt. Try to increase timeout value in Trakt settings', logger.WARNING)                      
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all                    
                else:
                    logger.log(u'Could not connect to Trakt. Error: {0}'.format(e), logger.WARNING)                
            elif 502 == code:
                # Retry the request, Cloudflare had a proxying issue
                logger.log(u'Retrying api request url: %s' % url, logger.WARNING)
                return self.trakt_request(data, headers, url, method, count=count)
            elif code in (500, 501, 503, 504, 520, 521, 522):
                # http://docs.trakt.apiary.io/#introduction/status-codes
                logger.log(u'Trakt may have some issues and it\'s unavailable. Try again later please', logger.WARNING)
            elif 404 == code:
                logger.log(u'Trakt error (404) the resource does not exist: %s' % url, logger.WARNING)
            else:
                logger.log(u'Could not connect to Trakt. Code error: {0}'.format(code), logger.ERROR)
            return {}
        
        # check and confirm Imdb call did not fail
        if isinstance(resp, dict) and 'failure' == resp.get('status', None):
            if 'message' in resp:
                raise IMDbError(resp['message'])
            if 'error' in resp:
                raise IMDbError(resp['error'])
            else:
                raise IMDbError('Unknown Error')

        return resp

class WatchlistParser(IMDBWatchlistApi):
    def __init__(self):
        super(WatchlistParser, self).__init__()
        self.watchlist_items = []
    
    #Helper
    def parse(self, html):
        ### Get the tt's (shows) from the ajax html. E.a. [ tt1958961|imdb|8.1|8.1|list, tt1958961|imdb|8.1|8.1|list ]
        if not html or not html.has_key('table_data') or not int(html['num_results']):
            return False
        
        shows = re.findall("(tt[0-9]+)\\|imdb\\|([.0-9]+)", html['table_data'])
        if shows:
            return shows
        
        return False
    
    def getShowsFromWatchlist(self, watchlist=None):
        
        shows = []
        
        if watchlist:
            # Get the query data used for constructing the watchlist ajax url
            query_data = self.convertUrlData(watchlist)
            
            # Perform the ajax request for the watchlist
            html = self.watchlist_request(params=query_data)
            
            #Extract all imdb_id's
            shows = self.parse(html)
            
            # Move through the imdb_ids and create WatchlistItem objects for them
            # Don't konw why i'm keeping the scores. Maybe comes of use some day.
            for show in shows:
                if show[0] not in [x.imdbid for x in self.watchlist_items]:
                    self.watchlist_items.append(WatchlistItem(show[0],score=show[1],watchlist_id=index))
        
        # Automatic add this show with default show options
        # Let's disable this for now.
        if None:
            for item in self.watchlist_items:
                if not item.getIdFromTrakt():
                    logger.log("Could not enrich, adding to db without indexer_id", logger.WARNING)
                else:
                    item.addDefaults()

        return self.watchlist_items
    
    def getShowsFromEnabledWatchlists(self):
        
        shows = []
        
        ### Get the configured imdb watchlist urls
        watchlists = sickbeard.IMDB_WL_USE_IDS.split('|')
        
        ### We're only intrested in enabled watchlists
        watchlists_enabled = sickbeard.IMDB_WL_IDS_ENABLED.split('|')
        
        if len(watchlists) == len(watchlists_enabled):
            # Start looping through the imdb watchlist urls
            for index, watchlist in enumerate(watchlists):
                if not int(watchlists_enabled[index]):
                    continue
                
                self.getShowsFromWatchlist(watchlist)
        
        # Automatic add this show with default show options
        # Let's disable this for now.
        if None:
            for item in self.watchlist_items:
                if not item.getIdFromTrakt():
                    logger.log("Could not enrich, adding to db without indexer_id", logger.WARNING)
                else:
                    item.addDefaults()

        return self.watchlist_items
    
    '''
    Tries to use the csvUrls as a comma separated list of imdb csv urls, 
    to retrieve a userid and listid for each of the csv url.
    For each csv url an Ajax url is created. Thats used to get the list of Tvshows.
    '''
    def convertUrlData(self, watchlist_url):
        ajaxUrls = []
        ajaxUrlBase = u"http://www.imdb.com/list/_ajax/list_filter?"
        
        re_user_id = re.compile(".*(ur[0-9]+)")
        user_id_match = re_user_id.match(watchlist_url)
        if user_id_match:
            user_id = user_id_match.group(1)
            
        #reListId = re.compile(".*(ls[0-9]+)")
        main_watchlist_id = self.getListIds(user_id)[0]
        
        if user_id_match and main_watchlist_id:
            query = {"list_id" : main_watchlist_id,
                 "list_class" : "WATCHLIST", 
                 "view" : "compact", 
                 "list_type" : "Titles", 
                 "filter" : '{"title_type":["tv_series"]}', 
                 "sort_field" : "created", 
                 "sort_direction" : "desc", 
                 "user_id" : user_id}
            return query  
                
        return False
    
    def getListIds(self, user_id):
        URL_WATCHLIST = "http://www.imdb.com/user/%s/watchlist?ref_=wt_nv_wl_all_0"
        watchlist_page = self.watchlist_request(url=URL_WATCHLIST % user_id, conttype=None)
        
        list_ids = []
        
        # Retrieve the Main Watchlist list id's
        # user_id should be parsed as: ur59344686
        re_main_watchlist = re.compile("(ls[0-9]+)&author_id=%s" % (user_id))
        main_watchlist_id = re_main_watchlist.search(watchlist_page.text)
        
        # Retrieve the any secondary list id's
        re_secondary_list_ids = re.compile(".*<strong><a.href=./list/(ls[0-9]+)\?")
        secondary_list_ids = re_secondary_list_ids.findall(watchlist_page.text)
        
        # A user should always have a primary whatchlist
        if not main_watchlist_id:
            return False
        
        list_ids.append(main_watchlist_id.group(1))
        
        # Let's search of addintional watchlists
        for listid in secondary_list_ids:
            list_ids.append(listid)
            
        return list_ids