# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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

import adba
import time
import datetime
import requests
import threading

import sickbeard
from sickbeard import db, helpers, logger
from sickbeard.indexers.indexer_config import INDEXER_TVDB

exception_dict = {}
anidb_exception_dict = {}
xem_exception_dict = {}

exceptionsCache = {}
exceptionsSeasonCache = {}

exceptionLock = threading.Lock()


def shouldRefresh(exList):
    """
    Check if we should refresh cache for items in exList

    :param exList: exception list to check if needs a refresh
    :return: True if refresh is needed
    """
    MAX_REFRESH_AGE_SECS = 86400  # 1 day

    cache_db_con = db.DBConnection('cache.db')
    rows = cache_db_con.select("SELECT last_refreshed FROM scene_exceptions_refresh WHERE list = ?", [exList])
    if rows:
        lastRefresh = int(rows[0]['last_refreshed'])
        return int(time.mktime(datetime.datetime.today().timetuple())) > lastRefresh + MAX_REFRESH_AGE_SECS
    else:
        return True


def setLastRefresh(exList):
    """
    Update last cache update time for shows in list

    :param exList: exception list to set refresh time
    """
    cache_db_con = db.DBConnection('cache.db')
    cache_db_con.upsert(
        "scene_exceptions_refresh",
        {'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple()))},
        {'list': exList}
    )


def get_scene_exceptions(indexer_id, season=-1):
    """
    Given a indexer_id, return a list of all the scene exceptions.
    """

    scene_exceptions_list = []

    if indexer_id not in exceptionsCache or season not in exceptionsCache[indexer_id]:
        cache_db_con = db.DBConnection('cache.db')
        exceptions = cache_db_con.select("SELECT show_name FROM scene_exceptions WHERE indexer_id = ? and season = ?",
                                         [indexer_id, season])
        if exceptions:
            scene_exceptions_list = list({cur_exception["show_name"] for cur_exception in exceptions})

            if indexer_id not in exceptionsCache:
                exceptionsCache[indexer_id] = {}
            exceptionsCache[indexer_id][season] = scene_exceptions_list
    else:
        scene_exceptions_list = exceptionsCache[indexer_id][season]

    # Add generic exceptions regardless of the season if there is no exception for season
    if season != -1 and not scene_exceptions_list:
        scene_exceptions_list += get_scene_exceptions(indexer_id, season=-1)

    return list({exception for exception in scene_exceptions_list})


def get_all_scene_exceptions(indexer_id):
    """
    Get all scene exceptions for a show ID

    :param indexer_id: ID to check
    :return: dict of exceptions
    """
    exceptionsDict = {}

    cache_db_con = db.DBConnection('cache.db')
    exceptions = cache_db_con.select("SELECT show_name,season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])

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
    exceptionsSeasonList = []

    if indexer_id not in exceptionsSeasonCache:
        cache_db_con = db.DBConnection('cache.db')
        sql_results = cache_db_con.select("SELECT DISTINCT(season) as season FROM scene_exceptions WHERE indexer_id = ?",
                                          [indexer_id])
        if sql_results:
            exceptionsSeasonList = list({int(x["season"]) for x in sql_results})

            if indexer_id not in exceptionsSeasonCache:
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
    cache_db_con = db.DBConnection('cache.db')
    exception_result = cache_db_con.select(
        "SELECT indexer_id, season FROM scene_exceptions WHERE LOWER(show_name) = ? ORDER BY season ASC",
        [show_name.lower()])
    if exception_result:
        return [(int(x["indexer_id"]), int(x["season"])) for x in exception_result]

    out = []
    all_exception_results = cache_db_con.select("SELECT show_name, indexer_id, season FROM scene_exceptions")

    for cur_exception in all_exception_results:

        cur_exception_name = cur_exception["show_name"]
        cur_indexer_id = int(cur_exception["indexer_id"])

        if show_name.lower() in (
                cur_exception_name.lower(),
                sickbeard.helpers.sanitizeSceneName(cur_exception_name).lower().replace('.', ' ')):

            logger.log(u"Scene exception lookup got indexer id {0}, using that".format
                       (cur_indexer_id), logger.DEBUG)

            out.append((cur_indexer_id, int(cur_exception["season"])))

    if out:
        return out

    return [(None, None)]


def retrieve_exceptions():  # pylint:disable=too-many-locals, too-many-branches
    """
    Looks up the exceptions on github, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Also clears the scene name cache.
    """

    do_refresh = False
    for indexer in sickbeard.indexerApi().indexers:
        if shouldRefresh(sickbeard.indexerApi(indexer).name):
            do_refresh = True

    if do_refresh:
        loc = sickbeard.indexerApi(INDEXER_TVDB).config['scene_loc']
        logger.log(u"Checking for scene exception updates from {0}".format(loc))

        try:
            jdata = helpers.getURL(loc, session=sickbeard.indexerApi(INDEXER_TVDB).session, returns='json')
        except Exception:
            jdata = None

        if not jdata:
            # When jdata is None, trouble connecting to github, or reading file failed
            logger.log(u"Check scene exceptions update failed. Unable to update from {0}".format(loc), logger.DEBUG)
        else:
            for indexer in sickbeard.indexerApi().indexers:
                try:
                    setLastRefresh(sickbeard.indexerApi(indexer).name)
                    for indexer_id in jdata[sickbeard.indexerApi(indexer).config['xem_origin']]:
                        alias_list = [
                            {scene_exception: int(scene_season)}
                            for scene_season in jdata[sickbeard.indexerApi(indexer).config['xem_origin']][indexer_id]
                            for scene_exception in jdata[sickbeard.indexerApi(indexer).config['xem_origin']][indexer_id][scene_season]
                        ]
                        exception_dict[indexer_id] = alias_list
                except Exception:
                    continue

    # XEM scene exceptions
    _xem_exceptions_fetcher()
    for xem_ex in xem_exception_dict:
        if xem_ex in exception_dict:
            exception_dict[xem_ex] += exception_dict[xem_ex]
        else:
            exception_dict[xem_ex] = xem_exception_dict[xem_ex]

    # AniDB scene exceptions
    _anidb_exceptions_fetcher()
    for anidb_ex in anidb_exception_dict:
        if anidb_ex in exception_dict:
            exception_dict[anidb_ex] += anidb_exception_dict[anidb_ex]
        else:
            exception_dict[anidb_ex] = anidb_exception_dict[anidb_ex]

    queries = []
    cache_db_con = db.DBConnection('cache.db')
    for cur_indexer_id in exception_dict:
        sql_ex = cache_db_con.select("SELECT show_name FROM scene_exceptions WHERE indexer_id = ?;", [cur_indexer_id])
        existing_exceptions = [x["show_name"] for x in sql_ex]
        if cur_indexer_id not in exception_dict:
            continue

        for cur_exception_dict in exception_dict[cur_indexer_id]:
            for ex in cur_exception_dict.iteritems():
                cur_exception, cur_season = ex
                if cur_exception not in existing_exceptions:
                    queries.append(
                        ["INSERT OR IGNORE INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?);",
                         [cur_indexer_id, cur_exception, cur_season]])
    if queries:
        cache_db_con.mass_action(queries)
        logger.log(u"Updated scene exceptions", logger.DEBUG)

    # cleanup
    exception_dict.clear()
    anidb_exception_dict.clear()
    xem_exception_dict.clear()


def update_scene_exceptions(indexer_id, scene_exceptions, season=-1):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    """
    cache_db_con = db.DBConnection('cache.db')
    cache_db_con.action('DELETE FROM scene_exceptions WHERE indexer_id=? and season=?', [indexer_id, season])

    logger.log(u"Updating scene exceptions", logger.INFO)

    # A change has been made to the scene exception list. Let's clear the cache, to make this visible
    if indexer_id in exceptionsCache:
        exceptionsCache[indexer_id] = {}
        exceptionsCache[indexer_id][season] = scene_exceptions

    for cur_exception in scene_exceptions:
        cache_db_con.action("INSERT INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?)",
                            [indexer_id, cur_exception, season])


def _anidb_exceptions_fetcher():
    if shouldRefresh('anidb'):
        logger.log(u"Checking for scene exception updates for AniDB")
        for show in sickbeard.show_list:
            if show.is_anime and show.indexer == 1:
                try:
                    anime = adba.Anime(None, name=show.name, tvdbid=show.indexerid, autoCorrectName=True)
                except Exception:
                    continue
                else:
                    if anime.name and anime.name != show.name:
                        anidb_exception_dict[show.indexerid] = [{anime.name: -1}]

        setLastRefresh('anidb')
    return anidb_exception_dict

xem_session = helpers.make_session()

def _xem_exceptions_fetcher():
    if shouldRefresh('xem'):
        for indexer in sickbeard.indexerApi().indexers:
            logger.log(u"Checking for XEM scene exception updates for {0}".format
                       (sickbeard.indexerApi(indexer).name))

            url = "http://thexem.de/map/allNames?origin={0}&seasonNumbers=1".format(sickbeard.indexerApi(indexer).config['xem_origin'])

            parsedJSON = helpers.getURL(url, session=xem_session, timeout=90, returns='json')
            if not parsedJSON:
                logger.log(u"Check scene exceptions update failed for {0}, Unable to get URL: {1}".format
                           (sickbeard.indexerApi(indexer).name, url), logger.DEBUG)
                continue

            if parsedJSON['result'] == 'failure':
                continue

            for indexerid, names in parsedJSON['data'].iteritems():
                try:
                    xem_exception_dict[int(indexerid)] = names
                except Exception as error:
                    logger.log(u"XEM: Rejected entry: indexerid:{0}; names:{1}".format(indexerid, names), logger.WARNING)
                    logger.log(u"XEM: Rejected entry error message:{0}".format(error), logger.DEBUG)

        setLastRefresh('xem')

    return xem_exception_dict


def getSceneSeasons(indexer_id):
    """get a list of season numbers that have scene exceptions"""
    cache_db_con = db.DBConnection('cache.db')
    seasons = cache_db_con.select("SELECT DISTINCT season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])
    return [cur_exception["season"] for cur_exception in seasons]
