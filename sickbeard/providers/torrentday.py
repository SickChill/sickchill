# Author: Mr_Orange <mr_orange@hotmail.it>
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import time
import json
import re
import traceback
import datetime
import urlparse
import sickbeard
import generic
from sickbeard.common import Quality, cpu_presets
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
from bs4 import BeautifulSoup
from lib.unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName


class TorrentDayProvider(generic.TorrentProvider):
    urls = {'base_url': 'http://www.torrentday.com',
            'login': 'http://www.torrentday.com/torrents/',
            'search': 'http://www.torrentday.com/V3/API/API.php',
            'download': 'http://www.torrentday.com/download.php/%s/%s'
    }

    def __init__(self):

        generic.TorrentProvider.__init__(self, "TorrentDay")

        self.supportsBacklog = True

        self.enabled = False
        self.uid = None
        self.hash = None
        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.cache = TorrentDayCache(self)

        self.url = self.urls['base_url']

        self.cookies = None

        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1},
                           'RSS': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c14': 1}}

    def __del__(self):
        pass

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'torrentday.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        if self.uid and self.hash:

            requests.utils.add_dict_to_cookiejar(self.session.cookies, self.cookies)

        else:

            login_params = {'username': self.username,
                            'password': self.password,
                            'submit.x': 0,
                            'submit.y': 0
            }

            try:
                response = self.session.post(self.urls['login'], data=login_params, timeout=30)
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
                logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
                return False

            if re.search('You tried too often', response.text):
                logger.log(u'Too many login access for ' + self.name + ', can''t retrive any data', logger.ERROR)
                return False

            if response.status_code == 401:
                logger.log(u'Invalid username or password for ' + self.name + ', Check your settings!', logger.ERROR)
                return False

            if requests.utils.dict_from_cookiejar(self.session.cookies)['uid'] and requests.utils.dict_from_cookiejar(self.session.cookies)['pass']:
                self.uid = requests.utils.dict_from_cookiejar(self.session.cookies)['uid']
                self.hash = requests.utils.dict_from_cookiejar(self.session.cookies)['pass']

                self.cookies = {'uid': self.uid,
                                'pass': self.hash
                }
                return True

            else:
                logger.log(u'Unable to obtain cookie for TorrentDay', logger.ERROR)
                return False


    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
                search_string['Season'].append(ep_string)
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)  #1) showName SXX

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode}

                search_string['Episode'].append(re.sub('\s+', ' ', ep_string))

        return [search_string]

    def _doSearch(self, search_params, epcount=0, age=0):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        freeleech = '&free=on' if self.freeleech else ''

        if not self._doLogin():
            return []

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                logger.log(u"Search string: " + search_string, logger.DEBUG)

                search_string = '+'.join(search_string.split())

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 8, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                if self.freeleech:
                    post_data.update({'free': 'on'})

                data = self.session.post(self.urls['search'], data=post_data).json()

                try:
                    torrents = data.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
                except:
                    continue

                for torrent in torrents:

                    title = re.sub(r"\[.*\=.*\].*\[/.*\]", "", torrent['name'])
                    url = self.urls['download'] % ( torrent['id'], torrent['fname'] )
                    seeders = int(torrent['seed'])
                    leechers = int(torrent['leech'])

                    if mode != 'RSS' and (seeders == 0 or seeders < self.minseed or leechers < self.minleech):
                        continue

                    if not title or not url:
                        continue

                    item = title, url, seeders, leechers
                    items[mode].append(item)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url = item[0], item[1]

        if url:
            url = str(url).replace('&amp;', '&')

        return (title, url)

    def getURL(self, url, post_data=None, headers=None, json=False):

        if not self.session:
            self._doLogin()

        try:
            # Remove double-slashes from url
            parsed = list(urlparse.urlparse(url))
            parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one
            url = urlparse.urlunparse(parsed)

            response = self.session.get(url, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u"Error loading " + self.name + " URL: " + ex(e), logger.ERROR)
            return None

        if response.status_code != 200:
            logger.log(self.name + u" page requested with url " + url + " returned status code is " + str(
                response.status_code) + ': ' + clients.http_error_code[response.status_code], logger.WARNING)
            return None

        return response.content

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
                    results.append(classes.Proper(title, url, datetime.datetime.today()))

        return results

    def seedRatio(self):
        return self.ratio


class TorrentDayCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # Only poll IPTorrents every 10 minutes max
        self.minTime = 10

    def __del__(self):
        pass

    def updateCache(self):

        # delete anything older then 7 days
        logger.log(u"Clearing " + self.provider.name + " cache")
        self._clearCache()

        if not self.shouldUpdate():
            return

        search_params = {'RSS': ['']}
        rss_results = self.provider._doSearch(search_params)

        if rss_results:
            self.setLastUpdate()
        else:
            return []

        cl = []
        for result in rss_results:

            item = (result[0], result[1])
            ci = self._parseItem(item)
            if ci is not None:
                cl.append(ci)

        if cl:
            myDB = self._getDB()
            myDB.mass_action(cl)


    def _parseItem(self, item):

        (title, url) = item

        if not title or not url:
            return None

        logger.log(u"Attempting to cache item:[" + title +"]", logger.DEBUG)

        return self._addCacheEntry(title, url)


provider = TorrentDayProvider()
