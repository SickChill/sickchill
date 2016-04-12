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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import time
import datetime
import itertools

import sickbeard
from sickbeard import db
from sickbeard import logger
from sickbeard.rssfeeds import getFeed
from sickbeard import show_name_helpers
from sickrage.helper.exceptions import AuthException, ex
from sickrage.show.Show import Show
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException


class CacheDBConnection(db.DBConnection):
    def __init__(self, providerName):
        db.DBConnection.__init__(self, 'cache.db')

        # Create the table if it's not already there
        try:
            if not self.hasTable(providerName):
                self.action(
                    "CREATE TABLE [" + providerName + "] (name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT, release_group TEXT)")
            else:
                sql_results = self.select("SELECT url, COUNT(url) AS count FROM [" + providerName + "] GROUP BY url HAVING count > 1")

                for cur_dupe in sql_results:
                    self.action("DELETE FROM [" + providerName + "] WHERE url = ?", [cur_dupe["url"]])

            # add unique index to prevent further dupes from happening if one does not exist
            self.action("CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON [" + providerName + "] (url)")

            # add release_group column to table if missing
            if not self.hasColumn(providerName, 'release_group'):
                self.addColumn(providerName, 'release_group', "TEXT", "")

            # add version column to table if missing
            if not self.hasColumn(providerName, 'version'):
                self.addColumn(providerName, 'version', "NUMERIC", "-1")

        except Exception as e:
            if str(e) != "table [" + providerName + "] already exists":
                raise

        # Create the table if it's not already there
        try:
            if not self.hasTable('lastUpdate'):
                self.action("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC)")
        except Exception as e:
            if str(e) != "table lastUpdate already exists":
                raise


class TVCache(object):
    def __init__(self, provider, **kwargs):
        self.provider = provider
        self.providerID = self.provider.get_id()
        self.providerDB = None
        self.minTime = kwargs.pop(u'min_time', 10)
        self.search_params = kwargs.pop(u'search_params', dict(RSS=['']))

    def _getDB(self):
        # init provider database if not done already
        if not self.providerDB:
            self.providerDB = CacheDBConnection(self.providerID)

        return self.providerDB

    def _clearCache(self):
        if self.shouldClearCache():
            cache_db_con = self._getDB()
            cache_db_con.action("DELETE FROM [" + self.providerID + "] WHERE 1")

    def _get_title_and_url(self, item):
        return self.provider._get_title_and_url(item)  # pylint:disable=protected-access

    def _getRSSData(self):
        return {u'entries': self.provider.search(self.search_params)} if self.search_params else None

    def _checkAuth(self, data):  # pylint:disable=unused-argument, no-self-use
        return True

    def _checkItemAuth(self, title, url):  # pylint:disable=unused-argument, no-self-use
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

                if cl:
                    cache_db_con = self._getDB()
                    cache_db_con.mass_action(cl)

        except AuthException as e:
            logger.log(u"Authentication error: " + ex(e), logger.ERROR)
        except Exception as e:
            logger.log(u"Error while searching " + self.provider.name + ", skipping: " + repr(e), logger.DEBUG)

    def getRSSFeed(self, url, params=None):
        if self.provider.login():
            return getFeed(url, params=params, request_hook=self.provider.get_url)
        return {'entries': []}

    @staticmethod
    def _translateTitle(title):
        return u'' + title.replace(' ', '.')

    @staticmethod
    def _translateLinkURL(url):
        return url.replace('&amp;', '&')

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)

        self._checkItemAuth(title, url)

        if title and url:
            title = self._translateTitle(title)
            url = self._translateLinkURL(url)

            # logger.log(u"Attempting to add item to cache: " + title, logger.DEBUG)
            return self._addCacheEntry(title, url)

        else:
            logger.log(
                u"The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable",
                logger.DEBUG)

        return False

    def _getLastUpdate(self):
        cache_db_con = self._getDB()
        sql_results = cache_db_con.select("SELECT time FROM lastUpdate WHERE provider = ?", [self.providerID])

        if sql_results:
            lastTime = int(sql_results[0]["time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())):
                lastTime = 0
        else:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    def _getLastSearch(self):
        cache_db_con = self._getDB()
        sql_results = cache_db_con.select("SELECT time FROM lastSearch WHERE provider = ?", [self.providerID])

        if sql_results:
            lastTime = int(sql_results[0]["time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())):
                lastTime = 0
        else:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    def setLastUpdate(self, toDate=None):
        if not toDate:
            toDate = datetime.datetime.today()

        cache_db_con = self._getDB()
        cache_db_con.upsert(
            "lastUpdate",
            {'time': int(time.mktime(toDate.timetuple()))},
            {'provider': self.providerID}
        )

    def setLastSearch(self, toDate=None):
        if not toDate:
            toDate = datetime.datetime.today()

        cache_db_con = self._getDB()
        cache_db_con.upsert(
            "lastSearch",
            {'time': int(time.mktime(toDate.timetuple()))},
            {'provider': self.providerID}
        )

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
                showObj = Show.find(sickbeard.show_list, indexer_id)

            try:
                parse_result = NameParser(showObj=showObj).parse(name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.log(u"{0}".format(error), logger.DEBUG)
                return None

            if not parse_result or not parse_result.series_name:
                return None

        # if we made it this far then lets add the parsed result to cache for usager later on
        season = parse_result.season_number if parse_result.season_number else 1
        episodes = parse_result.episode_numbers

        if season and episodes:
            # store episodes as a seperated string
            episodeText = "|" + "|".join({str(episode) for episode in episodes if episode}) + "|"

            # get the current timestamp
            cur_timestamp = int(time.mktime(datetime.datetime.today().timetuple()))

            # get quality of release
            quality = parse_result.quality

            assert isinstance(name, unicode)

            # get release group
            release_group = parse_result.release_group

            # get version
            version = parse_result.version

            logger.log(u"Added RSS item: [" + name + "] to cache: [" + self.providerID + "]", logger.DEBUG)

            return [
                "INSERT OR IGNORE INTO [" + self.providerID + "] (name, season, episodes, indexerid, url, time, quality, release_group, version) VALUES (?,?,?,?,?,?,?,?,?)",
                [name, season, episodeText, parse_result.show.indexerid, url, cur_timestamp, quality, release_group, version]]

    def searchCache(self, episode, manualSearch=False, downCurQuality=False):
        neededEps = self.findNeededEpisodes(episode, manualSearch, downCurQuality)
        return neededEps.get(episode, [])

    def listPropers(self, date=None):
        cache_db_con = self._getDB()
        sql = "SELECT * FROM [" + self.providerID + "] WHERE name LIKE '%.PROPER.%' OR name LIKE '%.REPACK.%'"

        if date is not None:
            sql += " AND time >= " + str(int(time.mktime(date.timetuple())))

        propers_results = cache_db_con.select(sql)
        return [x for x in propers_results if x['indexerid']]

    def findNeededEpisodes(self, episode, manualSearch=False, downCurQuality=False):  # pylint:disable=too-many-locals, too-many-branches
        neededEps = {}
        cl = []

        cache_db_con = self._getDB()
        if not episode:
            sql_results = cache_db_con.select("SELECT * FROM [" + self.providerID + "]")
        elif not isinstance(episode, list):
            sql_results = cache_db_con.select(
                "SELECT * FROM [" + self.providerID + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ?",
                [episode.show.indexerid, episode.season, "%|" + str(episode.episode) + "|%"])
        else:
            for epObj in episode:
                cl.append([
                    "SELECT * FROM [" + self.providerID + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND quality IN (" + ",".join(
                        [str(x) for x in epObj.wantedQuality]) + ")",
                    [epObj.show.indexerid, epObj.season, "%|" + str(epObj.episode) + "|%"]])

            sql_results = cache_db_con.mass_action(cl, fetchall=True)
            sql_results = list(itertools.chain(*sql_results))

        # for each cache entry
        for cur_result in sql_results:
            # get the show object, or if it's not one of our shows then ignore it
            showObj = Show.find(sickbeard.show_list, int(cur_result["indexerid"]))
            if not showObj:
                continue

            # ignored/required words, and non-tv junk
            if not show_name_helpers.filterBadReleases(cur_result["name"], show=showObj):
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not showObj.is_anime:
                logger.log(u"" + str(showObj.name) + " is not an anime, skiping", logger.DEBUG)
                continue

            # get season and ep data (ignoring multi-eps for now)
            cur_season = int(cur_result["season"])
            if cur_season == -1:
                continue

            cur_ep = cur_result["episodes"].split("|")[1]
            if not cur_ep:
                continue

            cur_ep = int(cur_ep)

            cur_quality = int(cur_result["quality"])
            cur_rls_group = cur_result["release_group"]
            cur_version = cur_result["version"]

            # if the show says we want that episode then add it to the list
            if not showObj.wantEpisode(cur_season, cur_ep, cur_quality, manualSearch, downCurQuality):
                logger.log(u"Ignoring " + cur_result["name"], logger.DEBUG)
                continue

            epObj = showObj.get_episode(cur_season, cur_ep)

            # build a result object
            title = cur_result["name"]
            url = cur_result["url"]

            logger.log(u"Found result " + title + " at " + url)

            result = self.provider.get_result([epObj])
            result.show = showObj
            result.url = url
            result.name = title
            result.quality = cur_quality
            result.release_group = cur_rls_group
            result.version = cur_version
            result.content = None

            # add it to the list
            if epObj not in neededEps:
                neededEps[epObj] = [result]
            else:
                neededEps[epObj].append(result)

        # datetime stamp this search so cache gets cleared
        self.setLastSearch()

        return neededEps
