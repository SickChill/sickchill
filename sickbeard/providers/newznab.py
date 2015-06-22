# Author: Nic Wolfe <nic@wolfeden.ca>
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

import urllib
import time
import datetime
import os
import re

import sickbeard
import generic
from sickbeard.common import Quality
from sickbeard import classes
from sickbeard import helpers
from sickbeard import scene_exceptions
from sickbeard import encodingKludge as ek
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard.exceptions import AuthException

class NewznabProvider(generic.NZBProvider):
    def __init__(self, name, url, key='0', catIDs='5030,5040', search_mode='eponly', search_fallback=False,
                 enable_daily=False, enable_backlog=False):

        generic.NZBProvider.__init__(self, name)

        self.cache = NewznabCache(self)

        self.urls = {'base_url': url}

        self.url = self.urls['base_url']

        self.key = key

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog

        # a 0 in the key spot indicates that no key is needed
        if self.key == '0':
            self.needs_auth = False
        else:
            self.needs_auth = True

        if catIDs:
            self.catIDs = catIDs
        else:
            self.catIDs = '5030,5040'

        self.enabled = True
        self.supportsBacklog = True

        self.default = False
        self.last_search = datetime.datetime.now()

    def configStr(self):
        return self.name + '|' + self.url + '|' + self.key + '|' + self.catIDs + '|' + str(
            int(self.enabled)) + '|' + self.search_mode + '|' + str(int(self.search_fallback)) + '|' + str(
            int(self.enable_daily)) + '|' + str(int(self.enable_backlog))

    def imageName(self):
        if ek.ek(os.path.isfile,
                 ek.ek(os.path.join, sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME, 'images', 'providers',
                       self.getID() + '.png')):
            return self.getID() + '.png'
        return 'newznab.png'

    def isEnabled(self):
        return self.enabled

    def _getURL(self, url, post_data=None, params=None, timeout=30, json=False):
        return self.getURL(url, post_data=post_data, params=params, timeout=timeout, json=json)
    
    def get_newznab_categories(self):
        """
        Uses the newznab provider url and apikey to get the capabilities.
        Makes use of the default newznab caps param. e.a. http://yournewznab/api?t=caps&apikey=skdfiw7823sdkdsfjsfk
        Returns a tuple with (succes or not, array with dicts [{"id": "5070", "name": "Anime"}, 
        {"id": "5080", "name": "Documentary"}, {"id": "5020", "name": "Foreign"}...etc}], error message)
        """
        return_categories = []
        
        self._checkAuth()
        
        params = {"t": "caps"}
        if self.needs_auth and self.key:
            params['apikey'] = self.key

        try:
            data = self.cache.getRSSFeed("%s/api?%s" % (self.url, urllib.urlencode(params)))
        except:
            logger.log(u"Error getting html for [%s]" % 
                    ("%s/api?%s" % (self.url, '&'.join("%s=%s" % (x,y) for x,y in params.items())) ), logger.DEBUG)
            return (False, return_categories, "Error getting html for [%s]" % 
                    ("%s/api?%s" % (self.url, '&'.join("%s=%s" % (x,y) for x,y in params.items()) )))

        if not self._checkAuthFromData(data):
            logger.log(u"Error parsing xml for [%s]" % (self.name), logger.DEBUG)
            return False, return_categories, "Error parsing xml for [%s]" % (self.name)
            
        try:
            for category in data.feed.categories:
                if category.get('name') == 'TV':
                        for subcat in category.subcats:
                            return_categories.append(subcat)
        except:
            logger.log(u"Error parsing result for [%s]" % (self.name),
                       logger.DEBUG)
            return (False, return_categories, "Error parsing result for [%s]" % (self.name))                                         
          
        return True, return_categories, ""

    def _get_season_search_strings(self, ep_obj):

        to_return = []
        cur_params = {}

        cur_params['maxage'] = (datetime.datetime.now() - datetime.datetime.combine(ep_obj.airdate, datetime.datetime.min.time())).days + 1

        # season
        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate).split('-')[0]
            cur_params['season'] = date_str
            cur_params['q'] = date_str.replace('-', '.')
        elif ep_obj.show.is_anime:
            cur_params['season'] = "%d" % ep_obj.scene_absolute_number
        else:
            cur_params['season'] = str(ep_obj.scene_season)

        # search
        rid = helpers.mapIndexersToShow(ep_obj.show)[2]
        if rid:
            cur_params['rid'] = rid
        elif 'rid' in params:
            cur_params.pop('rid')

        # add new query strings for exceptions
        name_exceptions = list(
            set(scene_exceptions.get_scene_exceptions(ep_obj.show.indexerid) + [ep_obj.show.name]))
        for cur_exception in name_exceptions:
            if 'q' in cur_params:
                cur_params['q'] = helpers.sanitizeSceneName(cur_exception) + '.' + cur_params['q']
            else:
                cur_params['q'] = helpers.sanitizeSceneName(cur_exception)
            to_return.append(cur_params)

        return to_return

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        to_return = []
        params = {}

        if not ep_obj:
            return [params]

        params['maxage'] = (datetime.datetime.now() - datetime.datetime.combine(ep_obj.airdate, datetime.datetime.min.time())).days + 1

        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate)
            params['season'] = date_str.partition('-')[0]
            params['ep'] = date_str.partition('-')[2].replace('-', '/')
        elif ep_obj.show.anime:
            params['ep'] = "%i" % int(ep_obj.scene_absolute_number if int(ep_obj.scene_absolute_number) > 0 else ep_obj.scene_episode)
        else:
            params['season'] = ep_obj.scene_season
            params['ep'] = ep_obj.scene_episode

        # search
        rid = helpers.mapIndexersToShow(ep_obj.show)[2]
        if rid:
            params['rid'] = rid
        elif 'rid' in params:
            params.pop('rid')

        # add new query strings for exceptions
        name_exceptions = list(
            set(scene_exceptions.get_scene_exceptions(ep_obj.show.indexerid) + [ep_obj.show.name]))
        for cur_exception in name_exceptions:
            params['q'] = helpers.sanitizeSceneName(cur_exception)
            if add_string:
                params['q'] += ' ' + add_string

            to_return.append(params)

            if ep_obj.show.anime:
                paramsNoEp = params.copy()
                paramsNoEp['q'] = paramsNoEp['q'] + " " + paramsNoEp['ep']
                if "ep" in paramsNoEp:
                    paramsNoEp.pop("ep")
                to_return.append(paramsNoEp)

        return to_return

    def _doGeneralSearch(self, search_string):
        return self._doSearch({'q': search_string})

    def _checkAuth(self):

        if self.needs_auth and not self.key:
            logger.log(u"Incorrect authentication credentials for " + self.name + " : " + "API key is missing",
                       logger.DEBUG)
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _checkAuthFromData(self, data):

        try:
            data['feed']
            data['entries']
        except:return self._checkAuth()

        try:
            bozo = int(data['bozo'])
            bozo_exception = data['bozo_exception']
            err_code = int(data['feed']['error']['code'])
            err_desc = data['feed']['error']['description']
            if not err_code or err_desc:
                raise
        except:
            return True

        if err_code == 100:
            raise AuthException("Your API key for " + self.name + " is incorrect, check your config.")
        elif err_code == 101:
            raise AuthException("Your account on " + self.name + " has been suspended, contact the administrator.")
        elif err_code == 102:
            raise AuthException(
                "Your account isn't allowed to use the API on " + self.name + ", contact the administrator")
        elif bozo == 1:
            raise Exception(bozo_exception)
        else:
            logger.log(u"Unknown error given from " + self.name + ": " + err_desc, logger.ERROR)

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        self._checkAuth()

        params = {"t": "tvsearch",
                  "maxage": sickbeard.USENET_RETENTION,
                  "limit": 100,
                  "attrs": "rageid",
                  "offset": 0}

        # category ids
        if self.show and self.show.is_sports:
            params['cat'] = self.catIDs + ',5060'
        elif self.show and self.show.is_anime:
            params['cat'] = self.catIDs + ',5070'
        else:
            params['cat'] = self.catIDs

        params['maxage'] = (4, age)[age]

        if search_params:
            params.update(search_params)

        if self.needs_auth and self.key:
            params['apikey'] = self.key

        results = []
        offset = total = 0

        while (total >= offset):
            search_url = self.url + 'api?' + urllib.urlencode(params)

            while((datetime.datetime.now() - self.last_search).seconds < 5):
                time.sleep(1)

            logger.log(u"Search url: " + search_url, logger.DEBUG)

            data = self.cache.getRSSFeed(search_url)

            self.last_search = datetime.datetime.now()

            if not self._checkAuthFromData(data):
                break

            for item in data['entries'] or []:

                (title, url) = self._get_title_and_url(item)

                if title and url:
                    results.append(item)
                else:
                    logger.log(
                        u"The data returned from the " + self.name + " is incomplete, this result is unusable",
                        logger.DEBUG)

            # get total and offset attribs
            try:
                if total == 0:
                    total = int(data['feed'].newznab_response['total'] or 0)
                offset = int(data['feed'].newznab_response['offset'] or 0)
            except AttributeError:
                break

            # No items found, prevent from doing another search
            if total == 0:
                break

            if offset != params['offset']:
                logger.log("Tell your newznab provider to fix their bloody newznab responses")
                break

            params['offset'] += params['limit']
            if (total > int(params['offset'])) and (offset < 500):
                offset = int(params['offset'])
                # if there are more items available then the amount given in one call, grab some more
                logger.log(u'%d' % (total - offset) + ' more items to be fetched from provider.' +
                'Fetching another %d' % int(params['limit']) + ' items.', logger.DEBUG)
            else:
                logger.log(u'No more searches needed.', logger.DEBUG)
                break

        return results

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
                searchStrings = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')
                for searchString in searchStrings:
                    for item in self._doSearch(searchString):
                        title, url = self._get_title_and_url(item)
                        if(re.match(r'.*(REPACK|PROPER).*', title, re.I)):
                             results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results


class NewznabCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll newznab providers every 30 minutes
        self.minTime = 30
        self.last_search = datetime.datetime.now()

    def _getRSSData(self):

        params = {"t": "tvsearch",
                  "cat": self.provider.catIDs + ',5060,5070',
                  "attrs": "rageid",
                  "maxage": 4,
                 }

        if self.provider.needs_auth and self.provider.key:
            params['apikey'] = self.provider.key

        rss_url = self.provider.url + 'api?' + urllib.urlencode(params)

        while((datetime.datetime.now() - self.last_search).seconds < 5):
                time.sleep(1)

        logger.log(self.provider.name + " cache update URL: " + rss_url, logger.DEBUG)
        data = self.getRSSFeed(rss_url)

        self.last_search = datetime.datetime.now()

        return data

    def _checkAuth(self, data):
        return self.provider._checkAuthFromData(data)

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)

        self._checkItemAuth(title, url)

        if not title or not url:
            logger.log(
                u"The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable",
                logger.DEBUG)
            return None

        tvrageid = 0
        for attr in item['newznab_attr'] if isinstance(item['newznab_attr'], list) else [item['newznab_attr']]:
            if attr['name'] == 'tvrageid' or attr['name'] == 'rageid':
                tvrageid = int(attr['value'] or 0)
                break

        logger.log(u"Attempting to add item from RSS to cache: " + title, logger.DEBUG)
        return self._addCacheEntry(title, url, indexer_id=tvrageid)
