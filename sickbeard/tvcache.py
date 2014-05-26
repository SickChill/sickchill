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

import os

import time
import datetime
import sqlite3
import urllib
import urlparse
import re
import threading
import sickbeard

from lib.shove import Shove
from lib.feedcache import cache

from sickbeard import db
from sickbeard import logger
from sickbeard.common import Quality, cpu_presets

from sickbeard import helpers, show_name_helpers
from sickbeard.exceptions import MultipleShowObjectsException
from sickbeard.exceptions import AuthException
from sickbeard import encodingKludge as ek

from name_parser.parser import NameParser, InvalidNameException

cache_lock = threading.Lock()


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
        if not self.shouldClearCache():
            return

        myDB = self._getDB()

        curDate = datetime.date.today() - datetime.timedelta(weeks=1)

        myDB.action("DELETE FROM [" + self.providerID + "] WHERE time < ?", [int(time.mktime(curDate.timetuple()))])

    def _getRSSData(self):

        data = None

        return data

    def _checkAuth(self, data):
        return True

    def _checkItemAuth(self, title, url):
        return True

    def updateCache(self):

        # delete anything older then 7 days
        logger.log(u"Clearing " + self.provider.name + " cache")
        self._clearCache()

        if not self.shouldUpdate():
            return

        if self._checkAuth(None):
            data = self._getRSSData()

            # as long as the http request worked we count this as an update
            if data:
                self.setLastUpdate()
            else:
                return []

            if self._checkAuth(data):
                items = data.entries
                cl = []
                for item in items:
                    ci = self._parseItem(item)
                    if ci is not None:
                        cl.append(ci)

                myDB = self._getDB()
                myDB.mass_action(cl)

            else:
                raise AuthException(
                    u"Your authentication credentials for " + self.provider.name + " are incorrect, check your config")

        return []

    def getRSSFeed(self, url, post_data=None):
        # create provider storaqe cache
        storage = Shove('sqlite:///' + ek.ek(os.path.join, sickbeard.CACHE_DIR, self.provider.name) + '.db')
        fc = cache.Cache(storage)

        parsed = list(urlparse.urlparse(url))
        parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one

        if post_data:
            url += urllib.urlencode(post_data)

        f = fc.fetch(url)

        if not f:
            logger.log(u"Error loading " + self.providerID + " URL: " + url, logger.ERROR)
            return None
        elif 'error' in f.feed:
            logger.log(u"Newznab ERROR:[%s] CODE:[%s]" % (f.feed['error']['description'], f.feed['error']['code']),
                       logger.DEBUG)
            return None
        elif not f.entries:
            logger.log(u"No items found on " + self.providerID + " using URL: " + url, logger.WARNING)
            return None

        storage.close()

        return f


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

            logger.log(u"Checking if item from RSS feed is in the cache: " + title, logger.DEBUG)
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

    def _getLastSearch(self):
        myDB = self._getDB()
        sqlResults = myDB.select("SELECT time FROM lastSearch WHERE provider = ?", [self.providerID])

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

    def setLastSearch(self, toDate=None):
        if not toDate:
            toDate = datetime.datetime.today()

        myDB = self._getDB()
        myDB.upsert("lastSearch",
                    {'time': int(time.mktime(toDate.timetuple()))},
                    {'provider': self.providerID})

    lastUpdate = property(_getLastUpdate)
    lastSearch = property(_getLastSearch)

    def shouldUpdate(self):
        # if we've updated recently then skip the update
        #if datetime.datetime.today() - self.lastUpdate < datetime.timedelta(minutes=self.minTime):
        #    logger.log(u"Last update was too soon, using old cache: today()-" + str(self.lastUpdate) + "<" + str(
        #        datetime.timedelta(minutes=self.minTime)), logger.DEBUG)
        #    return False

        return True

    def shouldClearCache(self):
        # if daily search hasn't used our previous results yet then don't clear the cache
        if self.lastUpdate > self.lastSearch:
            logger.log(
                u"Daily search has not yet searched our last cache results, skipping clearig cache ...", logger.DEBUG)
            return False

        return True

    def _addCacheEntry(self, name, url, quality=None):

        try:
            myParser = NameParser()
            parse_result = myParser.parse(name).convert()
        except InvalidNameException:
            logger.log(u"Unable to parse the filename " + name + " into a valid episode", logger.DEBUG)
            return None

        if not parse_result or not parse_result.series_name:
            return None

        if not parse_result.show:
            logger.log(u"No match for show: [" + parse_result.series_name + "], not caching ...", logger.DEBUG)
            return None

        season = episodes = None
        if parse_result.air_by_date or parse_result.sports:
            myDB = db.DBConnection()

            airdate = parse_result.air_date.toordinal() or parse_result.sports_event_date.toordinal()
            sql_results = myDB.select(
                "SELECT season, episode FROM tv_episodes WHERE showid = ? AND indexer = ? AND airdate = ?",
                [parse_result.show.indexerid, parse_result.show.indexer, airdate])
            if sql_results > 0:
                season = int(sql_results[0]["season"])
                episodes = [int(sql_results[0]["episode"])]
        else:
            season = parse_result.season_number if parse_result.season_number != None else 1
            episodes = parse_result.episode_numbers

        if season and episodes:
            # store episodes as a seperated string
            episodeText = "|" + "|".join(map(str, episodes)) + "|"

            # get the current timestamp
            curTimestamp = int(time.mktime(datetime.datetime.today().timetuple()))

            # get quality of release
            if quality is None:
                quality = Quality.sceneQuality(name, parse_result.is_anime)

            if not isinstance(name, unicode):
                name = unicode(name, 'utf-8')

            logger.log(u"Added RSS item: [" + name + "] to cache: [" + self.providerID + "]", logger.DEBUG)

            return [
                "INSERT INTO [" + self.providerID + "] (name, season, episodes, indexerid, url, time, quality) VALUES (?,?,?,?,?,?,?)",
                [name, season, episodeText, parse_result.show.indexerid, url, curTimestamp, quality]]


    def searchCache(self, episodes, manualSearch=False):
        neededEps = self.findNeededEpisodes(episodes, manualSearch)
        return neededEps

    def listPropers(self, date=None, delimiter="."):
        myDB = self._getDB()

        sql = "SELECT * FROM [" + self.providerID + "] WHERE name LIKE '%.PROPER.%' OR name LIKE '%.REPACK.%'"

        if date != None:
            sql += " AND time >= " + str(int(time.mktime(date.timetuple())))

        return filter(lambda x: x['indexerid'] != 0, myDB.select(sql))


    def findNeededEpisodes(self, episodes, manualSearch=False):
        neededEps = {}

        cacheDB = self._getDB()

        for epObj in episodes:
            sqlResults = cacheDB.select(
                "SELECT * FROM [" + self.providerID + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ?",
                [epObj.show.indexerid, epObj.season, "%|" + str(epObj.episode) + "|%"])

            # for each cache entry
            for curResult in sqlResults:

                # skip non-tv crap (but allow them for Newzbin cause we assume it's filtered well)
                if self.providerID != 'newzbin' and not show_name_helpers.filterBadReleases(curResult["name"]):
                    continue

                # get the show object, or if it's not one of our shows then ignore it
                try:
                    showObj = helpers.findCertainShow(sickbeard.showList, int(curResult["indexerid"]))
                except MultipleShowObjectsException:
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

                    if not epObj:
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

        # datetime stamp this search so cache gets cleared
        self.setLastSearch()

        return neededEps

