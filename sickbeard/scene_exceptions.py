# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

import re
import time
import threading
import datetime

import sickbeard
import adba
from sickbeard import helpers
from sickbeard import logger
from sickbeard import db
import requests

exception_dict = {}
anidb_exception_dict = {}
xem_exception_dict = {}

exceptionsCache = {}
exceptionsSeasonCache = {}

exceptionLock = threading.Lock()

def shouldRefresh(list):
    """
    Check if we should refresh cache for items in list

    :param list: list to check
    :return: True if refresh is needed
    """
    MAX_REFRESH_AGE_SECS = 86400  # 1 day

    myDB = db.DBConnection('cache.db')
    rows = myDB.select("SELECT last_refreshed FROM scene_exceptions_refresh WHERE list = ?", [list])
    if rows:
        lastRefresh = int(rows[0]['last_refreshed'])
        return int(time.mktime(datetime.datetime.today().timetuple())) > lastRefresh + MAX_REFRESH_AGE_SECS
    else:
        return True

def setLastRefresh(list):
    """
    Update last cache update time for shows in list

    :param list: list to check
    """
    myDB = db.DBConnection('cache.db')
    myDB.upsert("scene_exceptions_refresh",
                {'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple()))},
                {'list': list})

def get_scene_exceptions(indexer_id, season=-1):
    """
    Given a indexer_id, return a list of all the scene exceptions.
    """
    global exceptionsCache
    exceptionsList = []

    if indexer_id not in exceptionsCache or season not in exceptionsCache[indexer_id]:
        myDB = db.DBConnection('cache.db')
        exceptions = myDB.select("SELECT show_name FROM scene_exceptions WHERE indexer_id = ? and season = ?",
                                 [indexer_id, season])
        if exceptions:
            exceptionsList = list(set([cur_exception["show_name"] for cur_exception in exceptions]))

            if not indexer_id in exceptionsCache:
                exceptionsCache[indexer_id] = {}
            exceptionsCache[indexer_id][season] = exceptionsList
    else:
        exceptionsList = exceptionsCache[indexer_id][season]

    if season == 1:  # if we where looking for season 1 we can add generic names
        exceptionsList += get_scene_exceptions(indexer_id, season=-1)

    return exceptionsList


def get_all_scene_exceptions(indexer_id):
    """
    Get all scene exceptions for a show ID

    :param indexer_id: ID to check
    :return: dict of exceptions
    """
    exceptionsDict = {}

    myDB = db.DBConnection('cache.db')
    exceptions = myDB.select("SELECT show_name,season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])

    if exceptions:
        for cur_exception in exceptions:
            if not cur_exception["season"] in exceptionsDict:
                exceptionsDict[cur_exception["season"]] = []
            exceptionsDict[cur_exception["season"]].append(cur_exception["show_name"])

    return exceptionsDict


def get_scene_seasons(indexer_id):
    """
    return a list of season numbers that have scene exceptions
    """
    global exceptionsSeasonCache
    exceptionsSeasonList = []

    if indexer_id not in exceptionsSeasonCache:
        myDB = db.DBConnection('cache.db')
        sqlResults = myDB.select("SELECT DISTINCT(season) as season FROM scene_exceptions WHERE indexer_id = ?",
                                 [indexer_id])
        if sqlResults:
            exceptionsSeasonList = list(set([int(x["season"]) for x in sqlResults]))

            if not indexer_id in exceptionsSeasonCache:
                exceptionsSeasonCache[indexer_id] = {}

            exceptionsSeasonCache[indexer_id] = exceptionsSeasonList
    else:
        exceptionsSeasonList = exceptionsSeasonCache[indexer_id]

    return exceptionsSeasonList


def get_scene_exception_by_name(show_name):
    return get_scene_exception_by_name_multiple(show_name)[0]


def get_scene_exception_by_name_multiple(show_name):
    """
    Given a show name, return the indexerid of the exception, None if no exception
    is present.
    """

    # try the obvious case first
    myDB = db.DBConnection('cache.db')
    exception_result = myDB.select(
        "SELECT indexer_id, season FROM scene_exceptions WHERE LOWER(show_name) = ? ORDER BY season ASC",
        [show_name.lower()])
    if exception_result:
        return [(int(x["indexer_id"]), int(x["season"])) for x in exception_result]

    out = []
    all_exception_results = myDB.select("SELECT show_name, indexer_id, season FROM scene_exceptions")

    for cur_exception in all_exception_results:

        cur_exception_name = cur_exception["show_name"]
        cur_indexer_id = int(cur_exception["indexer_id"])
        cur_season = int(cur_exception["season"])

        if show_name.lower() in (
                cur_exception_name.lower(),
                sickbeard.helpers.sanitizeSceneName(cur_exception_name).lower().replace('.', ' ')):
            logger.log(u"Scene exception lookup got indexer id " + str(cur_indexer_id) + u", using that", logger.DEBUG)
            out.append((cur_indexer_id, cur_season))

    if out:
        return out

    return [(None, None)]


def retrieve_exceptions():
    """
    Looks up the exceptions on github, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Also clears the scene name cache.
    """
    global exception_dict, anidb_exception_dict, xem_exception_dict

    # exceptions are stored in submodules in this repo, sourced from the github repos
    # TODO: `git submodule update`
    for indexer in sickbeard.indexerApi().indexers:
        if shouldRefresh(sickbeard.indexerApi(indexer).name):
            logger.log(u"Checking for scene exception updates for " + sickbeard.indexerApi(indexer).name + "")

            loc = sickbeard.indexerApi(indexer).config['scene_loc']
            try:
                data = helpers.getURL(loc, session=sickbeard.indexerApi(indexer).session)
            except Exception:
                continue

            if data is None:
                # When data is None, trouble connecting to github, or reading file failed
                logger.log(u"Check scene exceptions update failed. Unable to update from: " + loc, logger.WARNING)
                continue

            setLastRefresh(sickbeard.indexerApi(indexer).name)

            # each exception is on one line with the format indexer_id: 'show name 1', 'show name 2', etc
            for cur_line in data.splitlines():
                indexer_id, sep, aliases = cur_line.partition(':')  # @UnusedVariable

                if not aliases:
                    continue

                indexer_id = int(indexer_id)

                # regex out the list of shows, taking \' into account
                # alias_list = [re.sub(r'\\(.)', r'\1', x) for x in re.findall(r"'(.*?)(?<!\\)',?", aliases)]
                alias_list = [{re.sub(r'\\(.)', r'\1', x): -1} for x in re.findall(r"'(.*?)(?<!\\)',?", aliases)]
                exception_dict[indexer_id] = alias_list
                del alias_list

            # cleanup
            del data

    # XEM scene exceptions
    _xem_exceptions_fetcher()
    for xem_ex in xem_exception_dict:
        if xem_ex in exception_dict:
            exception_dict[xem_ex] = exception_dict[xem_ex] + xem_exception_dict[xem_ex]
        else:
            exception_dict[xem_ex] = xem_exception_dict[xem_ex]

    # AniDB scene exceptions
    _anidb_exceptions_fetcher()
    for anidb_ex in anidb_exception_dict:
        if anidb_ex in exception_dict:
            exception_dict[anidb_ex] = exception_dict[anidb_ex] + anidb_exception_dict[anidb_ex]
        else:
            exception_dict[anidb_ex] = anidb_exception_dict[anidb_ex]

    queries = []
    myDB = db.DBConnection('cache.db')
    for cur_indexer_id in exception_dict:
        sql_ex = myDB.select("SELECT * FROM scene_exceptions WHERE indexer_id = ?;", [cur_indexer_id])
        existing_exceptions = [x["show_name"] for x in sql_ex]
        if not cur_indexer_id in exception_dict:
            continue

        for cur_exception_dict in exception_dict[cur_indexer_id]:
            for ex in cur_exception_dict.iteritems():
                cur_exception, curSeason = ex
                if cur_exception not in existing_exceptions:
                    queries.append(["INSERT OR IGNORE INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?);",
                            [cur_indexer_id, cur_exception, curSeason]])
    if queries:
        myDB.mass_action(queries)
        logger.log(u"Updated scene exceptions", logger.DEBUG)
    else:
        logger.log(u"No scene exceptions update needed", logger.DEBUG)

    # cleanup
    exception_dict.clear()
    anidb_exception_dict.clear()
    xem_exception_dict.clear()

def update_scene_exceptions(indexer_id, scene_exceptions, season=-1):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    """
    global exceptionsCache
    myDB = db.DBConnection('cache.db')
    myDB.action('DELETE FROM scene_exceptions WHERE indexer_id=? and season=?', [indexer_id, season])

    logger.log(u"Updating scene exceptions", logger.INFO)
    
    # A change has been made to the scene exception list. Let's clear the cache, to make this visible
    if indexer_id in exceptionsCache:
        exceptionsCache[indexer_id] = {}
        exceptionsCache[indexer_id][season] = scene_exceptions

    for cur_exception in scene_exceptions:
        myDB.action("INSERT INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?)",
                    [indexer_id, cur_exception, season])

def _anidb_exceptions_fetcher():
    global anidb_exception_dict

    if shouldRefresh('anidb'):
        logger.log(u"Checking for scene exception updates for AniDB")
        for show in sickbeard.showList:
            if show.is_anime and show.indexer == 1:
                try:
                    anime = adba.Anime(None, name=show.name, tvdbid=show.indexerid, autoCorrectName=True)
                except:
                    continue
                else:
                    if anime.name and anime.name != show.name:
                        anidb_exception_dict[show.indexerid] = [{anime.name: -1}]

        setLastRefresh('anidb')
    return anidb_exception_dict


xem_session = requests.Session()

def _xem_exceptions_fetcher():
    global xem_exception_dict
    global xem_session

    if shouldRefresh('xem'):
        for indexer in sickbeard.indexerApi().indexers:
            logger.log(u"Checking for XEM scene exception updates for " + sickbeard.indexerApi(indexer).name)

            url = "http://thexem.de/map/allNames?origin=%s&seasonNumbers=1" % sickbeard.indexerApi(indexer).config[
                'xem_origin']

            parsedJSON = helpers.getURL(url, session=xem_session, timeout = 90, json=True)
            if not parsedJSON:
                logger.log(u"Check scene exceptions update failed for " + sickbeard.indexerApi(
                    indexer).name + ", Unable to get URL: " + url, logger.ERROR)
                continue

            if parsedJSON['result'] == 'failure':
                continue

            for indexerid, names in parsedJSON['data'].iteritems():
                try:
                    xem_exception_dict[int(indexerid)] = names
                except Exception as e:
                    logger.log(u"XEM: Rejected entry: indexerid:{0}; names:{1}".format(indexerid, names), logger.WARNING)
                    logger.log(u"XEM: Rejected entry error message:{0}".format(str(e)), logger.DEBUG)

        setLastRefresh('xem')

    return xem_exception_dict


def getSceneSeasons(indexer_id):
    """get a list of season numbers that have scene exceptions"""
    myDB = db.DBConnection('cache.db')
    seasons = myDB.select("SELECT DISTINCT season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])
    return [cur_exception["season"] for cur_exception in seasons]
