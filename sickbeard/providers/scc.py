# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import re
import traceback
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
from bs4 import BeautifulSoup
from lib.unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName


class SCCProvider(generic.TorrentProvider):
    urls = {'base_url': 'https://sceneaccess.eu',
            'login': 'https://sceneaccess.eu/login',
            'detail': 'https://www.sceneaccess.eu/details?id=%s',
            'search': 'https://sceneaccess.eu/browse?search=%s&method=1&%s',
            'nonscene': 'https://sceneaccess.eu/nonscene?search=%s&method=1&c44=44&c45=44',
            'foreign': 'https://sceneaccess.eu/foreign?search=%s&method=1&c34=34&c33=33',
            'archive': 'https://sceneaccess.eu/archive?search=%s&method=1&c26=26',
            'download': 'https://www.sceneaccess.eu/%s',
    }

    def __init__(self):

        generic.TorrentProvider.__init__(self, "SceneAccess")

        self.supportsBacklog = True

        self.cache = SCCCache(self)

        self.url = self.urls['base_url']

        self.categories = "c27=27&c17=17&c11=11"

        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36'}

    def isEnabled(self):
        return sickbeard.SCC

    def imageName(self):
        return 'scc.png'

    def getQuality(self, item):

        quality = Quality.sceneQuality(item[0])
        return quality

    def _doLogin(self):

        login_params = {'username': sickbeard.SCC_USERNAME,
                        'password': sickbeard.SCC_PASSWORD,
                        'submit': 'come on in',
        }

        self.session = requests.Session()

        try:
            response = self.session.post(self.urls['login'], data=login_params, headers=self.headers, timeout=30, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
            return False

        if re.search('Username or password incorrect', response.text) \
                or re.search('<title>SceneAccess \| Login</title>', response.text) \
                or response.status_code == 401:
            logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
            return False

        return True

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': [], 'Episode': []}
        if not (ep_obj.show.air_by_date or ep_obj.show.sports):
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)  #1) showName SXX
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
                ep_string = show_name_helpers.sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode}

                search_string['Episode'].append(re.sub('\s+', ' ', ep_string))

        return [search_string]

    def _doSearch(self, search_params, show=None, age=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return []

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                if mode == 'Season':
                    searchURL = self.urls['archive'] % (search_string)
                    data = [self.getURL(searchURL, headers=self.headers)]
                else:
                    searchURL = self.urls['search'] % (search_string, self.categories)
                    nonsceneSearchURL = self.urls['nonscene'] % (search_string)
                    foreignSearchURL = self.urls['foreign'] % (search_string)
                    data = [self.getURL(searchURL, headers=self.headers),
                            self.getURL(nonsceneSearchURL, headers=self.headers),
                            self.getURL(foreignSearchURL, headers=self.headers)]
                    logger.log(u"Search string: " + nonsceneSearchURL, logger.DEBUG)
                    logger.log(u"Search string: " + foreignSearchURL, logger.DEBUG)

                logger.log(u"Search string: " + searchURL, logger.DEBUG)

                if not data:
                    continue

                try:
                    for dataItem in data:
                        html = BeautifulSoup(dataItem, features=["html5lib", "permissive"])

                        torrent_table = html.find('table', attrs={'id': 'torrents-table'})
                        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                        #Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            if html.title:
                                source = self.name + " (" + html.title.string + ")"
                            else:
                                source = self.name
                            logger.log(u"The Data returned from " + source + " does not contain any torrent", logger.DEBUG)
                            continue

                        for result in torrent_table.find_all('tr')[1:]:

                            try:
                                link = result.find('td', attrs={'class': 'ttr_name'}).find('a')
                                url = result.find('td', attrs={'class': 'td_dl'}).find('a')
                                title = link.string
                                if re.search('\.\.\.', title):
                                    details_html = BeautifulSoup(self.getURL(self.url + "/" + link['href']))
                                    title = re.search('(?<=").+(?<!")', details_html.title.string).group(0)
                                download_url = self.urls['download'] % url['href']
                                id = int(link['href'].replace('details?id=', ''))
                                seeders = int(result.find('td', attrs={'class': 'ttr_seeders'}).string)
                                leechers = int(result.find('td', attrs={'class': 'ttr_leechers'}).string)
                            except (AttributeError, TypeError):
                                continue

                            if mode != 'RSS' and seeders == 0:
                                continue

                            if not title or not download_url:
                                continue

                            item = title, download_url, id, seeders, leechers

                            if re.search('<title>SceneAccess \| Non-Scene</title>', dataItem):
                                logger.log(u"Found result: " + title + "(" + nonsceneSearchURL + ")", logger.DEBUG)
                            elif re.search('<title>SceneAccess \| Foreign</title>', dataItem):
                                logger.log(u"Found result: " + title + "(" + foreignSearchURL + ")", logger.DEBUG)
                            else:
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
            headers = {}

        try:
            # Remove double-slashes from url
            parsed = list(urlparse.urlparse(url))
            parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one
            url = urlparse.urlunparse(parsed)

            response = self.session.get(url, headers=headers, verify=False)
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

        sqlResults = db.DBConnection().select(
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
            curEp = curshow.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))

            searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

            for item in self._doSearch(searchString[0]):
                title, url = self._get_title_and_url(item)
                results.append(classes.Proper(title, url, datetime.datetime.today()))

        return results


class SCCCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll SCC every 10 minutes max
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

        cl = []
        for result in rss_results:
            item = (result[0], result[1])
            ci = self._parseItem(item)
            if ci is not None:
                cl.append(ci)

        if len(cl) > 0:
            myDB = self._getDB()
            myDB.mass_action(cl)

    def _parseItem(self, item):

        (title, url) = item

        if not title or not url:
            return None

        logger.log(u"Adding item to cache: " + title, logger.DEBUG)

        return self._addCacheEntry(title, url)


provider = SCCProvider()
