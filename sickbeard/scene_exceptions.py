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

import re
import threading
import sickbeard

from lib import adba
from sickbeard import helpers
from sickbeard import name_cache
from sickbeard import logger
from sickbeard import db

exceptionCache = {}
exceptionSeasonCache = {}
exceptionIndexerCache = {}

def get_scene_exceptions(indexer_id, season=-1):
    """
    Given a indexer_id, return a list of all the scene exceptions.
    """

    global exceptionCache

    if indexer_id not in exceptionCache or season not in exceptionCache[indexer_id]:
        myDB = db.DBConnection("cache.db")
        exceptions = myDB.select("SELECT show_name FROM scene_exceptions WHERE indexer_id = ? and season = ?",
                                 [indexer_id, season])
        exceptionsList = list(set([cur_exception["show_name"] for cur_exception in exceptions]))

        if len(exceptionsList):
            try:
                exceptionCache[indexer_id][season] = exceptionsList
            except:
                exceptionCache[indexer_id] = {season:exceptionsList}
    else:
        exceptionsList = list(set(exceptionCache[indexer_id][season]))

    if season == 1:  # if we where looking for season 1 we can add generic names
        exceptionsList += get_scene_exceptions(indexer_id, season=-1)

    return exceptionsList

def get_all_scene_exceptions(indexer_id):
    myDB = db.DBConnection("cache.db")
    exceptions = myDB.select("SELECT show_name,season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])
    exceptionsList = {}
    [cur_exception["show_name"] for cur_exception in exceptions]
    for cur_exception in exceptions:
        if not cur_exception["season"] in exceptionsList:
            exceptionsList[cur_exception["season"]] = []
        exceptionsList[cur_exception["season"]].append(cur_exception["show_name"])

    return exceptionsList

def get_scene_seasons(indexer_id):
    """
    return a list of season numbers that have scene exceptions
    """
    global exceptionSeasonCache
    if indexer_id not in exceptionSeasonCache:
        myDB = db.DBConnection("cache.db")
        sqlResults = myDB.select("SELECT DISTINCT(season) as season FROM scene_exceptions WHERE indexer_id = ?",
                                 [indexer_id])
        exceptionSeasonCache[indexer_id] = [int(x["season"]) for x in sqlResults]

    return exceptionSeasonCache[indexer_id]


def get_scene_exception_by_name(show_name):
    return get_scene_exception_by_name_multiple(show_name)[0]


def get_scene_exception_by_name_multiple(show_name):
    """
    Given a show name, return the indexerid of the exception, None if no exception
    is present.
    """

    myDB = db.DBConnection("cache.db")

    # try the obvious case first
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
        cur_exception_name.lower(), sickbeard.helpers.sanitizeSceneName(cur_exception_name).lower().replace('.', ' ')):
            logger.log(u"Scene exception lookup got indexer id " + str(cur_indexer_id) + u", using that", logger.DEBUG)
            out.append((cur_indexer_id, cur_season))
    if out:
        return out
    else:
        return [(None, None)]


def retrieve_exceptions():
    """
    Looks up the exceptions on github, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Also clears the scene name cache.
    """

    global exceptionCache, exceptionSeasonCache

    exception_dict = {}
    exceptionCache = {}
    exceptionSeasonCache = {}

    # exceptions are stored on github pages
    for indexer in sickbeard.indexerApi().indexers:
        logger.log(u"Checking for scene exception updates for " + sickbeard.indexerApi(indexer).name + "")

        url = sickbeard.indexerApi(indexer).config['scene_url']

        url_data = helpers.getURL(url)

        if url_data is None:
            # When urlData is None, trouble connecting to github
            logger.log(u"Check scene exceptions update failed. Unable to get URL: " + url, logger.ERROR)
            continue

        else:
            # each exception is on one line with the format indexer_id: 'show name 1', 'show name 2', etc
            for cur_line in url_data.splitlines():
                cur_line = cur_line.decode('utf-8')
                indexer_id, sep, aliases = cur_line.partition(':')  # @UnusedVariable

                if not aliases:
                    continue

                indexer_id = int(indexer_id)

                # regex out the list of shows, taking \' into account
                # alias_list = [re.sub(r'\\(.)', r'\1', x) for x in re.findall(r"'(.*?)(?<!\\)',?", aliases)]
                alias_list = [{re.sub(r'\\(.)', r'\1', x): -1} for x in re.findall(r"'(.*?)(?<!\\)',?", aliases)]

                exception_dict[indexer_id] = alias_list

        logger.log(u"Checking for XEM scene exception updates for " + sickbeard.indexerApi(indexer).name)
        xem_exceptions = _xem_excpetions_fetcher(indexer)
        for xem_ex in xem_exceptions:  # anidb xml anime exceptions
            if xem_ex in exception_dict:
                exception_dict[xem_ex] = exception_dict[xem_ex] + xem_exceptions[xem_ex]
            else:
                exception_dict[xem_ex] = xem_exceptions[xem_ex]

    logger.log(u"Checking for scene exception updates for AniDB")
    local_exceptions = _retrieve_anidb_mainnames()
    for local_ex in local_exceptions:  # anidb xml anime exceptions
        if local_ex in exception_dict:
            exception_dict[local_ex] = exception_dict[local_ex] + local_exceptions[local_ex]
        else:
            exception_dict[local_ex] = local_exceptions[local_ex]

    myDB = db.DBConnection("cache.db")

    changed_exceptions = False

    # write all the exceptions we got off the net into the database
    for cur_indexer_id in exception_dict:

        # get a list of the existing exceptions for this ID
        existing_exceptions = [x["show_name"] for x in
                               myDB.select("SELECT * FROM scene_exceptions WHERE indexer_id = ?", [cur_indexer_id])]

        for cur_exception_dict in exception_dict[cur_indexer_id]:
            cur_exception, curSeason = cur_exception_dict.items()[0]

            # if this exception isn't already in the DB then add it
            if cur_exception not in existing_exceptions:
                myDB.action("INSERT INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?)",
                            [cur_indexer_id, cur_exception, curSeason])
                changed_exceptions = True

    # since this could invalidate the results of the cache we clear it out after updating
    if changed_exceptions:
        logger.log(u"Updated scene exceptions")
        name_cache.clearCache()
    else:
        logger.log(u"No scene exceptions update needed")

    # build indexer scene name cache
    buildIndexerCache()

def update_scene_exceptions(indexer_id, scene_exceptions):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    """

    global exceptionIndexerCache

    myDB = db.DBConnection("cache.db")

    myDB.action('DELETE FROM scene_exceptions WHERE indexer_id=?', [indexer_id])

    logger.log(u"Updating internal scene name cache", logger.MESSAGE)
    for cur_exception, cur_season in scene_exceptions:
        exceptionIndexerCache[helpers.full_sanitizeSceneName(cur_exception)] = indexer_id
        myDB.action("INSERT INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?)",
                    [indexer_id, cur_exception, cur_season])

    name_cache.clearCache()

def _retrieve_anidb_mainnames():
    anidb_mainNames = {}
    for show in sickbeard.showList:
        if show.is_anime and show.indexer == 1:
            try:
                anime = adba.Anime(None, name=show.name, tvdbid=show.indexerid, autoCorrectName=True)
            except:
                continue
            else:
                if anime.name and anime.name != show.name:
                    anidb_mainNames[show.indexerid] = [{anime.name: -1}]

    return anidb_mainNames


def _xem_excpetions_fetcher(indexer):
    exception_dict = {}

    url = "http://thexem.de/map/allNames?origin=%s&seasonNumbers=1" % sickbeard.indexerApi(indexer).config['xem_origin']

    url_data = helpers.getURL(url, json=True)
    if url_data is None:
        logger.log(u"Check scene exceptions update failed. Unable to get URL: " + url, logger.ERROR)
        return exception_dict

    if url_data['result'] == 'failure':
        return exception_dict

    for indexerid, names in url_data['data'].items():
        exception_dict[int(indexerid)] = names

    return exception_dict


def getSceneSeasons(indexer_id):
    """get a list of season numbers that have scene excpetions
    """
    myDB = db.DBConnection("cache.db")
    seasons = myDB.select("SELECT DISTINCT season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])
    return [cur_exception["season"] for cur_exception in seasons]

def buildIndexerCache():
    logger.log(u"Updating internal scene name cache", logger.MESSAGE)
    global exceptionIndexerCache
    exceptionIndexerCache = {}

    for show in sickbeard.showList:
        for curSeason in [-1] + sickbeard.scene_exceptions.get_scene_seasons(show.indexerid):
            exceptionIndexerCache[helpers.full_sanitizeSceneName(show.name)] = show.indexerid
            for name in get_scene_exceptions(show.indexerid, season=curSeason):
                exceptionIndexerCache[name] = show.indexerid
                exceptionIndexerCache[helpers.full_sanitizeSceneName(name)] = show.indexerid

    logger.log(u"Updated internal scene name cache", logger.MESSAGE)
    logger.log(u"Internal scene name cache set to: " + str(exceptionIndexerCache), logger.DEBUG)