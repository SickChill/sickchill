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
import urllib2

import sickbeard
from sickbeard import db
from sickbeard import logger
from sickbeard.rssfeeds import getFeed
from sickbeard import show_name_helpers
from sickrage.helper.encoding import ss
from sickrage.helper.exceptions import AuthException, ex
from sickrage.show.Show import Show
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException


class CacheDBConnection(db.DBConnection):
    def __init__(self, providerName):
        db.DBConnection.__init__(self, u'cache.db')

        # Create the table if it's not already there
        try:
            if not self.hasTable(providerName):
                self.action(b'CREATE TABLE [{provider}] (name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT, release_group TEXT)'.format(provider=providerName))
            else:
                sql_results = self.select(b'SELECT url, COUNT(url) AS count FROM [{provider}] GROUP BY url HAVING count > 1'.format(provider=providerName))

                for cur_dupe in sql_results:
                    self.action(b'DELETE FROM [{provider}] WHERE url = ?'.format(provider=providerName), [cur_dupe[b'url']])

            # add unique index to prevent further dupes from happening if one does not exist
            self.action(b'CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON [{provider}] (url)'.format(provider=providerName))

            # add release_group column to table if missing
            if not self.hasColumn(providerName, b'release_group'):
                self.addColumn(providerName, b'release_group', b'TEXT', b'')

            # add version column to table if missing
            if not self.hasColumn(providerName, b'version'):
                self.addColumn(providerName, b'version', b'NUMERIC', b'-1')

        except Exception as e:
            if str(e) != u'table [{}] already exists'.format(providerName):
                raise

        # Create the table if it's not already there
        try:
            if not self.hasTable(b'lastUpdate'):
                self.action(b'CREATE TABLE lastUpdate (provider TEXT, time NUMERIC)')
        except Exception as e:
            if str(e) != u'table lastUpdate already exists':
                raise


class TVCache(object):
    def __init__(self, provider, **kwargs):
        self.provider = provider
        self.providerID = self.provider.get_id()
        self.providerDB = None
        self.minTime = kwargs.pop(u'min_time', 10)
        self.search_params = kwargs.pop(u'search_params', dict(RSS=[u'']))

    def _getDB(self):
        # init provider database if not done already
        if not self.providerDB:
            self.providerDB = CacheDBConnection(self.providerID)

        return self.providerDB

    def _clearCache(self):
        if self.shouldClearCache():
            cache_db_con = self._getDB()
            cache_db_con.action(b'DELETE FROM [{provider}] WHERE 1'.format(provider=self.providerID))

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
                for item in data[u'entries'] or []:
                    ci = self._parseItem(item)
                    if ci is not None:
                        cl.append(ci)

                if len(cl) > 0:
                    cache_db_con = self._getDB()
                    cache_db_con.mass_action(cl)

        except AuthException as error:
            logger.log(u'Authentication error: {error}'.format
                       (error=ex(error)), logger.ERROR)
        except Exception as error:
            logger.log(u'Error while searching {provider}, skipping: {error!r}'.format
                       (provider=self.provider.name, error=error), logger.DEBUG)

    def getRSSFeed(self, url):
        handlers = []

        if sickbeard.PROXY_SETTING:
            logger.log(u'Using global proxy for url: {url}'.format(url=url), logger.DEBUG)
            scheme, address = urllib2.splittype(sickbeard.PROXY_SETTING)
            address = sickbeard.PROXY_SETTING if scheme else u'http://' + sickbeard.PROXY_SETTING
            handlers = [urllib2.ProxyHandler({u'http': address, u'https': address})]
            self.provider.headers.update({u'Referer': address})
        elif u'Referer' in self.provider.headers:
            self.provider.headers.pop(u'Referer')

        return getFeed(
            url,
            request_headers=self.provider.headers,
            handlers=handlers)

    @staticmethod
    def _translateTitle(title):
        return u'{name}'.format(name=title).replace(u' ', u'.')

    @staticmethod
    def _translateLinkURL(url):
        return url.replace(u'&amp;', u'&')

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)

        self._checkItemAuth(title, url)

        if title and url:
            title = self._translateTitle(title)
            url = self._translateLinkURL(url)

            # logger.log(u'Attempting to add item to cache: {name}'.format(name=title), logger.DEBUG)
            return self._addCacheEntry(title, url)

        else:
            logger.log(u'The data returned from the {provider} feed is incomplete, this result is unusable'.format
                       (provider=self.provider.name), logger.DEBUG)

        return False

    def _getLastUpdate(self):
        cache_db_con = self._getDB()
        sql_results = cache_db_con.select(b'SELECT time FROM lastUpdate WHERE provider = ?', [self.providerID])

        if sql_results:
            lastTime = int(sql_results[0][b'time'])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())):
                lastTime = 0
        else:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    def _getLastSearch(self):
        cache_db_con = self._getDB()
        sql_results = cache_db_con.select(b'SELECT time FROM lastSearch WHERE provider = ?', [self.providerID])

        if sql_results:
            lastTime = int(sql_results[0][b'time'])
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
            b'lastUpdate',
            {b'time': int(time.mktime(toDate.timetuple()))},
            {b'provider': self.providerID}
        )

    def setLastSearch(self, toDate=None):
        if not toDate:
            toDate = datetime.datetime.today()

        cache_db_con = self._getDB()
        cache_db_con.upsert(
            b'lastSearch',
            {b'time': int(time.mktime(toDate.timetuple()))},
            {b'provider': self.providerID}
        )

    lastUpdate = property(_getLastUpdate)
    lastSearch = property(_getLastSearch)

    def shouldUpdate(self):
        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.lastUpdate < datetime.timedelta(minutes=self.minTime):
            logger.log(u'Last update was too soon, using old cache: {update}. Updated less then {minutes} minutes ago'.format
                       (update=self.lastUpdate, minutes=self.minTime), logger.DEBUG)
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
                showObj = Show.find(sickbeard.showList, indexer_id)

            try:
                parse_result = NameParser(showObj=showObj).parse(name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.log(u'{error}'.format(error=error), logger.DEBUG)
                return None

            if not parse_result or not parse_result.series_name:
                return None

        # if we made it this far then lets add the parsed result to cache for usager later on
        season = parse_result.season_number if parse_result.season_number else 1
        episodes = parse_result.episode_numbers

        if season and episodes:
            # store episodes as a separated string
            episodeText = u'|{episodes}|'.format(episodes=u'|'.join({str(episode) for episode in episodes if episode}))

            # get the current timestamp
            curTimestamp = int(time.mktime(datetime.datetime.today().timetuple()))

            # get quality of release
            quality = parse_result.quality

            name = ss(name)

            # get release group
            release_group = parse_result.release_group

            # get version
            version = parse_result.version

            logger.log(u'Added RSS item: [{name}] to cache: [{provider}]'.format
                       (name=name.decode('utf-8'), provider=self.providerID), logger.DEBUG)

            return [b'INSERT OR IGNORE INTO [{provider}}] (name, season, episodes, indexerid, url, time, quality, release_group, version) VALUES (?,?,?,?,?,?,?,?,?)'.format
                    (provider=self.providerID), [name, season, episodeText, parse_result.show.indexerid, url, curTimestamp, quality, release_group, version]]

    def searchCache(self, episode, manualSearch=False, downCurQuality=False):
        neededEps = self.findNeededEpisodes(episode, manualSearch, downCurQuality)
        return neededEps[episode] if episode in neededEps else []

    def listPropers(self, date=None):
        cache_db_con = self._getDB()
        sql = b"SELECT * FROM [{provider}] WHERE name LIKE '%.PROPER.%' OR name LIKE '%.REPACK.%'".format(provider=self.providerID)

        if date is not None:
            sql += b' AND time >= {date}'.format(date=int(time.mktime(date.timetuple())))

        propers_results = cache_db_con.select(sql)
        return [result for result in propers_results if result[b'indexerid']]

    def findNeededEpisodes(self, episode, manualSearch=False, downCurQuality=False):  # pylint:disable=too-many-locals, too-many-branches
        neededEps = {}
        cl = []

        cache_db_con = self._getDB()
        if not episode:
            sql_results = cache_db_con.select(b'SELECT * FROM [{provider}]'.format(provider=self.providerID))
        elif not isinstance(episode, list):
            sql_results = cache_db_con.select(
                b'SELECT * FROM [{provider}] WHERE indexerid = ? AND season = ? AND episodes LIKE ?'.format
                (provider=self.providerID),
                [episode.show.indexerid, episode.season, b'%|{episode}|%'.format(episode=episode.episode)])
        else:
            for epObj in episode:
                cl.append([
                    b'SELECT * FROM [{provider}] WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND quality IN ({qualities})'.format
                    (provider=self.providerID, qualities=b','.join([str(x) for x in epObj.wantedQuality])),
                    [epObj.show.indexerid, epObj.season, b'%|{episode}|%'.format(episode=epObj.episode)]])

            sql_results = cache_db_con.mass_action(cl, fetchall=True)
            sql_results = list(itertools.chain(*sql_results))

        # for each cache entry
        for curResult in sql_results:
            # ignored/required words, and non-tv junk
            if not show_name_helpers.filterBadReleases(curResult[b'name']):
                continue

            # get the show object, or if it's not one of our shows then ignore it
            showObj = Show.find(sickbeard.showList, int(curResult[b'indexerid']))
            if not showObj:
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not showObj.is_anime:
                logger.log(u'{name} is not an anime, skipping'.format(name=showObj.name), logger.DEBUG)
                continue

            # get season and ep data (ignoring multi-eps for now)
            curSeason = int(curResult[b'season'])
            if curSeason == -1:
                continue

            curEp = curResult[b'episodes'].split(b'|')[1]
            if not curEp:
                continue

            curEp = int(curEp)

            curQuality = int(curResult[b'quality'])
            curReleaseGroup = curResult[b'release_group']
            curVersion = curResult[b'version']

            # if the show says we want that episode then add it to the list
            if not showObj.wantEpisode(curSeason, curEp, curQuality, manualSearch, downCurQuality):
                logger.log(u'Ignoring {name}'.format(name=curResult[b'name']), logger.DEBUG)
                continue

            epObj = showObj.getEpisode(curSeason, curEp)

            # build a result object
            title = curResult[b'name']
            url = curResult[b'url']

            logger.log(u'Found result {name} at {url}'.format(name=title, url=url))

            result = self.provider.get_result([epObj])
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
