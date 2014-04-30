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
from sickbeard import name_cache, scene_exceptions
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

        # Clear out records missing there Indexer IDs
        try:
            sql = "DELETE FROM [" + providerName + "] WHERE indexerid is NULL or indexerid is 0"
            self.connection.execute(sql)
            self.connection.commit()
        except:
            pass

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

    def _addCacheEntry(self, name, url, quality=None):

        cacheDB = self._getDB()
        parse_result = None
        indexer_id = None
        season = None
        episodes = None
        from_cache = False

        # if we don't have complete info then parse the filename to get it
        while(True):
            try:
                myParser = NameParser()
                parse_result = myParser.parse(name).convert()
            except InvalidNameException:
                logger.log(u"Unable to parse the filename " + name + " into a valid episode", logger.DEBUG)
                return None

            if not parse_result:
                logger.log(u"Giving up because I'm unable to parse this name: " + name, logger.DEBUG)
                return None

            if not parse_result.series_name:
                logger.log(u"No series name retrieved from " + name + ", unable to cache it", logger.DEBUG)
                return None

            logger.log(
                u"Checking the cahe for show:" + str(parse_result.series_name),
                logger.DEBUG)

            # remember if the cache lookup worked or not so we know whether we should bother updating it later
            cache_id = name_cache.retrieveNameFromCache(parse_result.series_name)
            if cache_id:
                logger.log(u"Cache lookup found Indexer ID:" + repr(indexer_id) + ", using that for " + parse_result.series_name, logger.DEBUG)
                from_cache = True
                indexer_id = cache_id
                break

            # if the cache failed, try looking up the show name in the database
            logger.log(
                u"Checking the database for show:" + str(parse_result.series_name),
                logger.DEBUG)

            showResult = helpers.searchDBForShow(parse_result.series_name)
            if showResult:
                logger.log(
                    u"Database lookup found Indexer ID:" + str(showResult[1]) + ", using that for " + parse_result.series_name, logger.DEBUG)
                indexer_id = showResult[1]
            break

        # if we didn't find a Indexer ID return None
        if indexer_id:
            # add to name cache if we didn't get it from the cache
            if not from_cache:
                name_cache.addNameToCache(parse_result.series_name, indexer_id)

            # if the show isn't in out database then return None
            try:
                showObj = helpers.findCertainShow(sickbeard.showList, indexer_id)
                myDB = db.DBConnection()
                if parse_result.air_by_date:
                    sql_results = myDB.select("SELECT season, episode FROM tv_episodes WHERE showid = ? AND airdate = ?",
                                              [showObj.indexerid, parse_result.air_date.toordinal()])
                    if sql_results > 0:
                        season = int(sql_results[0]["season"])
                        episodes = [int(sql_results[0]["episode"])]
                else:
                    season = parse_result.season_number
                    episodes = parse_result.episode_numbers

                if season and episodes:
                    # store episodes as a seperated string
                    episodeText = "|" + "|".join(map(str, episodes)) + "|"

                    # get the current timestamp
                    curTimestamp = int(time.mktime(datetime.datetime.today().timetuple()))

                    # get quality of release
                    if quality is None:
                        quality = Quality.sceneQuality(name)

                    if not isinstance(name, unicode):
                        name = unicode(name, 'utf-8')

                    cacheDB.action(
                        "INSERT INTO [" + self.providerID + "] (name, season, episodes, indexerid, url, time, quality) VALUES (?,?,?,?,?,?,?)",
                        [name, season, episodeText, indexer_id, url, curTimestamp, quality])
            except:
                return

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
            # skip if we don't have a indexerid
            indexerid = int(curResult["indexerid"])
            if not indexerid:
                continue

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
                epObj = None
                if episode:
                    epObj = episode

                if epObj:
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
