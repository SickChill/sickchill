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
import time
import re
import datetime
import sickbeard
import generic
import cookielib
import urllib
import urllib2

from lib import requests
from lib.requests import exceptions

from sickbeard.common import USER_AGENT, Quality, cpu_presets
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard.bs4_parser import BS4Parser
from sickbeard import db
from sickbeard import helpers
from sickbeard import classes
from sickbeard.helpers import sanitizeSceneName
from sickbeard.exceptions import ex


class RarbgProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "Rarbg")

        self.supportsBacklog = True
        self.enabled = False

        self.cache = RarbgCache(self)

        self.ratio = None

        self.cookies = cookielib.CookieJar()
	self.cookie = cookielib.Cookie(version=0, name='7fAY799j', value='VtdTzG69', port=None, port_specified=False, domain='rarbg.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
	self.cookies.set_cookie(self.cookie)
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies))
        self.opener.addheaders=[('User-agent', 'Mozilla/5.0')]

        self.urls = {'base_url': 'https://rarbg.com/torrents.php',
                'search': 'https://rarbg.com/torrents.php?search=%s&category[]=%s',
                'download': 'https://rarbg.com/download.php?id=%s&f=%s',
                }

        self.url = self.urls['base_url']

        self.subcategories = [41] #18


    def getURL(self, url, post_data=None, params=None, timeout=30, json=False):
        logger.log(u"Rarbg downloading url :" + url, logger.DEBUG)
	request = urllib2.Request(url)
	content = self.opener.open(request)
	return content.read()


    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'rarbg.png'

    def getQuality(self, item, anime=False):
        quality = Quality.sceneQuality(item[0], anime)
        return quality

#    def _doLogin(self):
#        login_params = {'login': self.username,
#                        'password': self.password,
#        }
#
#        self.session = requests.Session()
#
#        try:
#            response = self.session.post(self.urls['login_page'], data=login_params, timeout=30, verify=False)
#            response = self.session.get(self.urls['base_url'], timeout=30, verify=False)
#        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
#            logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
#            return False
#
#        if not re.search('/users/logout/', response.text.lower()):
#            logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
#            return False
#
#        return True

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + '.' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + '.' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + '.S%02d' % int(ep_obj.scene_season)  #1) showName.SXX

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) + '.' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string

                search_string['Episode'].append(re.sub('\s+', '.', ep_string))

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

	# Get cookie
	#dummy = self.getURL(self.url)

#        if not self._doLogin():
#            return results

        for mode in search_params.keys():

            for search_string in search_params[mode]:

                for sc in self.subcategories:
                    searchURL = self.urls['search'] % (urllib.quote(search_string), sc)
                    logger.log(u"" + self.name + " search page URL: " + searchURL, logger.DEBUG)

                    data = self.getURL(searchURL)
                    if not data:
                        continue

                    try:
                        with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                            resultsTable = html.find('table', attrs={'class': 'lista2t'})

                            if not resultsTable:
                                logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                           logger.DEBUG)
                                continue

                            entries = resultsTable.find("tbody").findAll("tr")

                            if len(entries) > 0:
                                for result in entries:

                                    try:
                                        link = result.find('a', title=True)
                                        torrentName = link['title']
                                        torrent_name = str(torrentName)
                                        torrentId = result.find_all('td')[1].find_all('a')[0]['href'][1:].replace(
                                            'torrent/', '')
                                        torrent_download_url = (self.urls['download'] % (torrentId, torrent_name + '-[rarbg.com].torrent')).encode('utf8')
                                    except (AttributeError, TypeError):
                                        continue

                                    if not torrent_name or not torrent_download_url:
                                        continue

                                    item = torrent_name, torrent_download_url
                                    logger.log(u"Found result: " + torrent_name + " (" + torrent_download_url + ")",
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

class RarbgCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # Only poll Rarbg every 30 minutes max
        self.minTime = 30

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = RarbgProvider()
