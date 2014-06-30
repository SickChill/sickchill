# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import time
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


class HDTorrentsProvider(generic.TorrentProvider):
    urls = {'base_url': 'https://hdts.ru/index.php',
            'login': 'https://hdts.ru/login.php',
            'detail': 'https://www.hdts.ru/details.php?id=%s',
            'search': 'https://hdts.ru/torrents.php?search=%s&active=1&options=0%s',
            'download': 'https://www.sceneaccess.eu/%s',
            'home': 'https://www.hdts.ru/%s'
    }

    def __init__(self):

        generic.TorrentProvider.__init__(self, "HDTorrents")

        self.supportsBacklog = True

        self.enabled = False
        self.uid = None
        self.hash = None
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = HDTorrentsCache(self)

        self.url = self.urls['base_url']

        self.categories = "&category[]=59&category[]=60&category[]=30&category[]=38"

        self.cookies = None

    def __del__(self):
        pass

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'hdtorrents.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0])
        return quality

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        if self.uid and self.hash:

            requests.utils.add_dict_to_cookiejar(self.session.cookies, self.cookies)

        else:

            login_params = {'uid': self.username,
                            'pwd': self.password,
                            'submit': 'Confirm',
            }

            try:
                response = self.session.post(self.urls['login'], data=login_params, timeout=30)
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
                logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
                return False

            if re.search('You need cookies enabled to log in.', response.text) \
                    or response.status_code == 401:
                logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
                return False

            self.uid = requests.utils.dict_from_cookiejar(self.session.cookies)['uid']
            self.hash = requests.utils.dict_from_cookiejar(self.session.cookies)['pass']

            self.cookies = {'uid': self.uid,
                            'pass': self.hash
            }

        return True

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
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

        if not self._doLogin():
            return []

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                if search_string == '':
                    continue
                search_string = str(search_string).replace('.', ' ')
                searchURL = self.urls['search'] % (search_string, self.categories)

                logger.log(u"Search string: " + searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data:
                    continue

                # Remove HDTorrents NEW list
                split_data = data.partition('<!-- show New Torrents After Last Visit -->\n\n\n\n')
                data = split_data[2]

                try:
                    html = BeautifulSoup(data, features=["html5lib", "permissive"])

                    #Get first entry in table
                    entries = html.find_all('td', attrs={'align': 'center'})

                    if not entries:
                        logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                   logger.DEBUG)
                        continue

                    try:
                        title = entries[22].find('a')['title'].strip('History - ').replace('Blu-ray', 'bd50')
                        url = self.urls['home'] % entries[15].find('a')['href']
                        download_url = self.urls['home'] % entries[15].find('a')['href']
                        id = entries[23].find('div')['id']
                        seeders = int(entries[20].get_text())
                        leechers = int(entries[21].get_text())
                    except (AttributeError, TypeError):
                        continue

                    if mode != 'RSS' and (seeders == 0 or seeders < self.minseed or leechers < self.minleech):
                        continue

                    if not title or not download_url:
                        continue

                    item = title, download_url, id, seeders, leechers
                    logger.log(u"Found result: " + title + "(" + searchURL + ")", logger.DEBUG)

                    items[mode].append(item)

                    #Now attempt to get any others
                    result_table = html.find('table', attrs={'class': 'mainblockcontenttt'})

                    if not result_table:
                        continue

                    entries = result_table.find_all('td', attrs={'align': 'center', 'class': 'listas'})

                    if not entries:
                        continue

                    for result in entries:
                        block2 = result.find_parent('tr').find_next_sibling('tr')
                        if not block2:
                            continue
                        cells = block2.find_all('td')

                        try:
                            title = cells[1].find('b').get_text().strip('\t ').replace('Blu-ray', 'bd50')
                            url = self.urls['home'] % cells[4].find('a')['href']
                            download_url = self.urls['home'] % cells[4].find('a')['href']
                            detail = cells[1].find('a')['href']
                            id = detail.replace('details.php?id=', '')
                            seeders = int(cells[9].get_text())
                            leechers = int(cells[10].get_text())
                        except (AttributeError, TypeError):
                            continue

                        if mode != 'RSS' and (seeders == 0 or seeders < self.minseed or leechers < self.minleech):
                            continue

                        if not title or not download_url:
                            continue

                        item = title, download_url, id, seeders, leechers
                        logger.log(u"Found result: " + title + "(" + searchURL + ")", logger.DEBUG)

                        items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(), logger.ERROR)

            #For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url, id, seeders, leechers = item

        if url:
            url = str(url).replace('&amp;', '&')

        return (title, url)

    def getURL(self, url, post_data=None, headers=None, json=False):

        if not self.session:
            self._doLogin()

        if not headers:
            headers = []
        try:
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
            self.show = curshow = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if not self.show: continue
            curEp = curshow.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))

            searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

            for item in self._doSearch(searchString[0]):
                title, url = self._get_title_and_url(item)
                results.append(classes.Proper(title, url, datetime.datetime.today()))

        return results

    def seedRatio(self):
        return self.ratio


class HDTorrentsCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll HDTorrents every 10 minutes max
        self.minTime = 20

    def __del__(self):
        pass

    def updateCache(self):

        # delete anything older then 7 days
        logger.log(u"Clearing " + self.provider.name + " cache")
        self._clearCache()

        if not self.shouldUpdate():
            return

        search_params = {'RSS': []}
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


provider = HDTorrentsProvider()
