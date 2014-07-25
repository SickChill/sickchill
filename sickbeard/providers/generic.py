# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import datetime
import os
import re
import itertools
import Queue
import sickbeard
import requests

from sickbeard import helpers, classes, logger, db
from sickbeard.common import MULTI_EP_RESULT, SEASON_RESULT
from sickbeard import tvcache
from sickbeard import encodingKludge as ek
from sickbeard.exceptions import ex
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException
from sickbeard.common import Quality

from lib.hachoir_parser import createParser

class GenericProvider:
    NZB = "nzb"
    TORRENT = "torrent"

    def __init__(self, name):
        self.queue = Queue.Queue()

        # these need to be set in the subclass
        self.providerType = None
        self.name = name
        self.url = ''

        self.show = None

        self.supportsBacklog = False
        self.supportsAbsoluteNumbering = False
        self.anime_only = False

        self.search_mode = None
        self.search_fallback = False
        self.backlog_only = False

        self.cache = tvcache.TVCache(self)

        self.session = requests.session()
        self.session.verify = False
        self.session.headers.update({
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36'})

    def getID(self):
        return GenericProvider.makeID(self.name)

    @staticmethod
    def makeID(name):
        return re.sub("[^\w\d_]", "_", name.strip().lower())

    def imageName(self):
        return self.getID() + '.png'

    def _checkAuth(self):
        return

    def isActive(self):
        if self.providerType == GenericProvider.NZB and sickbeard.USE_NZBS:
            return self.isEnabled()
        elif self.providerType == GenericProvider.TORRENT and sickbeard.USE_TORRENTS:
            return self.isEnabled()
        else:
            return False

    def isEnabled(self):
        """
        This should be overridden and should return the config setting eg. sickbeard.MYPROVIDER
        """
        return False

    def getResult(self, episodes):
        """
        Returns a result of the correct type for this provider
        """

        if self.providerType == GenericProvider.NZB:
            result = classes.NZBSearchResult(episodes)
        elif self.providerType == GenericProvider.TORRENT:
            result = classes.TorrentSearchResult(episodes)
        else:
            result = classes.SearchResult(episodes)

        result.provider = self

        return result

    def getURL(self, url, post_data=None, headers=None, json=False):
        """
        By default this is just a simple urlopen call but this method should be overridden
        for providers with special URL requirements (like cookies)
        """

        if not headers:
            headers = []

        data = helpers.getURL(url, post_data, headers, json=json)

        if not data:
            logger.log(u"Error loading " + self.name + " URL: " + url, logger.ERROR)
            return None

        return data

    def downloadResult(self, result):
        """
        Save the result to disk.
        """

        logger.log(u"Downloading a result from " + self.name + " at " + result.url)

        data = self.getURL(result.url)

        if data is None:
            return False

        # use the appropriate watch folder
        if self.providerType == GenericProvider.NZB:
            saveDir = sickbeard.NZB_DIR
            writeMode = 'w'
        elif self.providerType == GenericProvider.TORRENT:
            saveDir = sickbeard.TORRENT_DIR
            writeMode = 'wb'
        else:
            return False

        # use the result name as the filename
        file_name = ek.ek(os.path.join, saveDir, helpers.sanitizeFileName(result.name) + '.' + self.providerType)

        logger.log(u"Saving to " + file_name, logger.DEBUG)

        try:
            with open(file_name, writeMode) as fileOut:
                fileOut.write(data)
            helpers.chmodAsParent(file_name)
        except EnvironmentError, e:
            logger.log("Unable to save the file: " + ex(e), logger.ERROR)
            return False

        # as long as it's a valid download then consider it a successful snatch
        return self._verify_download(file_name)

    def _verify_download(self, file_name=None):
        """
        Checks the saved file to see if it was actually valid, if not then consider the download a failure.
        """

        # primitive verification of torrents, just make sure we didn't get a text file or something
        if self.providerType == GenericProvider.TORRENT:
            parser = createParser(file_name)
            if parser:
                mime_type = parser._getMimeType()
                try:
                    parser.stream._input.close()
                except:
                    pass
                if mime_type != 'application/x-bittorrent':
                    logger.log(u"Result is not a valid torrent file", logger.WARNING)
                    return False

        return True

    def searchRSS(self, episodes):
        return self.cache.findNeededEpisodes(episodes)

    def getQuality(self, item, anime=False):
        """
        Figures out the quality of the given RSS item node
        
        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed
        
        Returns a Quality value obtained from the node's data 
        """
        (title, url) = self._get_title_and_url(item)  # @UnusedVariable
        quality = Quality.sceneQuality(title, anime)
        return quality

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0):
        return []

    def _get_season_search_strings(self, episode):
        return []

    def _get_episode_search_strings(self, eb_obj, add_string=''):
        return []

    def _get_title_and_url(self, item):
        """
        Retrieves the title and URL data from the item XML node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns: A tuple containing two strings representing title and URL respectively
        """

        title = item.title if item.title else None
        if title:
            title = u'' + title
            title = title.replace(' ', '.')

        url = item.link if item.link else None
        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

    def findSearchResults(self, show, season, episodes, search_mode, manualSearch=False):

        self._checkAuth()
        self.show = show

        results = {}
        itemList = []

        searched_scene_season = None
        for epObj in episodes:
            # check cache for results
            cacheResult = self.cache.searchCache([epObj], manualSearch)
            if len(cacheResult):
                results.update({epObj.episode: cacheResult[epObj]})
                continue

            # skip if season already searched
            if len(episodes) > 1 and searched_scene_season == epObj.scene_season:
                continue

            # mark season searched for season pack searches so we can skip later on
            searched_scene_season = epObj.scene_season

            if len(episodes) > 1:
                # get season search results
                for curString in self._get_season_search_strings(epObj):
                    itemList += self._doSearch(curString, search_mode, len(episodes))
            else:
                # get single episode search results
                for curString in self._get_episode_search_strings(epObj):
                    itemList += self._doSearch(curString, 'eponly', len(episodes))

        # if we found what we needed already from cache then return results and exit
        if len(results) == len(episodes):
            return results

        # sort list by quality
        if len(itemList):
            items = {}
            itemsUnknown = []
            for item in itemList:
                quality = self.getQuality(item, anime=show.is_anime)
                if quality == Quality.UNKNOWN:
                    itemsUnknown += [item]
                else:
                    if quality not in items:
                        items[quality] = [item]
                    else:
                        items[quality].append(item)

            itemList = list(itertools.chain(*[v for (k, v) in sorted(items.items(), reverse=True)]))
            itemList += itemsUnknown if itemsUnknown else []

        # filter results
        cl = []
        for item in itemList:
            (title, url) = self._get_title_and_url(item)

            # parse the file name
            try:
                myParser = NameParser(False, convert=True)
                parse_result = myParser.parse(title)
            except InvalidNameException:
                logger.log(u"Unable to parse the filename " + title + " into a valid episode", logger.DEBUG)
                continue
            except InvalidShowException:
                logger.log(u"Unable to parse the filename " + title + " into a valid show", logger.DEBUG)
                continue

            showObj = parse_result.show
            quality = parse_result.quality
            release_group = parse_result.release_group

            addCacheEntry = False
            if not (showObj.air_by_date or showObj.sports):
                if search_mode == 'sponly' and len(parse_result.episode_numbers):
                    logger.log(
                        u"This is supposed to be a season pack search but the result " + title + " is not a valid season pack, skipping it",
                        logger.DEBUG)
                    addCacheEntry = True
                else:
                    if not len(parse_result.episode_numbers) and (
                                parse_result.season_number and parse_result.season_number != season) or (
                                not parse_result.season_number and season != 1):
                        logger.log(u"The result " + title + " doesn't seem to be a valid season that we are trying to snatch, ignoring",
                                   logger.DEBUG)
                        addCacheEntry = True
                    elif len(parse_result.episode_numbers) and (
                                    parse_result.season_number != season or not [ep for ep in episodes if
                                                                                 ep.scene_episode in parse_result.episode_numbers]):
                        logger.log(u"The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring",
                                   logger.DEBUG)
                        addCacheEntry = True

                if not addCacheEntry:
                    # we just use the existing info for normal searches
                    actual_season = season
                    actual_episodes = parse_result.episode_numbers
            else:
                if not (parse_result.is_air_by_date or parse_result.is_sports):
                    logger.log(
                        u"This is supposed to be a date search but the result " + title + " didn't parse as one, skipping it",
                        logger.DEBUG)
                    addCacheEntry = True
                else:
                    airdate = parse_result.air_date.toordinal() if parse_result.air_date else parse_result.sports_air_date.toordinal()
                    myDB = db.DBConnection()
                    sql_results = myDB.select(
                        "SELECT season, episode FROM tv_episodes WHERE showid = ? AND airdate = ?",
                        [showObj.indexerid, airdate])

                    if len(sql_results) != 1:
                        logger.log(
                            u"Tried to look up the date for the episode " + title + " but the database didn't give proper results, skipping it",
                            logger.WARNING)
                        addCacheEntry = True

                if not addCacheEntry:
                    actual_season = int(sql_results[0]["season"])
                    actual_episodes = [int(sql_results[0]["episode"])]

            # add parsed result to cache for usage later on
            if addCacheEntry:
                logger.log(u"Adding item from search to cache: " + title, logger.DEBUG)
                ci = self.cache._addCacheEntry(title, url, parse_result=parse_result)
                if ci is not None:
                    cl.append(ci)
                continue

            # make sure we want the episode
            wantEp = True
            for epNo in actual_episodes:
                if not showObj.wantEpisode(actual_season, epNo, quality, manualSearch):
                    wantEp = False
                    break

            if not wantEp:
                logger.log(
                    u"Ignoring result " + title + " because we don't want an episode that is " +
                    Quality.qualityStrings[
                        quality], logger.DEBUG)

                continue

            logger.log(u"Found result " + title + " at " + url, logger.DEBUG)

            # make a result object
            epObj = []
            for curEp in actual_episodes:
                epObj.append(showObj.getEpisode(actual_season, curEp))

            result = self.getResult(epObj)
            result.show = showObj
            result.url = url
            result.name = title
            result.quality = quality
            result.release_group = release_group
            result.content = None

            if len(epObj) == 1:
                epNum = epObj[0].episode
                logger.log(u"Single episode result.", logger.DEBUG)
            elif len(epObj) > 1:
                epNum = MULTI_EP_RESULT
                logger.log(u"Separating multi-episode result to check for later - result contains episodes: " + str(
                    parse_result.episode_numbers), logger.DEBUG)
            elif len(epObj) == 0:
                epNum = SEASON_RESULT
                logger.log(u"Separating full season result to check for later", logger.DEBUG)

            if not result:
                continue

            if epNum not in results:
                results[epNum] = [result]
            else:
                results[epNum].append(result)

        # check if we have items to add to cache
        if len(cl) > 0:
            myDB = self.cache._getDB()
            myDB.mass_action(cl)

        return results

    def findPropers(self, search_date=None):

        results = self.cache.listPropers(search_date)

        return [classes.Proper(x['name'], x['url'], datetime.datetime.fromtimestamp(x['time']), self.show) for x in
                results]

    def seedRatio(self):
        '''
        Provider should override this value if custom seed ratio enabled
        It should return the value of the provider seed ratio
        '''
        return ''


class NZBProvider(GenericProvider):
    def __init__(self, name):
        GenericProvider.__init__(self, name)

        self.providerType = GenericProvider.NZB


class TorrentProvider(GenericProvider):
    def __init__(self, name):
        GenericProvider.__init__(self, name)

        self.providerType = GenericProvider.TORRENT
