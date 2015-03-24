# Author: Idan Gutman
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

import re
import traceback
import datetime
import urlparse
import sickbeard
import generic
import urllib
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
from sickbeard.bs4_parser import BS4Parser
from lib.unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName


class HoundDawgsProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "HoundDawgs")

        self.supportsBacklog = True

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = HoundDawgsCache(self)
		
        self.urls = {'base_url': 'https://hounddawgs.org/',
		        'search': 'https://hounddawgs.org/torrents.php?type=&userid=&searchstr=%s&searchimdb=&searchtags=&order_by=s3&order_way=desc&%s',
                'login': 'https://hounddawgs.org/login.php',
        }

        self.url = self.urls['base_url']

        self.categories = "&filter_cat[85]=1&filter_cat[58]=1&filter_cat[57]=1&filter_cat[74]=1&filter_cat[92]=1&filter_cat[93]=1"

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'hounddawgs.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'keeplogged': 'on',
                        'login': 'Login',
        }

        self.session = requests.Session()

        try:
            self.session.get(self.urls['base_url'], timeout=30, verify=False)
            response = self.session.post(self.urls['login'], data=login_params, timeout=30, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
            return False

        if re.search('Dit brugernavn eller kodeord er forkert.', response.text) \
                or re.search('<title>Login :: HoundDawgs</title>', response.text) \
                or re.search('Dine cookies er ikke aktiveret.', response.text) \
                or response.status_code == 401:
            logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
            return False

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

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
		
            for search_string in search_params[mode]:

                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                #if mode == 'RSS':
                    #searchURL = self.urls['index'] % self.categories
                #else:
                searchURL = self.urls['search'] % (urllib.quote(search_string), self.categories)

                logger.log(u"Search string: " + searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                strTableStart = "<table class=\"torrent_table"
                startTableIndex=data.find(strTableStart)
                trimmedData = data[startTableIndex:]
                if not trimmedData:
                    continue

                try:
                    with BS4Parser(trimmedData, features=["html5lib", "permissive"]) as html:
                        result_table = html.find('table', {'id': 'torrent_table'})
        
                        if not result_table:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.DEBUG)
                            continue
                        
                        result_tbody = result_table.find('tbody')
                        entries = result_tbody.contents
                        del entries[1::2]   

                        for result in entries[1:]:
                            
                            torrent = result.find_all('td')
                            if len(torrent) <= 1:
                                break
                            
                            allAs = (torrent[1]).find_all('a')

                            try:
                                link = self.urls['base_url'] + allAs[2].attrs['href']
                                #url = result.find('td', attrs={'class': 'quickdownload'}).find('a')
                                title = allAs[2].string
                                #Trimming title so accepted by scene check(Feature has been rewuestet i forum)
                                title = title.replace("custom.", "")
                                title = title.replace("CUSTOM.", "")
                                title = title.replace("Custom.", "")
                                title = title.replace("dk", "")
                                title = title.replace("DK", "")
                                title = title.replace("Dk", "")
                                title = title.replace("subs.", "")
                                title = title.replace("SUBS.", "")
                                title = title.replace("Subs.", "")
                                
                                download_url = self.urls['base_url']+allAs[0].attrs['href']
                                id = link.replace(self.urls['base_url']+'torrents.php?id=','')
                                
                            except (AttributeError, TypeError):
                                continue

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
            title = u'' + title
            title = title.replace(' ', '.')

        if url:
            url = str(url).replace('&amp;', '&')

        return (title, url)

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


class HoundDawgsCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll HoundDawgs every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = HoundDawgsProvider()
