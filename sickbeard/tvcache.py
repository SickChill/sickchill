# Author: Nic Wolfe <nic@wolfeden.ca>
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

import time
import datetime
import sqlite3

import sickbeard

from sickbeard import db
from sickbeard import logger
from sickbeard.common import Quality

from sickbeard import helpers, show_name_helpers
from sickbeard import name_cache
from sickbeard.exceptions import MultipleShowObjectsException, ex
from sickbeard.exceptions import ex, AuthException

from name_parser.parser import NameParser, InvalidNameException


class CacheDBConnection(db.DBConnection):
    def __init__(self, providerName):
        db.DBConnection.__init__(self, "cache.db")

        # Create the table if it's not already there
        try:
            sql = "CREATE TABLE [" + providerName + "] (name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT);"
            self.connection.execute(sql)
            self.connection.commit()
        except sqlite3.OperationalError, e:
            if str(e) != "table [" + providerName + "] already exists":
                raise

        # Create the table if it's not already there
        try:
            sql = "CREATE TABLE lastUpdate (provider TEXT, time NUMERIC);"
            self.connection.execute(sql)
            self.connection.commit()
        except sqlite3.OperationalError, e:
            if str(e) != "table lastUpdate already exists":
                raise


class TVCache():
    def __init__(self, provider):

        self.provider = provider
        self.providerID = self.provider.getID()
        self.minTime = 10

    def _getDB(self):

        return CacheDBConnection(self.providerID)

    def _clearCache(self):

        myDB = self._getDB()

        myDB.action("DELETE FROM [" + self.providerID + "] WHERE 1")

    def _getRSSData(self):

        data = None

        return data

    def _checkAuth(self, data):
        return True

    def _checkItemAuth(self, title, url):
        return True

    def updateCache(self):

        if not self.shouldUpdate():
            return

        if self._checkAuth(None):
            data = self._getRSSData()

            # as long as the http request worked we count this as an update
            if data:
                self.setLastUpdate()
            else:
                return []

            # now that we've loaded the current RSS feed lets delete the old cache
            logger.log(u"Clearing " + self.provider.name + " cache and updating with new information")
            self._clearCache()

            if self._checkAuth(data):
                items = data.entries
                cl = []
                for item in items:
                    ci = self._parseItem(item)
                    if ci is not None:
                        cl.append(ci)

                if len(cl) > 0:
                    myDB = self._getDB()
                    myDB.mass_action(cl)

            else:
                raise AuthException(
                    u"Your authentication credentials for " + self.provider.name + " are incorrect, check your config")

        return []

    def _translateTitle(self, title):
        return title.replace(' ', '.')

    def _translateLinkURL(self, url):
        return url.replace('&amp;', '&')

    def _parseItem(self, item):

        title = item.title
        url = item.link

        self._checkItemAuth(title, url)

        if title and url:
            title = self._translateTitle(title)
            url = self._translateLinkURL(url)

            logger.log(u"Adding item from RSS to cache: " + title, logger.DEBUG)
            return self._addCacheEntry(title, url)

        else:
            logger.log(
                u"The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable",
                logger.DEBUG)
            return None


    def _getLastUpdate(self):
        myDB = self._getDB()
        sqlResults = myDB.select("SELECT time FROM lastUpdate WHERE provider = ?", [self.providerID])

        if sqlResults:
            lastTime = int(sqlResults[0]["time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())):
                lastTime = 0
        else:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    def setLastUpdate(self, toDate=None):

        if not toDate:
            toDate = datetime.datetime.today()

        myDB = self._getDB()
        myDB.upsert("lastUpdate",
                    {'time': int(time.mktime(toDate.timetuple()))},
                    {'provider': self.providerID})

    lastUpdate = property(_getLastUpdate)

    def shouldUpdate(self):
        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.lastUpdate < datetime.timedelta(minutes=self.minTime):
            logger.log(u"Last update was too soon, using old cache: today()-" + str(self.lastUpdate) + "<" + str(
                datetime.timedelta(minutes=self.minTime)), logger.DEBUG)
            return False

        return True

    def _addCacheEntry(self, name, url, season=None, episodes=None, indexer_id=0, quality=None, extraNames=[]):

        myDB = self._getDB()

        parse_result = None

        # if we don't have complete info then parse the filename to get it
        for curName in [name] + extraNames:
            try:
                myParser = NameParser()
                parse_result = myParser.parse(curName, True)
            except InvalidNameException:
                logger.log(u"Unable to parse the filename " + curName + " into a valid episode", logger.DEBUG)
                continue

        if not parse_result:
            logger.log(u"Giving up because I'm unable to parse this name: " + name, logger.DEBUG)
            return None

        if not parse_result.series_name:
            logger.log(u"No series name retrieved from " + name + ", unable to cache it", logger.DEBUG)
            return None

        indexer_lang = None

        if indexer_id:
            # if we have only the indexer_id, use the database
            showObj = helpers.findCertainShow(sickbeard.showList, indexer_id)
            if showObj:
                self.indexer = int(showObj.indexer)
                indexer_lang = showObj.lang
            else:
                logger.log(u"We were given a Indexer ID " + str(indexer_id) + " but it doesn't match a show we have in our list, so leaving indexer_id empty",logger.DEBUG)
                indexer_id = 0

        # if no indexerID then fill out as much info as possible by searching the show name
        if not indexer_id:
            # check the name cache and see if we already know what show this is
            logger.log(
                u"Checking the cache to see if we already know the indexer id of " + parse_result.series_name,
                logger.DEBUG)
            indexer_id = name_cache.retrieveNameFromCache(parse_result.series_name)

            # remember if the cache lookup worked or not so we know whether we should bother updating it later
            if indexer_id == None:
                logger.log(u"No cache results returned, continuing on with the search", logger.DEBUG)
                from_cache = False
            else:
                logger.log(u"Cache lookup found " + repr(indexer_id) + ", using that", logger.DEBUG)
                from_cache = True

            # if the cache failed, try looking up the show name in the database
            if indexer_id == None:
                logger.log(u"Trying to look the show up in the show database", logger.DEBUG)
                showResult = helpers.searchDBForShow(parse_result.series_name)
                if showResult:
                    logger.log(
                        u"" + parse_result.series_name + " was found to be show " + showResult[2] + " (" + str(
                            showResult[1]) + ") in our DB.", logger.DEBUG)
                    indexer_id = showResult[1]

            # if the DB lookup fails then do a comprehensive regex search
            if indexer_id == None:
                logger.log(u"Couldn't figure out a show name straight from the DB, trying a regex search instead",
                           logger.DEBUG)
                for curShow in sickbeard.showList:
                    if show_name_helpers.isGoodResult(name, curShow, False):
                        logger.log(u"Successfully matched " + name + " to " + curShow.name + " with regex",
                                   logger.DEBUG)
                        indexer_id = curShow.indexerid
                        indexer_lang = curShow.lang
                        break

            # if indexer_id was anything but None (0 or a number) then
            if not from_cache:
                name_cache.addNameToCache(parse_result.series_name, indexer_id)

            # if we came out with indexer_id = None it means we couldn't figure it out at all, just use 0 for that
            if indexer_id == None:
                indexer_id = 0

            # if we found the show then retrieve the show object
            if indexer_id:
                try:
                    showObj = helpers.findCertainShow(sickbeard.showList, indexer_id)
                except (MultipleShowObjectsException):
                    showObj = None
                if showObj:
                    self.indexer = int(showObj.indexer)
                    indexer_lang = showObj.lang

        # if we weren't provided with season/episode information then get it from the name that we parsed
        if not season:
            season = parse_result.season_number if parse_result.season_number != None else 1
        if not episodes:
            episodes = parse_result.episode_numbers

        # if we have an air-by-date show then get the real season/episode numbers
        if parse_result.air_by_date and indexer_id:
            try:
                lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()
                if not (indexer_lang == "" or indexer_lang == "en" or indexer_lang == None):
                    lINDEXER_API_PARMS['language'] = indexer_lang

                t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

                epObj = t[indexer_id].airedOn(parse_result.air_date)[0]
                season = int(epObj["seasonnumber"])
                episodes = [int(epObj["episodenumber"])]
            except sickbeard.indexer_episodenotfound:
                logger.log(u"Unable to find episode with date " + str(
                    parse_result.air_date) + " for show " + parse_result.series_name + ", skipping", logger.WARNING)
                return None
            except sickbeard.indexer_error, e:
                logger.log(u"Unable to contact " + sickbeard.indexerApi(self.indexer).name + ": " + ex(e),
                           logger.WARNING)
                return None

        episodeText = "|" + "|".join(map(str, episodes)) + "|"

        # get the current timestamp
        curTimestamp = int(time.mktime(datetime.datetime.today().timetuple()))

        if not quality:
            quality = Quality.sceneQuality(name)

        if not isinstance(name, unicode):
            name = unicode(name, 'utf-8')

        myDB.action(
            "INSERT INTO [" + self.providerID + "] (name, season, episodes, indexerid, url, time, quality) VALUES (?,?,?,?,?,?,?)",
            [name, season, episodeText, indexer_id, url, curTimestamp, quality])


    def searchCache(self, episode, manualSearch=False):
        neededEps = self.findNeededEpisodes(episode, manualSearch)
        return neededEps[episode]

    def listPropers(self, date=None, delimiter="."):

        myDB = self._getDB()

        sql = "SELECT * FROM [" + self.providerID + "] WHERE name LIKE '%.PROPER.%' OR name LIKE '%.REPACK.%'"

        if date != None:
            sql += " AND time >= " + str(int(time.mktime(date.timetuple())))

        #return filter(lambda x: x['indexerid'] != 0, myDB.select(sql))
        return myDB.select(sql)

    def findNeededEpisodes(self, episode=None, manualSearch=False):
        neededEps = {}

        if episode:
            neededEps[episode] = []

        myDB = self._getDB()

        if not episode:
            sqlResults = myDB.select("SELECT * FROM [" + self.providerID + "]")
        else:
            sqlResults = myDB.select(
                "SELECT * FROM [" + self.providerID + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ?",
                [episode.show.indexerid, episode.season, "%|" + str(episode.episode) + "|%"])

        # for each cache entry
        for curResult in sqlResults:

            # skip non-tv crap (but allow them for Newzbin cause we assume it's filtered well)
            if self.providerID != 'newzbin' and not show_name_helpers.filterBadReleases(curResult["name"]):
                continue

            # get the show object, or if it's not one of our shows then ignore it
            try:
                showObj = helpers.findCertainShow(sickbeard.showList, int(curResult["indexerid"]))
            except (MultipleShowObjectsException):
                showObj = None
            if not showObj:
                continue

            # get season and ep data (ignoring multi-eps for now)
            curSeason = int(curResult["season"])
            if curSeason == -1:
                continue
            curEp = curResult["episodes"].split("|")[1]
            if not curEp:
                continue
            curEp = int(curEp)
            curQuality = int(curResult["quality"])

            # if the show says we want that episode then add it to the list
            if not showObj.wantEpisode(curSeason, curEp, curQuality, manualSearch):
                logger.log(u"Skipping " + curResult["name"] + " because we don't want an episode that's " +
                           Quality.qualityStrings[curQuality], logger.DEBUG)

            else:

                if episode:
                    epObj = episode
                else:
                    epObj = showObj.getEpisode(curSeason, curEp)

                # build a result object
                title = curResult["name"]
                url = curResult["url"]

                logger.log(u"Found result " + title + " at " + url)

                result = self.provider.getResult([epObj])
                result.url = url
                result.name = title
                result.quality = curQuality
                result.content = self.provider.getURL(url) \
                    if self.provider.providerType == sickbeard.providers.generic.GenericProvider.TORRENT \
                    and not url.startswith('magnet') else None

                # add it to the list
                if epObj not in neededEps:
                    neededEps[epObj] = [result]
                else:
                    neededEps[epObj].append(result)

        return neededEps
