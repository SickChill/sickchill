# -*- coding: latin-1 -*-
# Authors: Raver2046
#          adaur
# based on tpi.py
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
import datetime
import sickbeard
import generic

import requests
import cookielib
import urllib

from sickbeard.bs4_parser import BS4Parser
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard import helpers
from sickbeard import classes
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName
from sickbeard.exceptions import ex

class LibertaliaProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "Libertalia")

        self.supportsBacklog = True

        self.cj = cookielib.CookieJar()

        self.url = "https://libertalia.me"
        self.urlsearch = "https://libertalia.me/torrents.php?name=%s%s"

        self.categories = "&cat%5B%5D=9"

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'libertalia.png'

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + '.' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + '.' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + '.S%02d' % int(ep_obj.scene_season)  # 1) showName.SXX

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
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string

                search_string['Episode'].append(re.sub('\s+', '.', ep_string))

        return [search_string]

    def getQuality(self, item, anime=False):
        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                            'password': self.password
        }

        logger.log('Performing authentication to Libertalia', logger.DEBUG)
        response = self.getURL(self.url + '/login.php',  post_data=login_params, timeout=30)
        if not response:
            logger.log(u'Unable to connect to ' + self.name + ' provider.', logger.ERROR)
            return False

        if re.search('upload.php', response):
            logger.log(u'Login to ' + self.name + ' was successful.', logger.DEBUG)
            return True
        else:
            logger.log(u'Login to ' + self.name + ' was unsuccessful.', logger.DEBUG)
            return False

        return True


    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        logger.log(u"_doSearch started with ..." + str(search_params), logger.DEBUG)

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self._doLogin():
            return results

        for mode in search_params.keys():

            for search_string in search_params[mode]:

                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                searchURL = self.urlsearch % (urllib.quote(search_string), self.categories)

                logger.log(u"Search string: " + searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data:
                    continue

                with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                    resultsTable = html.find("table", { "class" : "torrent_table"  })
                    if resultsTable:
                        logger.log(u"Libertalia found result table ! " , logger.DEBUG)
                        rows = resultsTable.findAll("tr" ,  {"class" : "torrent_row  new  "}  )  # torrent_row new

                        for row in rows:

                            #bypass first row because title only
                            columns = row.find('td', {"class" : "torrent_name"} )
                            logger.log(u"Libertalia found rows ! " , logger.DEBUG)
                            isvfclass = row.find('td', {"class" : "sprite-vf"} )
                            isvostfrclass = row.find('td', {"class" : "sprite-vostfr"} )
                            link = columns.find("a",  href=re.compile("torrents"))
                            if link:
                                title = link.text
                                recherched=searchURL.replace(".","(.*)").replace(" ","(.*)").replace("'","(.*)")
                                logger.log(u"Libertalia title : " + title, logger.DEBUG)
                                downloadURL =  row.find("a",href=re.compile("torrent_pass"))['href']
                                logger.log(u"Libertalia download URL : " + downloadURL, logger.DEBUG)
                                item = title, downloadURL
                                items[mode].append(item)
            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

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
                search_params = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

                for item in self._doSearch(search_params[0]):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def _get_title_and_url(self, item):

        title, url = item

        if title:
            title = u'' + title
            title = title.replace(' ', '.')

        if url:
            url = str(url).replace('&amp;', '&')

        return (title, url)

provider = LibertaliaProvider()
