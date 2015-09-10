# coding=utf-8
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

import traceback
import re
import datetime
import generic
import datetime
import json
import time


import sickbeard
from sickbeard.common import Quality, USER_AGENT
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard import helpers
from sickbeard import classes
from sickbeard.exceptions import ex
from sickbeard.indexers.indexer_config import INDEXER_TVDB


class GetOutOfLoop(Exception):
    pass


class RarbgProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "Rarbg")

        self.enabled = False
        self.supportsBacklog = True
        self.ratio = None
        self.minseed = None
        self.ranked = None
        self.sorting = None
        self.minleech = None
        self.token = None
        self.tokenExpireDate = None

        self.urls = {'url': u'https://rarbg.com',
                     'token': u'http://torrentapi.org/pubapi_v2.php?get_token=get_token&format=json&app_id=sickrage',
                     'listing': u'http://torrentapi.org/pubapi_v2.php?mode=list&app_id=sickrage',
                     'search': u'http://torrentapi.org/pubapi_v2.php?mode=search&app_id=sickrage&search_string={search_string}',
                     'search_tvdb': u'http://torrentapi.org/pubapi_v2.php?mode=search&app_id=sickrage&search_tvdb={tvdb}&search_string={search_string}',
                     'api_spec': u'https://rarbg.com/pubapi/apidocs.txt',
                     }

        self.url = self.urls['listing']

        self.urlOptions = {'categories': '&category={categories}',
                        'seeders': '&min_seeders={min_seeders}',
                        'leechers': '&min_leechers={min_leechers}',
                        'sorting' : '&sort={sorting}',
                        'limit': '&limit={limit}',
                        'format': '&format={format}',
                        'ranked': '&ranked={ranked}',
                        'token': '&token={token}',
        }

        self.defaultOptions = self.urlOptions['categories'].format(categories='tv') + \
                                self.urlOptions['limit'].format(limit='100') + \
                                self.urlOptions['format'].format(format='json')

        self.next_request = datetime.datetime.now()

        self.cache = RarbgCache(self)

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'rarbg.png'

    def _doLogin(self):
        if self.token and self.tokenExpireDate and datetime.datetime.now() < self.tokenExpireDate:
            return True

        resp_json = None

        response = self.getURL(self.urls['token'], timeout=30, json=True)
        if not response:
            logger.log(u'Unable to connect to %s provider.' % self.name, logger.WARNING)
            return False

        try:
            if response['token']:
                self.token = response['token']
                self.tokenExpireDate = datetime.datetime.now() + datetime.timedelta(minutes=14)
                return True
        except Exception as e:
            logger.log(u'%s provider: No token found' % self.name, logger.WARNING)
            logger.log(u'%s provider: No token found: %s' % (self.name, ex(e)), logger.DEBUG)

        return False

    def getQuality(self, item, anime=False):
        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)  #1) showName.SXX

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name + ' ' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name + ' ' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode}
                if add_string:
                    ep_string = ep_string + ' %s' % add_string

                search_string['Episode'].append(ep_string)

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        if epObj != None:
            ep_indexerid = epObj.show.indexerid
            ep_indexer = epObj.show.indexer
        else:
            ep_indexerid = None
            ep_indexer = None

        for mode in search_params.keys(): #Mode = RSS, Season, Episode
            for search_string in search_params[mode]:
                if mode == 'RSS':
                    searchURL = self.urls['listing'] + self.defaultOptions
                elif mode == 'Season':
                    if ep_indexer == INDEXER_TVDB:
                        searchURL = self.urls['search_tvdb'].format(search_string=search_string, tvdb=ep_indexerid) + self.defaultOptions
                    else:
                        searchURL = self.urls['search'].format(search_string=search_string) + self.defaultOptions
                elif mode == 'Episode':
                    if ep_indexer == INDEXER_TVDB:
                        searchURL = self.urls['search_tvdb'].format(search_string=search_string, tvdb=ep_indexerid) + self.defaultOptions
                    else:
                        searchURL = self.urls['search'].format(search_string=search_string) + self.defaultOptions
                else:
                    logger.log(u'{name} invalid search mode:{mode}'.format(name=self.name, mode=mode), logger.ERROR)

                if self.minleech:
                    searchURL += self.urlOptions['leechers'].format(min_leechers=int(self.minleech))

                if self.minseed:
                    searchURL += self.urlOptions['seeders'].format(min_seeders=int(self.minseed))

                if self.sorting:
                    searchURL += self.urlOptions['sorting'].format(sorting=self.sorting)

                if self.ranked:
                    searchURL += self.urlOptions['ranked'].format(ranked=int(self.ranked))

                logger.log(u'{name} search page URL: {url}'.format(name=self.name, url=searchURL), logger.DEBUG)

                try:
                    retry = 3
                    while retry > 0:
                        time_out = 0
                        while (datetime.datetime.now() < self.next_request) and time_out <= 15:
                            time_out = time_out + 1
                            time.sleep(1)

                        data = self.getURL(searchURL + self.urlOptions['token'].format(token=self.token))

                        self.next_request = datetime.datetime.now() + datetime.timedelta(seconds=10)

                        if not data:
                            logger.log(u'{name} no data returned.'.format(name=self.name), logger.DEBUG)
                            raise GetOutOfLoop
                        if re.search('ERROR', data):
                            logger.log(u'{name} returned an error.'.format(name=self.name), logger.DEBUG)
                            raise GetOutOfLoop
                        if re.search('No results found', data):
                            logger.log(u'{name} no results found.'.format(name=self.name), logger.DEBUG)
                            raise GetOutOfLoop
                        if re.search('Invalid token set!', data):
                            logger.log(u'{name} Invalid token set!'.format(name=self.name), logger.ERROR)
                            return results
                        if re.search('Too many requests per minute. Please try again later!', data):
                            logger.log(u'{name} Too many requests per minute.'.format(name=self.name), logger.DEBUG)
                            retry = retry - 1
                            time.sleep(10)
                            continue
                        if re.search('Cant find search_tvdb in database. Are you sure this imdb exists?', data):
                            logger.log(u'{name} no results found. Search tvdb id do not exist on server.'.format(name=self.name), logger.DEBUG)
                            raise GetOutOfLoop
                        if re.search('Invalid token. Use get_token for a new one!', data):
                            logger.log(u'{name} Invalid token, retrieving new token'.format(name=self.name), logger.DEBUG)
                            retry = retry - 1
                            self.token = None
                            self.tokenExpireDate = None
                            if not self._doLogin():
                                logger.log(u'{name} Failed retrieving new token'.format(name=self.name), logger.DEBUG)
                                return results
                            logger.log(u'{name} Using new token'.format(name=self.name), logger.DEBUG)
                            continue
                        if re.search('<div id="error">.*</div>', data):
                            logger.log(u'{name} {proxy} does not support https.'.format(name=self.name, proxy=self.proxy.getProxyURL()), logger.DEBUG)
                            searchURL = searchURL.replace(u'https', 'http')
                            continue

                        #No error found break
                        break
                    else:
                        logger.log(u'{name} Retried 3 times without getting results.'.format(name=self.name), logger.DEBUG)
                        continue
                except GetOutOfLoop:
                    continue

                try:
                    data = re.search('\[\{\"filename\".*\}\]', data)
                    if data is not None:
                        data_json = json.loads(data.group())
                    else:
                        data_json = {}
                except Exception as e:
                    logger.log(u'{name} json load failed: {traceback_info}'.format(name=self.name, traceback_info=traceback.format_exc()), logger.DEBUG)
                    logger.log(u'{name} json load failed. Data dump = {data}'.format(name=self.name, data=data), logger.DEBUG)
                    logger.log(u'{name} json load failed.'.format(name=self.name), logger.ERROR)
                    continue

                try:
                    for item in data_json:
                        try:
                            torrent_title = item['filename']
                            torrent_download = item['download']
                            if torrent_title and torrent_download:
                                items[mode].append((torrent_title, torrent_download))
                            else:
                                logger.log(u'{name} skipping invalid result'.format(name=self.name), logger.DEBUG)
                        except Exception:
                            logger.log(u'{name} skipping invalid result: {traceback_info}'.format(name=self.name, traceback_info=traceback.format_exc()), logger.DEBUG)
                except Exception:
                    logger.log(u'{name} failed parsing data: {traceback_info}'.format(name=self.name, traceback_info=traceback.format_exc()), logger.ERROR)
            results += items[mode]

        return results

    def _get_title_and_url(self, item):
        """
        Retrieves the title and URL data from the item XML node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns: A tuple containing two strings representing title and URL respectively
        """

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


class RarbgCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll RARbg every 15 minutes max
        self.minTime = 5

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = RarbgProvider()
