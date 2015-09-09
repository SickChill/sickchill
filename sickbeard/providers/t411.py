# -*- coding: latin-1 -*-
# Author: djoole <bobby.djoole@gmail.com>
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

import requests

from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard import helpers
from sickbeard import classes
from sickbeard.helpers import sanitizeSceneName
from sickbeard.exceptions import ex


class T411Provider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "T411")

        self.supportsBacklog = True
        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None
        self.token = None
        self.tokenLastUpdate = None

        self.cache = T411Cache(self)

        self.urls = {'base_url': 'http://www.t411.io/',
                     'search': 'https://api.t411.io/torrents/search/%s?cid=%s&limit=100',
                     'login_page': 'https://api.t411.io/auth',
                     'download': 'https://api.t411.io/torrents/download/%s',
        }

        self.url = self.urls['base_url']

        self.subcategories = [433, 637, 455, 639]

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 't411.png'

    def getQuality(self, item, anime=False):
        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _doLogin(self):

        if self.token is not None:
            if time.time() < (self.tokenLastUpdate + 30 * 60):
                logger.log('T411 Authentication token is still valid', logger.DEBUG)
                return True

        login_params = {'username': self.username,
                        'password': self.password}

        logger.log('Performing authentication to T411', logger.DEBUG)

        response = helpers.getURL(self.urls['login_page'], post_data=login_params, timeout=30, json=True)
        if not response:
            logger.log(u'Unable to connect to ' + self.name + ' provider.', logger.WARNING)
            return False

        if response and 'token' in response:
            self.token = response['token']
            self.tokenLastUpdate = time.time()
            self.uid = response['uid'].encode('ascii', 'ignore')
            self.session.auth = T411Auth(self.token)
            logger.log('Using T411 Authorization token : ' + self.token, logger.DEBUG)
            return True
        else:
            logger.log('T411 token not found in authentication response', logger.WARNING)
            return False

    def _get_season_search_strings(self, ep_obj):
        search_string = {'Season': []}
        if not ep_obj:
            return [search_string]

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
            return [search_string]

        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            ep_string = sanitizeSceneName(show_name) + '.'
            if self.show.air_by_date:
                ep_string += str(ep_obj.airdate).replace('-', '|')
            elif self.show.sports:
                ep_string += str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
            elif self.show.anime:
                ep_string += "%i" % int(ep_obj.scene_absolute_number)
            else:
                 ep_string += sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                   'episodenumber': ep_obj.scene_episode}

            if add_string:
                ep_string += ' %s' % add_string
            search_string['Episode'].append(re.sub('\s+', '.', ep_string))

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        logger.log(u"_doSearch started with ..." + str(search_params), logger.DEBUG)

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():

            for search_string in search_params[mode]:

                for sc in self.subcategories:
                    searchURL = self.urls['search'] % (search_string, sc)
                    logger.log(u"" + self.name + " search page URL: " + searchURL, logger.DEBUG)

                    data = self.getURL(searchURL, json=True)
                    if not data:
                        continue
                    try:

                        if 'torrents' not in data:
                            logger.log(
                                u"The Data returned from " + self.name + " do not contains any torrent : " + str(data),
                                logger.DEBUG)
                            continue

                        torrents = data['torrents']

                        if not torrents:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.WARNING)
                            continue

                        for torrent in torrents:
                            try:
                                torrent_name = torrent['name']
                                torrent_id = torrent['id']
                                torrent_download_url = (self.urls['download'] % torrent_id).encode('utf8')

                                if not torrent_name or not torrent_download_url:
                                    continue

                                item = torrent_name, torrent_download_url
                                logger.log(u"Found result: " + torrent_name + " (" + torrent_download_url + ")",
                                           logger.DEBUG)
                                items[mode].append(item)
                            except Exception as e:
                                logger.log(u"Invalid torrent data, skipping results: {0}".format(str(torrent)), logger.DEBUG)
                                continue

                    except Exception, e:
                        logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(),
                                   logger.ERROR)
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

                searchResults = self._doSearch(searchString[0])
                for item in searchResults:
                    title, url = self._get_title_and_url(item)
                    if title and url:
                        results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio


class T411Auth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        return r


class T411Cache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # Only poll T411 every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = T411Provider()
