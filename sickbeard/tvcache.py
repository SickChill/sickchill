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

import time
import datetime
import itertools
import urllib2

import sickbeard

from sickbeard import db
from sickbeard import logger
from sickbeard.common import Quality
from sickbeard import helpers
from sickbeard.exceptions import ex
from sickbeard.exceptions import AuthException
from sickbeard.rssfeeds import RSSFeeds
from name_parser.parser import NameParser, InvalidNameException, InvalidShowException
from sickbeard import encodingKludge as ek
from sickbeard import show_name_helpers

class CacheDBConnection(db.DBConnection):
    def __init__(self, providerName):
        db.DBConnection.__init__(self, "cache.db")

        # Create the table if it's not already there
        try:
            if not self.hasTable(providerName):
                self.action(
                    "CREATE TABLE [" + providerName + "] (name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT, release_group TEXT)")
            else:
                sqlResults = self.select("SELECT url, COUNT(url) AS count FROM [" + providerName + "] GROUP BY url HAVING count > 1")

                for cur_dupe in sqlResults:
                    self.action("DELETE FROM [" + providerName + "] WHERE url = ?", [cur_dupe["url"]])

            # add unique index to prevent further dupes from happening if one does not exist
            self.action("CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON [" + providerName + "] (url)")

            # add release_group column to table if missing
            if not self.hasColumn(providerName, 'release_group'):
                self.addColumn(providerName, 'release_group', "TEXT", "")

            # add version column to table if missing
            if not self.hasColumn(providerName, 'version'):
                self.addColumn(providerName, 'version', "NUMERIC", "-1")

        except Exception, e:
            if str(e) != "table [" + providerName + "] already exists":
                raise

        # Create the table if it's not already there
        try:
            if not self.hasTable('lastUpdate'):
                self.action("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC)")
        except Exception, e:
            if str(e) != "table lastUpdate already exists":
                raise


class TVCache():
    def __init__(self, provider):
        self.provider = provider
        self.providerID = self.provider.getID()
        self.providerDB = None
        self.minTime = 10

    def _getDB(self):
        # init provider database if not done already
        if not self.providerDB:
            self.providerDB = CacheDBConnection(self.providerID)

        return self.providerDB

    def _clearCache(self):
        if self.shouldClearCache():
            myDB = self._getDB()
            myDB.action("DELETE FROM [" + self.providerID + "] WHERE 1")

    def _get_title_and_url(self, item):
        return self.provider._get_title_and_url(item)

    def _getRSSData(self):
        return None

    def _checkAuth(self, data):
        return True

    def _checkItemAuth(self, title, url):
        return True

    def updateCache(self):
        # check if we should update
        if not self.shouldUpdate():
            return

        try:
            data = self._getRSSData()
            if self._checkAuth(data):
                # clear cache
                self._clearCache()

                # set updated
                self.setLastUpdate()

                cl = []
                for item in data['entries'] or []:
                    ci = self._parseItem(item)
                    if ci is not None:
                        cl.append(ci)

                if len(cl) > 0:
                    myDB = self._getDB()
                    myDB.mass_action(cl)

        except AuthException, e:
            logger.log(u"Authentication error: " + ex(e), logger.ERROR)
        except Exception, e:
            logger.log(u"Error while searching " + self.provider.name + ", skipping: " + repr(e), logger.DEBUG)

    def getRSSFeed(self, url, post_data=None, items=[]):
        handlers = []

        if self.provider.proxy.isEnabled():
            self.provider.headers.update({'Referer': self.provider.proxy.getProxyURL()})
        elif sickbeard.PROXY_SETTING:
            logger.log("Using proxy for url: " + url, logger.DEBUG)
            scheme, address = urllib2.splittype(sickbeard.PROXY_SETTING)
            address = sickbeard.PROXY_SETTING if scheme else 'http://' + sickbeard.PROXY_SETTING
            handlers = [urllib2.ProxyHandler({'http': address, 'https': address})]
            self.provider.headers.update({'Referer': address})
        elif 'Referer' in self.provider.headers:
            self.provider.headers.pop('Referer')

        return RSSFeeds(self.providerID).getFeed(
            self.provider.proxy._buildURL(url),
            post_data,
            self.provider.headers,
            items,
            handlers=handlers)

    def _translateTitle(self, title):
        return u'' + title.replace(' ', '.')

    def _translateLinkURL(self, url):
        return url.replace('&amp;', '&')

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)

        self._checkItemAuth(title, url)

        if title and url:
            title = self._translateTitle(title)
            url = self._translateLinkURL(url)

            logger.log(u"Attempting to add item to cache: " + title, logger.DEBUG)
            return self._addCacheEntry(title, url)

        else:
            logger.log(
                u"The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable",
                logger.DEBUG)

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
        if datetime.datetime.today() - self.lastUpdate < datetime.timedelta(minutes=self.minTime):
            logger.log(u"Last update was too soon, using old cache: " + str(self.lastUpdate) + ". Updated less then " + str(self.minTime) + " minutes ago", logger.DEBUG)
            return False

        return True

    def shouldClearCache(self):
        # if daily search hasn't used our previous results yet then don't clear the cache
        if self.lastUpdate > self.lastSearch:
            return False

        return True

    def _addCacheEntry(self, name, url, parse_result=None, indexer_id=0):

        # check if we passed in a parsed result or should we try and create one
        if not parse_result:

            # create showObj from indexer_id if available
            showObj = None
            if indexer_id:
                showObj = helpers.findCertainShow(sickbeard.showList, indexer_id)

            try:
                myParser = NameParser(showObj=showObj)
                parse_result = myParser.parse(name)
            except InvalidNameException:
                logger.log(u"Unable to parse the filename " + name + " into a valid episode", logger.DEBUG)
                return None
            except InvalidShowException:
                logger.log(u"Unable to parse the filename " + name + " into a valid show", logger.DEBUG)
                return None

            if not parse_result or not parse_result.series_name:
                return None

        # if we made it this far then lets add the parsed result to cache for usager later on
        season = parse_result.season_number if parse_result.season_number else 1
        episodes = parse_result.episode_numbers

        if season and episodes:
            # store episodes as a seperated string
            episodeText = "|" + "|".join(map(str, episodes)) + "|"

            # get the current timestamp
            curTimestamp = int(time.mktime(datetime.datetime.today().timetuple()))

            # get quality of release
            quality = parse_result.quality

            name = ek.ss(name)

            # get release group
            release_group = parse_result.release_group

            # get version
            version = parse_result.version

            logger.log(u"Added RSS item: [" + name + "] to cache: [" + self.providerID + "]", logger.DEBUG)

            return [
                "INSERT OR IGNORE INTO [" + self.providerID + "] (name, season, episodes, indexerid, url, time, quality, release_group, version) VALUES (?,?,?,?,?,?,?,?,?)",
                [name, season, episodeText, parse_result.show.indexerid, url, curTimestamp, quality, release_group, version]]


    def searchCache(self, episode, manualSearch=False, downCurQuality=False):
        neededEps = self.findNeededEpisodes(episode, manualSearch, downCurQuality)
        return neededEps[episode] if episode in neededEps else []

    def listPropers(self, date=None, delimiter="."):
        myDB = self._getDB()
        sql = "SELECT * FROM [" + self.providerID + "] WHERE name LIKE '%.PROPER.%' OR name LIKE '%.REPACK.%'"

        if date != None:
            sql += " AND time >= " + str(int(time.mktime(date.timetuple())))

        return filter(lambda x: x['indexerid'] != 0, myDB.select(sql))


    def findNeededEpisodes(self, episode, manualSearch=False, downCurQuality=False):
        neededEps = {}
        cl = []

        myDB = self._getDB()
        if not episode:
            sqlResults = myDB.select("SELECT * FROM [" + self.providerID + "]")
        elif type(episode) != list:
            sqlResults = myDB.select(
                "SELECT * FROM [" + self.providerID + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ?",
                [episode.show.indexerid, episode.season, "%|" + str(episode.episode) + "|%"])
        else:
            for epObj in episode:
                cl.append([
                    "SELECT * FROM [" + self.providerID + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND quality IN (" + ",".join(
                        [str(x) for x in epObj.wantedQuality]) + ")",
                    [epObj.show.indexerid, epObj.season, "%|" + str(epObj.episode) + "|%"]])

            sqlResults = myDB.mass_action(cl, fetchall=True)
            sqlResults = list(itertools.chain(*sqlResults))

        # for each cache entry
        for curResult in sqlResults:
            # ignored/required words, and non-tv junk
            if not show_name_helpers.filterBadReleases(curResult["name"]):
                continue

            # get the show object, or if it's not one of our shows then ignore it
            showObj = helpers.findCertainShow(sickbeard.showList, int(curResult["indexerid"]))
            if not showObj:
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not showObj.is_anime:
                logger.log(u"" + str(showObj.name) + " is not an anime, skiping", logger.DEBUG)
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
            curReleaseGroup = curResult["release_group"]
            curVersion = curResult["version"]

            # if the show says we want that episode then add it to the list
            if not showObj.wantEpisode(curSeason, curEp, curQuality, manualSearch, downCurQuality):
                logger.log(u"Skipping " + curResult["name"] + " because we don't want an episode that's " +
                           Quality.qualityStrings[curQuality], logger.INFO)
                continue

            epObj = showObj.getEpisode(curSeason, curEp)

            # build a result object
            title = curResult["name"]
            url = curResult["url"]

            logger.log(u"Found result " + title + " at " + url)

            result = self.provider.getResult([epObj])
            result.show = showObj
            result.url = url
            result.name = title
            result.quality = curQuality
            result.release_group = curReleaseGroup
            result.version = curVersion
            result.content = None

            # add it to the list
            if epObj not in neededEps:
                neededEps[epObj] = [result]
            else:
                neededEps[epObj].append(result)

        # datetime stamp this search so cache gets cleared
        self.setLastSearch()

        return neededEps

