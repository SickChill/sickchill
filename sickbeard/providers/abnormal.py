# -*- coding: latin-1 -*-
# Author: Mybug
#
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
import sickbeard, generic

import requests, cookielib, urllib

from sickbeard.bs4_parser import BS4Parser
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard import helpers
from sickbeard import classes
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName


class ABNormalProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "ABNormal")

        self.supportsBacklog = True
        self.public = False

        self.cj = cookielib.CookieJar()

        self.url = "http://abnormal.ws"
        self.urlsearch = "http://abnormal.ws/torrents.php?search=%s%s"


        self.categories = "&cat%5B%5D=TV%7CSD%7CVOSTFR&cat%5B%5D=TV%7CHD%7CVOSTFR"
        self.categories += "&cat%5B%5D=TV%7CSD%7CVF&cat%5B%5D=TV%7CHD%7CVF"

        self.enabled = False
        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'abnormal.png'

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

        login_params = {'username': self.username, 'password': self.password}

        logger.log('Performing authentication to abnormal', logger.DEBUG)
        response = self.getURL(self.url+'/login.php', post_data=login_params, timeout=30)

        if not response:
            logger.log(u'Unable to connect to '+self.name+' provider.', logger.ERROR)
            return False

        if('<span class="warning">' in str(response)):
            logger.log(u'Impossible to login to '+self.name, logger.ERROR)
            return False
        else:
            logger.log(u'Successful login for '+self.name, logger.ERROR)
            return True

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        logger.log(u"_doSearch started with ..." + str(search_params), logger.DEBUG)

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

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
                    resultsTable = html.find_all("tr")

                    for row in resultsTable:
                        tmp = row.find_all("a", {"class" : "tooltip"})

                        # Check if the current tr div is a torrent
                        if not tmp or tmp == None:
                            continue

                        ### Get download link
                        # <a class="tooltip" href="torrents.php?action=download&id=
                        tmp = row.find('a', {"href" : re.compile(".*torrents\.php\?action=download&id=.*")})
                        url = "{}/{}".format(self.url, tmp['href'])

                        ### Get title
                        # <a href="torrents.php?id=
                        tmp = row.find("a", {"href" : re.compile(".*torrents.\php\?id=[0-9]{0,}.*")})
                        title = tmp.string

                        ### Get seeders & leechers
                        # <td style="color:red;">
                        tmp = row.find("td", { "style" : "color:green;" })
                        seeders = tmp.string

                        tmp = row.find("td", { "style" : "color:red;" })
                        leechers = tmp.string

                        ### Check seeders and leechers filters
                        if int(seeders) < self.minseed or int(leechers) < self.minleech:
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(str(title), str(seeders), str(leechers)), logger.ERROR)
                            continue

                        ### Format and add formated item
                        item = title, url, seeders, leechers
                        items[mode].append(item)

            ### Add show
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

        title, url, seeders, leechers = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

provider = ABNormalProvider()
