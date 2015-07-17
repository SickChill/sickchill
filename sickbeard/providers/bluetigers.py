# -*- coding: latin-1 -*-
# Author: raver2046 <raver2046@gmail.com>
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
from unidecode import unidecode
from sickbeard import classes
from sickbeard.helpers import sanitizeSceneName
from sickbeard.exceptions import ex


class BLUETIGERSProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "BLUETIGERS")

        self.supportsBacklog = True
        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None
        self.token = None
        self.tokenLastUpdate = None

        self.cache = BLUETIGERSCache(self)

        self.urls = {'base_url': 'https://www.bluetigers.ca/',
                     'search': 'https://www.bluetigers.ca/torrents-search.php?search=%s%s',
                     'login': 'https://www.bluetigers.ca/account-login.php',
                     'download': 'https://www.bluetigers.ca/torrents-details.php?id=%s&hit=1',
        }

        self.url = self.urls['base_url']
        self.categories = "&c16=1&c10=1&c130=1&c131=1&c17=1&c18=1&c19=1"

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'BLUETIGERS.png'

    def getQuality(self, item, anime=False):
        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _doLogin(self):      


        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

      
        login_params = {'username': self.username,
                            'password': self.password,
                            'take_login' : '1'
        }

        if not self.session:
            self.session = requests.Session()

        logger.log('Performing authentication to BLUETIGERS', logger.DEBUG)
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
                        result_linkz = html.findAll('a',  href=re.compile("torrents-details"))
        
                        if not result_linkz:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.DEBUG)
                            continue
                        
                        if result_linkz:
                            for link in result_linkz:                                                                                                                               
                                title = link.text
                                logger.log(u"BLUETIGERS TITLE TEMP: " + title, logger.DEBUG)                   
                                download_url =   self.urls['base_url']  + "/" + link['href'] 
                                download_url = download_url.replace("torrents-details","download")             
                                logger.log(u"BLUETIGERS downloadURL: " + download_url, logger.DEBUG)
        
                                if not title or not download_url:
                                   continue

                                item = title, download_url
                                logger.log(u"Found result: " + title.replace(' ','.') + " (" + download_url + ")", logger.DEBUG)

                                items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(), logger.ERROR)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url = item

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


class BLUETIGERSAuth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        return r


class BLUETIGERSCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # Only poll BLUETIGERS every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = BLUETIGERSProvider()
