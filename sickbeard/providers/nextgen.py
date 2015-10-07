# Author: seedboy
# URL: https://github.com/seedboy
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

import traceback
import urllib
import time
import re
import datetime
import sickbeard
import generic
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
import requests
from sickbeard.bs4_parser import BS4Parser
from sickbeard.helpers import sanitizeSceneName


class NextGenProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "NextGen")

        self.supportsBacklog = True
        self.public = False

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None

        self.cache = NextGenCache(self)

        self.urls = {'base_url': 'https://nxgn.org/',
                'search': 'https://nxgn.org/browse.php?search=%s&cat=0&incldead=0&modes=%s',
                'login_page': 'https://nxgn.org/login.php',
                'detail': 'https://nxgn.org/details.php?id=%s',
                'download': 'https://nxgn.org/download.php?id=%s',
                'takelogin': 'https://nxgn.org/takelogin.php?csrf=',
                }

        self.url = self.urls['base_url']

        self.categories = '&c7=1&c24=1&c17=1&c22=1&c42=1&c46=1&c26=1&c28=1&c43=1&c4=1&c31=1&c45=1&c33=1'

        self.last_login_check = None

        self.login_opener = None

    def isEnabled(self):
        return self.enabled

    def getLoginParams(self):
        return {
            'username': self.username,
            'password': self.password,
        }

    def loginSuccess(self, output):
        if "<title>NextGen - Login</title>" in output:
            return False
        else:
            return True

    def _doLogin(self):

        now = time.time()
        if self.login_opener and self.last_login_check < (now - 3600):
            try:
                output = self.getURL(self.urls['test'])
                if self.loginSuccess(output):
                    self.last_login_check = now
                    return True
                else:
                    self.login_opener = None
            except:
                self.login_opener = None

        if self.login_opener:
            return True

        try:
            login_params = self.getLoginParams()
            data = self.getURL(self.urls['login_page'])
            with BS4Parser(data) as bs:
                csrfraw = bs.find('form', attrs={'id': 'login'})['action']
                output = self.getURL(self.urls['base_url'] + csrfraw, post_data=login_params)

                if self.loginSuccess(output):
                    self.last_login_check = now
                    self.login_opener = self.session
                    return True

                error = 'unknown'
        except:
            error = traceback.format_exc()
            self.login_opener = None

        self.login_opener = None
        logger.log(u"Failed to login: %s" % error, logger.ERROR)
        return False

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urls['search'] % (urllib.quote(search_string.encode('utf-8')), self.categories)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG) 
                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    with BS4Parser(data.decode('iso-8859-1'), features=["html5lib", "permissive"]) as html:
                        resultsTable = html.find('div', attrs={'id': 'torrent-table-wrapper'})

                        if not resultsTable:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        # Collecting entries
                        entries_std = html.find_all('div', attrs={'id': 'torrent-std'})
                        entries_sticky = html.find_all('div', attrs={'id': 'torrent-sticky'})

                        entries = entries_std + entries_sticky

                        #Xirg STANDARD TORRENTS
                        #Continue only if one Release is found
                        if len(entries) > 0:

                            for result in entries:

                                try:
                                    torrentName = \
                                    ((result.find('div', attrs={'id': 'torrent-udgivelse2-users'})).find('a'))['title']
                                    torrentId = (
                                    ((result.find('div', attrs={'id': 'torrent-download'})).find('a'))['href']).replace(
                                        'download.php?id=', '')
                                    title = str(torrentName)
                                    download_url = (self.urls['download'] % torrentId).encode('utf8')
                                    torrent_details_url = (self.urls['detail'] % torrentId).encode('utf8')
                                    seeders = int(result.find('div', attrs = {'id' : 'torrent-seeders'}).find('a')['class'][0])
                                    ## Not used, perhaps in the future ##
                                    #torrent_id = int(torrent['href'].replace('/details.php?id=', ''))
                                    leechers = int(result.find('td', attrs = {'class' : 'ac t_leechers'}).string)
                                    #FIXME
                                    size = -1
                                except (AttributeError, TypeError):
                                    continue

                                if not all([title, download_url]):
                                    continue

                                #Filter unseeded torrent
                                if seeders < self.minseed or leechers < self.minleech:
                                    if mode != 'RSS':
                                        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                    continue

                                item = title, download_url, size, seeders, leechers
                                if mode != 'RSS':
                                    logger.log(u"Found result: %s " % title, logger.DEBUG)

                                items[mode].append(item)

                        else:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                except Exception, e:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            #For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

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
                searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

                for item in self._doSearch(searchString[0]):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio


class NextGenCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # Only poll NextGen every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = NextGenProvider()
