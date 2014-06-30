# Author: Mr_Orange <mr_orange@hotmail.it>
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

from __future__ import with_statement

import time
import sys
import os
import traceback
import urllib, urlparse
import re
import datetime

import sickbeard
import generic

from sickbeard.common import Quality, cpu_presets
from sickbeard.name_parser.parser import NameParser, InvalidNameException
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard import db
from sickbeard import classes
from sickbeard.show_name_helpers import allPossibleShowNames, sanitizeSceneName
from sickbeard.exceptions import ex
from sickbeard import encodingKludge as ek
from sickbeard import clients

from lib import requests
from lib.requests import exceptions
from bs4 import BeautifulSoup
from lib.unidecode import unidecode


class PublicHDProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "PublicHD")

        self.supportsBacklog = True

        self.enabled = False
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = PublicHDCache(self)

        self.url = 'http://phdproxy.com/'

        self.searchurl = self.url + 'index.php?page=torrents&search=%s&active=0&category=%s&order=5&by=2'  #order by seed

        self.categories = {'Season': ['23'], 'Episode': ['7', '14', '24'], 'RSS': ['7', '14', '23', '24']}

    def __del__(self):
        pass

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'publichd.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _get_season_search_strings(self, ep_obj):
        search_string = {'Season': []}

        for show_name in set(allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + str(ep_obj.airdate).split('-')[0]
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)  #1) showName SXX -SXXE
            search_string['Season'].append(ep_string)

            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' Season ' + str(ep_obj.airdate).split('-')[0]
            else:
                ep_string = show_name + ' Season ' + str(ep_obj.scene_season)  #2) showName Season X
            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode}

                for x in add_string.split('|'):
                    to_search = re.sub('\s+', ' ', ep_string + ' %s' % x)
                    search_string['Episode'].append(to_search)

        return [search_string]

    def _doSearch(self, search_params, epcount=0, age=0):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                if mode == 'RSS':
                    searchURL = self.url + 'index.php?page=torrents&active=1&category=%s' % (
                        ';'.join(self.categories[mode]))
                    logger.log(u"PublicHD cache update URL: " + searchURL, logger.DEBUG)
                else:
                    searchURL = self.searchurl % (
                        urllib.quote(unidecode(search_string)), ';'.join(self.categories[mode]))
                    logger.log(u"Search string: " + searchURL, logger.DEBUG)

                html = self.getURL(searchURL)

                if not html:
                    continue

                #remove unneccecary <option> lines which are slowing down BeautifulSoup
                optreg = re.compile(r'<option.*</option>')
                html = os.linesep.join([s for s in html.splitlines() if not optreg.search(s)])

                try:
                    soup = BeautifulSoup(html, features=["html5lib", "permissive"])

                    torrent_table = soup.find('table', attrs={'id': 'torrbg'})
                    torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                    #Continue only if one Release is found
                    if len(torrent_rows) < 2:
                        logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                   logger.DEBUG)
                        continue

                    for tr in torrent_rows[1:]:

                        try:
                            link = self.url + tr.find(href=re.compile('page=torrent-details'))['href']
                            title = tr.find(lambda x: x.has_attr('title')).text.replace('_', '.')
                            url = tr.find(href=re.compile('magnet+'))['href']
                            seeders = int(tr.find_all('td', {'class': 'header'})[4].text)
                            leechers = int(tr.find_all('td', {'class': 'header'})[5].text)
                        except (AttributeError, TypeError):
                            continue

                        if mode != 'RSS' and (seeders == 0 or seeders < self.minseed or leechers < self.minleech):
                            continue

                        if not title or not url:
                            continue

                        item = title, url, link, seeders, leechers

                        items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed to parsing " + self.name + " Traceback: " + traceback.format_exc(),
                               logger.ERROR)

            #For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url, id, seeders, leechers = item

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

    def getURL(self, url, post_data=None, headers=None, json=False):

        if not self.session:
            self.session = requests.Session()

        try:
            # Remove double-slashes from url
            parsed = list(urlparse.urlparse(url))
            parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one
            url = urlparse.urlunparse(parsed)

            r = self.session.get(url, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u"Error loading " + self.name + " URL: " + str(sys.exc_info()) + " - " + ex(e), logger.ERROR)
            return None

        if r.status_code != 200:
            logger.log(self.name + u" page requested with url " + url + " returned status code is " + str(
                r.status_code) + ': ' + clients.http_error_code[r.status_code], logger.WARNING)
            return None

        return r.content

    def downloadResult(self, result):
        """
        Save the result to disk.
        """

        if not self.session:
            self.session = requests.Session()

        torrent_hash = re.findall('urn:btih:([\w]{32,40})', result.url)[0].upper()

        if not torrent_hash:
            logger.log("Unable to extract torrent hash from link: " + ex(result.url), logger.ERROR)
            return False

        try:
            r = self.session.get('http://torcache.net/torrent/' + torrent_hash + '.torrent', verify=False)
        except Exception, e:
            logger.log("Unable to connect to TORCACHE: " + ex(e), logger.ERROR)
            try:
                logger.log("Trying TORRAGE cache instead")
                r = self.session.get('http://torrage.com/torrent/' + torrent_hash + '.torrent', verify=False)
            except Exception, e:
                logger.log("Unable to connect to TORRAGE: " + ex(e), logger.ERROR)
                return False

        if not r.status_code == 200:
            return False

        magnetFileName = ek.ek(os.path.join, sickbeard.TORRENT_DIR,
                               helpers.sanitizeFileName(result.name) + '.' + self.providerType)
        magnetFileContent = r.content

        try:
            with open(magnetFileName, 'wb') as fileOut:
                fileOut.write(magnetFileContent)

            helpers.chmodAsParent(magnetFileName)

        except EnvironmentError, e:
            logger.log("Unable to save the file: " + ex(e), logger.ERROR)
            return False

        logger.log(u"Saved magnet link to " + magnetFileName + " ", logger.MESSAGE)
        return True

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


class PublicHDCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll ThePirateBay every 10 minutes max
        self.minTime = 20

    def __del__(self):
        pass

    def updateCache(self):

        # delete anything older then 7 days
        logger.log(u"Clearing " + self.provider.name + " cache")
        self._clearCache()

        if not self.shouldUpdate():
            return

        search_params = {'RSS': ['rss']}
        rss_results = self.provider._doSearch(search_params)

        if rss_results:
            self.setLastUpdate()
        else:
            return []

        ql = []
        for result in rss_results:

            item = (result[0], result[1])
            ci = self._parseItem(item)
            if ci is not None:
                ql.append(ci)

        if ql:
            myDB = self._getDB()
            myDB.mass_action(ql)


    def _parseItem(self, item):

        (title, url) = item

        if not title or not url:
            return None

        logger.log(u"Attempting to cache item:[" + title +"]", logger.DEBUG)

        return self._addCacheEntry(title, url)


provider = PublicHDProvider()
