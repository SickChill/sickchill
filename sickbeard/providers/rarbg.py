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
import json
import time

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.common import USER_AGENT
from sickbeard.indexers.indexer_config import INDEXER_TVDB


class GetOutOfLoop(Exception):
    pass


class RarbgProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "Rarbg")

        self.supportsBacklog = True
        self.public = True
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
                     'api_spec': u'https://rarbg.com/pubapi/apidocs.txt'}

        self.url = self.urls['listing']

        self.urlOptions = {'categories': '&category={categories}',
                           'seeders': '&min_seeders={min_seeders}',
                           'leechers': '&min_leechers={min_leechers}',
                           'sorting' : '&sort={sorting}',
                           'limit': '&limit={limit}',
                           'format': '&format={format}',
                           'ranked': '&ranked={ranked}',
                           'token': '&token={token}'}

        self.defaultOptions = self.urlOptions['categories'].format(categories='tv') + \
                                self.urlOptions['limit'].format(limit='100') + \
                                self.urlOptions['format'].format(format='json_extended')

        self.proper_strings = ['{{PROPER|REPACK}}']

        self.next_request = datetime.datetime.now()

        self.headers.update({'User-Agent': USER_AGENT})

        self.cache = RarbgCache(self)

    def _doLogin(self):
        if self.token and self.tokenExpireDate and datetime.datetime.now() < self.tokenExpireDate:
            return True


        response = self.getURL(self.urls['token'], timeout=30, json=True)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        try:
            if response['token']:
                self.token = response['token']
                self.tokenExpireDate = datetime.datetime.now() + datetime.timedelta(minutes=14)
                return True
        except Exception as e:
            logger.log(u"No token found", logger.WARNING)
            logger.log(u"No token found: %s" % repr(e), logger.DEBUG)

        return False

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

        for mode in search_params.keys():  # Mode = RSS, Season, Episode
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                if mode is 'RSS':
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
                    logger.log(u"Invalid search mode: %s " % mode, logger.ERROR)

                if self.minleech:
                    searchURL += self.urlOptions['leechers'].format(min_leechers=int(self.minleech))

                if self.minseed:
                    searchURL += self.urlOptions['seeders'].format(min_seeders=int(self.minseed))

                if self.sorting:
                    searchURL += self.urlOptions['sorting'].format(sorting=self.sorting)

                if self.ranked:
                    searchURL += self.urlOptions['ranked'].format(ranked=int(self.ranked))

                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)

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
                            logger.log(u"No data returned from provider", logger.DEBUG)
                            raise GetOutOfLoop
                        if re.search('ERROR', data):
                            logger.log(u"Error returned from provider", logger.DEBUG)
                            raise GetOutOfLoop
                        if re.search('No results found', data):
                            logger.log(u"No results found", logger.DEBUG)
                            raise GetOutOfLoop
                        if re.search('Invalid token set!', data):
                            logger.log(u"Invalid token!", logger.WARNING)
                            return results
                        if re.search('Too many requests per minute. Please try again later!', data):
                            logger.log(u"Too many requests per minute", logger.WARNING)
                            retry = retry - 1
                            time.sleep(10)
                            continue
                        if re.search('Cant find search_tvdb in database. Are you sure this imdb exists?', data):
                            logger.log(u"No results found. The tvdb id: %s do not exist on provider" % ep_indexerid, logger.WARNING)
                            raise GetOutOfLoop
                        if re.search('Invalid token. Use get_token for a new one!', data):
                            logger.log(u"Invalid token, retrieving new token", logger.DEBUG)
                            retry = retry - 1
                            self.token = None
                            self.tokenExpireDate = None
                            if not self._doLogin():
                                logger.log(u"Failed retrieving new token", logger.DEBUG)
                                return results
                            logger.log(u"Using new token", logger.DEBUG)
                            continue

                        # No error found break
                        break
                    else:
                        logger.log(u"Retried 3 times without getting results", logger.DEBUG)
                        continue
                except GetOutOfLoop:
                    continue

                try:
                    data = re.search(r'\[\{\"title\".*\}\]', data)
                    if data is not None:
                        data_json = json.loads(data.group())
                    else:
                        data_json = {}
                except Exception:
                    logger.log(u"JSON load failed: %s" % traceback.format_exc(), logger.ERROR)
                    logger.log(u"JSON load failed. Data dump: %s" % data, logger.DEBUG)
                    continue

                try:
                    for item in data_json:
                        try:
                            title = item['title']
                            download_url = item['download']
                            size = item['size']
                            seeders = item['seeders']
                            leechers = item['leechers']
                            # pubdate = item['pubdate']

                            if not all([title, download_url]):
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)
                            items[mode].append(item)

                        except Exception:
                            logger.log(u"Skipping invalid result. JSON item: %s" % item, logger.DEBUG)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)
            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class RarbgCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll RARBG every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = RarbgProvider()
