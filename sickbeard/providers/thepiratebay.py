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
import re
import urllib, urllib2, urlparse
import sys
import os
import datetime

import sickbeard
import generic
from sickbeard.common import Quality, cpu_presets
from sickbeard.name_parser.parser import NameParser, InvalidNameException
from sickbeard import db
from sickbeard import classes
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard import clients
from sickbeard.show_name_helpers import allPossibleShowNames, sanitizeSceneName
from sickbeard.common import Overview
from sickbeard.exceptions import ex
from sickbeard import encodingKludge as ek
from lib import requests
from lib.requests import exceptions
from lib.unidecode import unidecode


class ThePirateBayProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "ThePirateBay")

        self.supportsBacklog = True

        self.enabled = False
        self.ratio = None
        self.confirmed = False
        self.minseed = None
        self.minleech = None

        self.cache = ThePirateBayCache(self)

        self.proxy = ThePirateBayWebproxy()

        self.url = 'http://pirateproxy.net/'

        self.searchurl = self.url + 'search/%s/0/7/200'  # order by seed       

        self.re_title_url = '/torrent/(?P<id>\d+)/(?P<title>.*?)//1".+?(?P<url>magnet.*?)//1".+?(?P<seeders>\d+)</td>.+?(?P<leechers>\d+)</td>'

    def __del__(self):
        pass

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'thepiratebay.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _reverseQuality(self, quality):

        quality_string = ''

        if quality == Quality.SDTV:
            quality_string = 'HDTV x264'
        if quality == Quality.SDDVD:
            quality_string = 'DVDRIP'
        elif quality == Quality.HDTV:
            quality_string = '720p HDTV x264'
        elif quality == Quality.FULLHDTV:
            quality_string = '1080p HDTV x264'
        elif quality == Quality.RAWHDTV:
            quality_string = '1080i HDTV mpeg2'
        elif quality == Quality.HDWEBDL:
            quality_string = '720p WEB-DL h264'
        elif quality == Quality.FULLHDWEBDL:
            quality_string = '1080p WEB-DL h264'
        elif quality == Quality.HDBLURAY:
            quality_string = '720p Bluray x264'
        elif quality == Quality.FULLHDBLURAY:
            quality_string = '1080p Bluray x264'

        return quality_string

    def _find_season_quality(self, title, torrent_id, ep_number):
        """ Return the modified title of a Season Torrent with the quality found inspecting torrent file list """

        mediaExtensions = ['avi', 'mkv', 'wmv', 'divx',
                           'vob', 'dvr-ms', 'wtv', 'ts'
                                                   'ogv', 'rar', 'zip', 'mp4']

        quality = Quality.UNKNOWN

        fileName = None

        fileURL = self.proxy._buildURL(self.url + 'ajax_details_filelist.php?id=' + str(torrent_id))

        data = self.getURL(fileURL)
        if not data:
            return None

        filesList = re.findall('<td.+>(.*?)</td>', data)

        if not filesList:
            logger.log(u"Unable to get the torrent file list for " + title, logger.ERROR)

        videoFiles = filter(lambda x: x.rpartition(".")[2].lower() in mediaExtensions, filesList)

        #Filtering SingleEpisode/MultiSeason Torrent
        if len(videoFiles) < ep_number or len(videoFiles) > float(ep_number * 1.1):
            logger.log(
                u"Result " + title + " have " + str(ep_number) + " episode and episodes retrived in torrent are " + str(
                    len(videoFiles)), logger.DEBUG)
            logger.log(u"Result " + title + " Seem to be a Single Episode or MultiSeason torrent, skipping result...",
                       logger.DEBUG)
            return None

        if Quality.sceneQuality(title) != Quality.UNKNOWN:
            return title

        for fileName in videoFiles:
            quality = Quality.sceneQuality(os.path.basename(fileName))
            if quality != Quality.UNKNOWN: break

        if fileName is not None and quality == Quality.UNKNOWN:
            quality = Quality.assumeQuality(os.path.basename(fileName))

        if quality == Quality.UNKNOWN:
            logger.log(u"Unable to obtain a Season Quality for " + title, logger.DEBUG)
            return None

        try:
            myParser = NameParser()
            parse_result = myParser.parse(fileName)
        except InvalidNameException:
            return None

        logger.log(u"Season quality for " + title + " is " + Quality.qualityStrings[quality], logger.DEBUG)

        if parse_result.series_name and parse_result.season_number:
            title = parse_result.series_name + ' S%02d' % int(parse_result.season_number) + ' ' + self._reverseQuality(
                quality)

        return title

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
                search_string['Season'].append(ep_string)
                ep_string = show_name + ' Season ' + str(ep_obj.airdate).split('-')[0]
                search_string['Season'].append(ep_string)
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
                search_string['Season'].append(ep_string)
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season) + ' -S%02d' % int(
                    ep_obj.scene_season) + 'E' + ' category:tv'  #1) showName SXX -SXXE
                search_string['Season'].append(ep_string)
                ep_string = show_name + ' Season ' + str(
                    ep_obj.scene_season) + ' -Ep*' + ' category:tv'  # 2) showName Season X
                search_string['Season'].append(ep_string)

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

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
        elif self.show.anime:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + '|' + \
                            sickbeard.config.naming_ep_type[0] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string
                search_string['Episode'].append(re.sub('\s+', ' ', ep_string))

        return [search_string]

    def _doSearch(self, search_params, epcount=0, age=0):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    searchURL = self.proxy._buildURL(self.searchurl % (urllib.quote(unidecode(search_string))))
                else:
                    searchURL = self.proxy._buildURL(self.url + 'tv/latest/')

                logger.log(u"Search string: " + searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data:
                    continue

                re_title_url = self.proxy._buildRE(self.re_title_url)

                #Extracting torrent information from data returned by searchURL                   
                match = re.compile(re_title_url, re.DOTALL).finditer(urllib.unquote(data))
                for torrent in match:

                    title = torrent.group('title').replace('_',
                                                           '.')  #Do not know why but SickBeard skip release with '_' in name
                    url = torrent.group('url')
                    id = int(torrent.group('id'))
                    seeders = int(torrent.group('seeders'))
                    leechers = int(torrent.group('leechers'))

                    #Filter unseeded torrent
                    if mode != 'RSS' and (seeders == 0 or seeders < self.minseed or leechers < self.minleech):
                        continue

                        #Accept Torrent only from Good People for every Episode Search
                    if self.confirmed and re.search('(VIP|Trusted|Helper|Moderator)', torrent.group(0)) is None:
                        logger.log(u"ThePirateBay Provider found result " + torrent.group(
                            'title') + " but that doesn't seem like a trusted result so I'm ignoring it", logger.DEBUG)
                        continue

                    #Check number video files = episode in season and find the real Quality for full season torrent analyzing files in torrent 
                    if mode == 'Season':
                        ep_number = int(epcount / len(set(allPossibleShowNames(self.show))))
                        title = self._find_season_quality(title, id, ep_number)

                    if not title or not url:
                        continue

                    item = title, url, id, seeders, leechers

                    items[mode].append(item)

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

        if not headers:
            headers = {}

        if not self.session:
            self.session = requests.Session()

        # Glype Proxies does not support Direct Linking.
        # We have to fake a search on the proxy site to get data
        if self.proxy.isEnabled():
            headers.update({'referer': self.proxy.getProxyURL()})
        
        try:
            if sickbeard.PROXY_SETTING:
                proxies = {
                    "http": sickbeard.PROXY_SETTING,
                    "https": sickbeard.PROXY_SETTING,
                }

                r = self.session.get(url, headers=headers, proxies=proxies, verify=False)
            else:
                r = self.session.get(url, headers=headers, verify=False)
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


class ThePirateBayCache(tvcache.TVCache):
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


class ThePirateBayWebproxy:
    def __init__(self):
        self.Type = 'GlypeProxy'
        self.param = 'browse.php?u='
        self.option = '&b=32'
        self.enabled = False
        self.url = None

        self.urls = {
            'Getprivate.eu (NL)': 'http://getprivate.eu/',
            '15bb51.info (US)': 'http://15bb51.info/',
            'Hideme.nl (NL)': 'http://hideme.nl/',
            'Proxite.eu (DE)': 'http://proxite.eu/',
            'Webproxy.cz (CZ)': 'http://webproxy.cz/',
            '2me2u (CZ)': 'http://2me2u.me/',
            'Interproxy.net (EU)': 'http://interproxy.net/',
            'Unblockersurf.info (DK)': 'http://unblockersurf.info/',
            'Hiload.org (NL)': 'http://hiload.org/',
        }

    def __del__(self):
        pass

    def isEnabled(self):
        """ Return True if we Choose to call TPB via Proxy """
        return self.enabled

    def getProxyURL(self):
        """ Return the Proxy URL Choosen via Provider Setting """
        return str(self.url)

    def _buildURL(self, url):
        """ Return the Proxyfied URL of the page """
        if self.isEnabled():
            url = self.getProxyURL() + self.param + url + self.option

        return url

    def _buildRE(self, regx):
        """ Return the Proxyfied RE string """
        if self.isEnabled():
            regx = re.sub('//1', self.option, regx).replace('&', '&amp;')
        else:
            regx = re.sub('//1', '', regx)

        return regx


provider = ThePirateBayProvider()
