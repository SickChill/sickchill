# coding=utf-8
# Author: djoole <bobby.djoole@gmail.com>
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

from requests.auth import AuthBase
import time
import traceback

from sickbeard import logger, tvcache
from sickbeard.common import USER_AGENT
from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class T411Provider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "T411")

        self.username = None
        self.password = None
        self.ratio = None
        self.token = None
        self.tokenLastUpdate = None

        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll T411 every 10 minutes max

        self.urls = {'base_url': 'http://www.t411.in/',
                     'search': 'https://api.t411.in/torrents/search/%s?cid=%s&offset=0&limit=100',
                     'rss': 'https://api.t411.in/torrents/top/today',
                     'login_page': 'https://api.t411.in/auth',
                     'download': 'https://api.t411.in/torrents/download/%s',
                     'terms_tree': 'https://api.t411.in/terms/tree'}

        self.url = self.urls['base_url']

        self.headers.update({'User-Agent': USER_AGENT})

        self.subcategories = [433, 637, 455, 639]
        
        self.apiTermsTree = None

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

    def login(self):

        if self.token is not None:
            if time.time() < (self.tokenLastUpdate + 30 * 60):
                return True

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.get_url(self.urls['login_page'], post_data=login_params, timeout=30, json=True)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if response and 'token' in response:
            self.token = response['token']
            self.tokenLastUpdate = time.time()
            self.session.auth = T411Auth(self.token)
            return True
        else:
            logger.log(u"Token not found in authentication response", logger.WARNING)
            return False
    
    def get_search_url_episode(self, search_string, subCategory, ep_obj=None):
        search_url = None
        episode_api_number = None
        season_api_number = None
        
        # for Serie TV , Animation Serie and Emission TV
        if subCategory == 433 or subCategory == 637 or subCategory == 639:
            # if episode object is available
            if ep_obj:
                # ["46"]['terms'] = SérieTV - Episode list (common to subcategory 433, 637 and 639)
                episode_api_number = [(key, value) for key, value in self.apiTermsTree[str(subCategory)]["46"]['terms'].iteritems() if value.endswith("%02d" % (int(ep_obj.episode)))]
                # ["45"]['terms'] = SérieTV - Saison list ( common to subcategory 433, 637 and 639)
                season_api_number  = [(key, value) for key, value in self.apiTermsTree[str(subCategory)]["45"]['terms'].iteritems() if value.endswith("%02d" % (int(ep_obj.season)))]
                # construct url with episode and season terms
                search_url = self.urls['search'] % ( search_string , subCategory ) + '&term[46][]=%s&term[45][]=%s' % (episode_api_number[0][0], season_api_number[0][0])
        
        return search_url
      
    def get_search_url_season(self, search_string, subCategory, ep_obj=None):
        search_url = None
        season_api_number = None
        
        # for Serie TV , Animation Serie and Emission TV
        if subCategory == 433 or subCategory == 637 or subCategory == 639:
            # if episode object is available
            if ep_obj:
                # ["45"]['terms'] = SérieTV - Saison list ( common to subcategory 433, 637 and 639)
                season_api_number = [(key, value) for key, value in self.apiTermsTree[str(subCategory)]["45"]['terms'].iteritems() if value.endswith("%02d" % (int(ep_obj.season)))]
                # construct url with episode and season terms "term[46][]=936" = Saison Complete
                search_url = self.urls['search'] % ( search_string , subCategory ) + '&term[46][]=936&term[45][]=%s' % (season_api_number[0][0])
        
        return search_url
      
    def get_filtered_items_from_torrents(self, mode, torrents):
        items = []
        for torrent in torrents:
            # filter by categories for RSS
            if mode == 'RSS' and int(torrent['category']) not in self.subcategories:
                continue
          
            try:
                # Retrieve torrent info
                title = torrent['name']
                torrent_id = torrent['id']
                download_url = (self.urls['download'] % torrent_id).encode('utf8')
                if not all([title, download_url]):
                    continue
          
                seeders = int(torrent['seeders'])
                leechers = int(torrent['leechers'])
                verified = bool(torrent['isVerified'])
                torrent_size = torrent['size']
                size = convert_size(torrent_size) or -1
          
                # Filter unseeded torrent
                if seeders < self.minseed or leechers < self.minleech:
                    if mode != 'RSS':
                        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                    continue
              
                # Filter by verified if necessary
                if self.confirmed and not verified and mode != 'RSS':
                    logger.log(u"Found result %s but that doesn't seem like a verified result so I'm ignoring it" % title, logger.DEBUG)
                    continue
              
                # Construct item
                item = title, download_url, size, seeders, leechers
                if mode != 'RSS':
                    logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)
              
                # Memorize item
                items.append(item)
          
            except Exception:
                logger.log(u"Invalid torrent data, skipping result: %s" % torrent, logger.DEBUG)
                logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.DEBUG)
              
        return items
        
    def get_torrents_from_search_url(self, mode, search_url):
        torrents = []
        offset = 0
        newOffset = 0
        total  = 1                          
        while offset < total:
            #update url offset
            if mode != 'RSS':
                search_url = search_url.replace(u"offset=%s" % (offset),u"offset=%s" % (newOffset))
                        
            logger.log(u"Search URL: %s" % search_url, logger.DEBUG)
            data = self.get_url(search_url, json=True)
            if data:
                try:
                    # if not 'torrents' key in data
                    if 'torrents' not in data and mode != 'RSS':
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                    else:
                        torrents = data['torrents'] if mode != 'RSS' else data    
                except Exception:
                        logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)
                
                # offset update for next page of query
                if mode != 'RSS':
                    newOffset = int(data['offset']) + 100
                    total = int(data['total'])
                else:
                    break
            
            offset = newOffset     
                      
        return torrents

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []
        if not self.login():
            return results
        
        if not self.apiTermsTree:
            self.apiTermsTree = self.get_url(self.urls['terms_tree'], json=True)
        
        logger.log(u"Search Queries : %s" % search_params, logger.DEBUG)

        for mode in search_params:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:
                
                if mode == 'RSS':
                    search_url = self.urls['rss']
                    torrents = self.get_torrents_from_search_url(mode, search_url)
                    items = self.get_filtered_items_from_torrents(mode, torrents)
                else :
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)
                    # for each subCategory
                    for subCategory in self.subcategories:
                        search_url = None
                        # try to construct a url more precise
                        if mode == 'Episode':
                            search_url = self.get_search_url_episode(search_string, subCategory, ep_obj)
                        elif mode == 'Season':
                            search_url = self.get_search_url_season(search_string, subCategory, ep_obj)
                        
                        # if no precise url
                        if not search_url:
                            # standard search
                            search_url = self.urls['search'] % (search_string, subCategory)
                        
                        # get torrents results
                        torrents = self.get_torrents_from_search_url(mode, search_url)
                        # filter torrent and add to items
                        items += self.get_filtered_items_from_torrents( mode, torrents)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items
                       
        return results

    def seed_ratio(self):
        return self.ratio


class T411Auth(AuthBase):  # pylint: disable=too-few-public-methods
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        return r

provider = T411Provider()
