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

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None

        self.cache = NextGenCache(self)

        self.urls = {'base_url': 'https://nxtgn.org/',
                'search': 'https://nxtgn.org/browse.php?search=%s&cat=0&incldead=0&modes=%s',
                'login_page': 'https://nxtgn.org/login.php',
                'detail': 'https://nxtgn.org/details.php?id=%s',
                'download': 'https://nxtgn.org/download.php?id=%s',
                'takelogin': 'https://nxtgn.org/takelogin.php?csrf=',
                }

        self.url = self.urls['base_url']

        self.categories = '&c7=1&c24=1&c17=1&c22=1&c42=1&c46=1&c26=1&c28=1&c43=1&c4=1&c31=1&c45=1&c33=1'

        self.last_login_check = None

        self.login_opener = None

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'nextgen.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

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
        logger.log(u'Failed to login:' + str(error), logger.ERROR)
        return False

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
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string

                search_string['Episode'].append(re.sub(r'\s+', ' ', ep_string))

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():

            for search_string in search_params[mode]:

                searchURL = self.urls['search'] % (urllib.quote(search_string.encode('utf-8')), self.categories)
                logger.log(u"" + self.name + " search page URL: " + searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    with BS4Parser(data.decode('iso-8859-1'), features=["html5lib", "permissive"]) as html:
                        resultsTable = html.find('div', attrs={'id': 'torrent-table-wrapper'})

                        if not resultsTable:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.DEBUG)
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
                                    torrent_name = str(torrentName)
                                    torrent_download_url = (self.urls['download'] % torrentId).encode('utf8')
                                    torrent_details_url = (self.urls['detail'] % torrentId).encode('utf8')
                                    #torrent_seeders = int(result.find('div', attrs = {'id' : 'torrent-seeders'}).find('a')['class'][0])
                                    ## Not used, perhaps in the future ##
                                    #torrent_id = int(torrent['href'].replace('/details.php?id=', ''))
                                    #torrent_leechers = int(result.find('td', attrs = {'class' : 'ac t_leechers'}).string)
                                except (AttributeError, TypeError):
                                    continue

                                # Filter unseeded torrent and torrents with no name/url
                                #if mode != 'RSS' and torrent_seeders == 0:
                                #    continue

                                if not torrent_name or not torrent_download_url:
                                    continue

                                item = torrent_name, torrent_download_url
                                logger.log(u"Found result: " + torrent_name.replace(' ','.') + " (" + torrent_details_url + ")",
                                           logger.DEBUG)
                                items[mode].append(item)

                        else:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.WARNING)
                            continue

                except Exception, e:
                    logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(),
                               logger.ERROR)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url = item

        if title:
            title = u'' + title
            title = title.replace(' ', '.')

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


class NextGenCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # Only poll NextGen every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = NextGenProvider()
