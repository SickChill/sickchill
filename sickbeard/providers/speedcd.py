# Author: Mr_Orange
# URL: https://github.com/mr-orange/Sick-Beard
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import re
import datetime
import urlparse
import sickbeard
import generic

from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard.common import Overview
from sickbeard.exceptions import ex
from sickbeard import clients
from lib import requests
from lib.requests import exceptions
from sickbeard.helpers import sanitizeSceneName


class SpeedCDProvider(generic.TorrentProvider):

    urls = {'base_url': 'http://speed.cd/',
            'login': 'http://speed.cd/takelogin.php',
            'detail': 'http://speed.cd/t/%s',
            'search': 'http://speed.cd/V3/API/API.php',
            'download': 'http://speed.cd/download.php?torrent=%s',
            }

    def __init__(self):

        generic.TorrentProvider.__init__(self, "Speedcd")

        self.supportsBacklog = True

        self.cache = SpeedCDCache(self)

        self.url = self.urls['base_url']

        self.categories = {'Season': {'c14':1}, 'Episode': {'c2':1, 'c49':1}, 'RSS': {'c14':1, 'c2':1, 'c49':1}}

    def isEnabled(self):
        return sickbeard.SPEEDCD

    def imageName(self):
        return 'speedcd.png'

    def getQuality(self, item):

        quality = Quality.sceneQuality(item[0])
        return quality

    def _doLogin(self):

        login_params = {'username': sickbeard.SPEEDCD_USERNAME,
                        'password': sickbeard.SPEEDCD_PASSWORD
                        }

        self.session = requests.Session()

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
            return False

        if re.search('Incorrect username or Password. Please try again.', response.text) \
        or response.status_code == 401:
            logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
            return False

        return True

    def _get_season_search_strings(self, ep_obj):

        #If Every episode in Season is a wanted Episode then search for Season first
        search_string = {'Season': [], 'Episode': []}
        if not (ep_obj.show.air_by_date or ep_obj.show.sports):
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name +' S%02d' % int(ep_obj.scene_season) #1) showName SXX
                search_string['Season'].append(ep_string)
        elif ep_obj.show.air_by_date or ep_obj.show.sports:
            search_string['Season'] = self._get_episode_search_strings(ep_obj)[0]['Season']

        #search_string['Episode'] = self._get_episode_search_strings(ep_obj)[0]['Episode']

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) +' '+ \
                sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season, 'episodenumber': ep_obj.scene_episode}

                search_string['Episode'].append(re.sub('\s+', ' ', ep_string))

        return [search_string]

    def _doSearch(self, search_params, show=None, age=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return []

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                logger.log(u"Search string: " + search_string, logger.DEBUG)

                search_string = '+'.join(search_string.split())

                post_data  = dict({'/browse.php?' : None, 'cata': 'yes','jxt': 4,'jxw': 'b','search': search_string}, **self.categories[mode])

                data = self.session.post(self.urls['search'], data=post_data).json()

                try:
                    torrents = data.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
                except:
                    continue

                for torrent in torrents:

                    if sickbeard.SPEEDCD_FREELEECH and not torrent['free']:
                        continue

                    title = re.sub('<[^>]*>', '', torrent['name'])
                    url = self.urls['download'] %(torrent['id'])
                    seeders = int(torrent['seed'])
                    leechers = int(torrent['leech'])

                    if mode != 'RSS' and seeders == 0:
                        continue

                    if not title or not url:
                        continue

                    item = title, url, seeders, leechers
                    items[mode].append(item)

            #For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[2], reverse=True)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url, seeders, leechers = item

        if url:
            url = str(url).replace('&amp;','&')

        return (title, url)

    def getURL(self, url, post_data=None, headers=None, json=False):
        if not self.session:
            self._doLogin()

        try:
            # Remove double-slashes from url
            parsed = list(urlparse.urlparse(url))
            parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one
            url = urlparse.urlunparse(parsed)

            if sickbeard.PROXY_SETTING:
                proxies = {
                    "http": sickbeard.PROXY_SETTING,
                    "https": sickbeard.PROXY_SETTING,
                }

                r = self.session.get(url, proxies=proxies, verify=False)
            else:
                r = self.session.get(url, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u"Error loading "+self.name+" URL: " + ex(e), logger.ERROR)
            return None

        if r.status_code != 200:
            logger.log(self.name + u" page requested with url " + url +" returned status code is " + str(r.status_code) + ': ' + clients.http_error_code[r.status_code], logger.WARNING)
            return None

        return r.content

    def findPropers(self, search_date=datetime.datetime.today()):

        results = []

        sqlResults = db.DBConnection().select('SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
                                              ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
                                              ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
                                              ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
                                              ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
                                              )
        if not sqlResults:
            return []

        for sqlshow in sqlResults:
            self.show = curshow = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            curEp = curshow.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))

            searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

            for item in self._doSearch(searchString[0]):
                title, url = self._get_title_and_url(item)
                results.append(classes.Proper(title, url, datetime.datetime.today()))

        return results


class SpeedCDCache(tvcache.TVCache):

    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll Speedcd every 20 minutes max
        self.minTime = 20

    def updateCache(self):

        if not self.shouldUpdate():
            return

        search_params = {'RSS': ['']}
        rss_results = self.provider._doSearch(search_params)

        if rss_results:
            self.setLastUpdate()
        else:
            return []

        logger.log(u"Clearing " + self.provider.name + " cache and updating with new information")
        self._clearCache()

        ql = []
        for result in rss_results:
            item = (result[0], result[1])
            ci = self._parseItem(item)
            if ci is not None:
                ql.append(ci)

        myDB = self._getDB()
        myDB.mass_action(ql)

    def _parseItem(self, item):

        (title, url) = item

        if not title or not url:
            return None

        logger.log(u"Adding item to cache: " + title, logger.DEBUG)

        return self._addCacheEntry(title, url)

provider = SpeedCDProvider()

