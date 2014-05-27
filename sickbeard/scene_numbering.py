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
#
# Created on Sep 20, 2012
# @author: Dermot Buckley <dermot@buckley.ie>
# @copyright: Dermot Buckley
#

import time
import traceback

try:
    import json
except ImportError:
    from lib import simplejson as json

import sickbeard

from sickbeard import logger
from sickbeard import db
from sickbeard.exceptions import ex
from lib import requests

MAX_XEM_AGE_SECS = 86400  # 1 day


def get_scene_numbering(indexer_id, indexer, season, episode, absolute_number=None, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode), with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise 
    returns the TVDB and TVRAGE numbering.
    (so the return values will always be set)
    
    @param indexer_id: int
    @param season: int
    @param episode: int
    @param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    @return: (int, int) a tuple with (season, episode)   
    """
    if indexer_id is None or season is None or episode is None:
        return (season, episode, absolute_number)

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    result = find_scene_numbering(indexer_id, indexer, season, episode, absolute_number)
    if result:
        return result
    else:
        if fallback_to_xem:
            xem_result = find_xem_numbering(indexer_id, indexer, season, episode, absolute_number)
            if xem_result:
                return xem_result
        return (season, episode, absolute_number)

def find_scene_numbering(indexer_id, indexer, season, episode, absolute_number=None):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    if indexer_id is None or season is None or episode is None:
        return (season, episode, absolute_number)

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    myDB = db.DBConnection()

    rows = myDB.select(
        "SELECT scene_season, scene_episode, scene_absolute_number FROM scene_numbering WHERE indexer = ? and indexer_id = ? and season = ? and episode = ?",
        [indexer, indexer_id, season, episode])
    if rows:
        return (int(rows[0]["scene_season"]), int(rows[0]["scene_episode"]), int(rows[0]["scene_absolute_number"]))


def get_indexer_numbering(indexer_id, indexer, sceneSeason, sceneEpisode, sceneAbsoluteNumber=None, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode) with the TVDB and TVRAGE numbering for (sceneSeason, sceneEpisode)
    (this works like the reverse of get_scene_numbering)
    """
    if indexer_id is None or sceneSeason is None or sceneEpisode is None:
        return (sceneSeason, sceneEpisode)

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    myDB = db.DBConnection()

    rows = myDB.select(
        "SELECT season, episode, absolute_number FROM scene_numbering WHERE indexer = ? and indexer_id = ? and scene_season = ? and scene_episode = ?",
        [indexer, indexer_id, sceneSeason, sceneEpisode])
    if rows:
        return (int(rows[0]["season"]), int(rows[0]["episode"]), int(rows[0]["absolute_number"]))
    else:
        if fallback_to_xem:
            return get_indexer_numbering_for_xem(indexer_id, indexer, sceneSeason, sceneEpisode, sceneAbsoluteNumber)
        return (sceneSeason, sceneEpisode, sceneAbsoluteNumber)


def get_scene_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    myDB = db.DBConnection()

    rows = myDB.select(
        'SELECT season, episode, absolute_number, scene_season, scene_episode, scene_absolute_number FROM scene_numbering WHERE indexer = ? and indexer_id = ? ORDER BY season, episode',
        [indexer, indexer_id])

    result = {}
    for row in rows:
        season = int(row['season'])
        episode = int(row['episode'])
        scene_season = int(row['scene_season'])
        scene_episode = int(row['scene_episode'])
        scene_absolute_number = int(row['scene_absolute_number'])

        try:
            result[(season, episode)]
        except:
            result[(season, episode)] = (scene_season, scene_episode, scene_absolute_number)

    return result


def set_scene_numbering(indexer_id, indexer, season, episode, absolute_number, sceneSeason=None, sceneEpisode=None,
                        sceneAbsoluteNumber=None):
    """
    Set scene numbering for a season/episode.
    To clear the scene numbering, leave both sceneSeason and sceneEpisode as None.
    
    """
    if indexer_id is None or season is None or episode is None:
        return

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    myDB = db.DBConnection()

    # sanity
    # if sceneSeason == None: sceneSeason = season
    #if sceneEpisode == None: sceneEpisode = episode

    # delete any existing record first
    myDB.action('DELETE FROM scene_numbering where indexer = ? and indexer_id = ? and season = ? and episode = ?',
                [indexer, indexer_id, season, episode])

    # now, if the new numbering is not the default, we save a new record
    if sceneSeason is not None and sceneEpisode is not None:
        myDB.action(
            "INSERT INTO scene_numbering (indexer, indexer_id, season, episode, absolute_number, scene_season, scene_episode, scene_absolute_number) VALUES (?,?,?,?,?,?,?,?)",
            [indexer, indexer_id, season, episode, absolute_number, sceneSeason, sceneEpisode, sceneAbsoluteNumber])


def find_xem_numbering(indexer_id, indexer, season, episode, absolute_number):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.
    
    @param indexer_id: int
    @param season: int
    @param episode: int
    @return: (int, int) a tuple of scene_season, scene_episode, or None if there is no special mapping.
    """
    if indexer_id is None or season is None or episode is None:
        return (season, episode, absolute_number)

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    if _xem_refresh_needed(indexer_id, indexer):
        _xem_refresh(indexer_id, indexer)

    cacheDB = db.DBConnection('cache.db')

    rows = cacheDB.select(
        "SELECT scene_season, scene_episode, scene_absolute_number FROM xem_numbering WHERE indexer = ? and indexer_id = ? and season = ? and episode = ?",
        [indexer, indexer_id, season, episode])

    if rows:
        return (int(rows[0]["scene_season"]), int(rows[0]["scene_episode"]), int(rows[0]["scene_absolute_number"]))
    elif cacheDB.select(
            "SELECT * FROM xem_numbering WHERE indexer = ? and indexer_id = ?",
            [indexer, indexer_id]):

        return (0, 0, 0)
    else:
        return None


def get_indexer_numbering_for_xem(indexer_id, indexer, sceneSeason, sceneEpisode, sceneAbsoluteNumber):
    """
    Reverse of find_xem_numbering: lookup a tvdb season and episode using scene numbering
    
    @param indexer_id: int
    @param sceneSeason: int
    @param sceneEpisode: int
    @return: (int, int) a tuple of (season, episode)   
    """
    if indexer_id is None or sceneSeason is None or sceneEpisode is None:
        return None

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    if _xem_refresh_needed(indexer_id, indexer):
        _xem_refresh(indexer_id, indexer)
    cacheDB = db.DBConnection('cache.db')
    rows = cacheDB.select(
        "SELECT season, episode, absolute_number FROM xem_numbering WHERE indexer = ? and indexer_id = ? and scene_season = ? and scene_episode = ?",
        [indexer, indexer_id, sceneSeason, sceneEpisode])
    if rows:
        return (int(rows[0]["season"]), int(rows[0]["episode"]), int(rows[0]["absolute_number"]))
    else:
        return (sceneSeason, sceneEpisode, sceneAbsoluteNumber)


def _xem_refresh_needed(indexer_id, indexer):
    """
    Is a refresh needed on a show?
    
    @param indexer_id: int
    @return: bool
    """
    if indexer_id is None:
        return False

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    cacheDB = db.DBConnection('cache.db')
    rows = cacheDB.select("SELECT last_refreshed FROM xem_refresh WHERE indexer = ? and indexer_id = ?",
                          [indexer, indexer_id])
    if rows:
        return time.time() > (int(rows[0]['last_refreshed']) + MAX_XEM_AGE_SECS)
    else:
        return True


def _xem_refresh(indexer_id, indexer):
    """
    Refresh data from xem for a tv show
    
    @param indexer_id: int
    """
    if indexer_id is None:
        return

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    try:
        logger.log(
            u'Looking up XEM scene mapping for show %s on %s' % (indexer_id, sickbeard.indexerApi(indexer).name,),
            logger.DEBUG)
        data = requests.get("http://thexem.de/map/all?id=%s&origin=%s&destination=scene" % (
            indexer_id, sickbeard.indexerApi(indexer).config['xem_origin'],), verify=False).json()

        if data is None or data == '':
            logger.log(u'No XEN data for show "%s on %s", trying TVTumbler' % (
                indexer_id, sickbeard.indexerApi(indexer).name,), logger.MESSAGE)
            data = requests.get("http://show-api.tvtumbler.com/api/thexem/all?id=%s&origin=%s&destination=scene" % (
                indexer_id, sickbeard.indexerApi(indexer).config['xem_origin'],), verify=False).json()
            if data is None or data == '':
                logger.log(u'TVTumbler also failed for show "%s on %s".  giving up.' % (indexer_id, indexer,),
                           logger.MESSAGE)
                return None

        result = data
        cacheDB = db.DBConnection('cache.db')

        ql = []
        if result:
            ql.append(["INSERT OR REPLACE INTO xem_refresh (indexer, indexer_id, last_refreshed) VALUES (?,?,?)",
                       [indexer, indexer_id, time.time()]])
            if 'success' in result['result']:
                ql.append(["DELETE FROM xem_numbering where indexer = ? and indexer_id = ?", [indexer, indexer_id]])
                for entry in result['data']:
                    if 'scene' in entry:
                        ql.append([
                            "INSERT OR IGNORE INTO xem_numbering (indexer, indexer_id, season, episode, absolute_number, scene_season, scene_episode, scene_absolute_number) VALUES (?,?,?,?,?,?,?,?)",
                            [indexer, indexer_id,
                             entry[sickbeard.indexerApi(indexer).config['xem_origin']]['season'],
                             entry[sickbeard.indexerApi(indexer).config['xem_origin']]['episode'],
                             entry[sickbeard.indexerApi(indexer).config['xem_origin']]['absolute'],
                             entry['scene']['season'],
                             entry['scene']['episode'],
                             entry['scene']['absolute']]])
                    if 'scene_2' in entry:  # for doubles
                        ql.append([
                            "INSERT OR IGNORE INTO xem_numbering (indexer, indexer_id, season, episode, absolute_number, scene_season, scene_episode, scene_absolute_number) VALUES (?,?,?,?,?,?,?,?)",
                            [indexer, indexer_id,
                             entry[sickbeard.indexerApi(indexer).config['xem_origin']]['season'],
                             entry[sickbeard.indexerApi(indexer).config['xem_origin']]['episode'],
                             entry[sickbeard.indexerApi(indexer).config['xem_origin']]['absolute'],
                             entry['scene_2']['season'],
                             entry['scene_2']['episode'],
                             entry['scene_2']['absolute']]])
            else:
                logger.log(u'Failed to get XEM scene data for show %s from %s because "%s"' % (
                    indexer_id, sickbeard.indexerApi(indexer).name, result['message']), logger.DEBUG)
        else:
            logger.log(u"Empty lookup result - no XEM data for show %s on %s" % (
                indexer_id, sickbeard.indexerApi(indexer).name,), logger.DEBUG)
    except Exception, e:
        logger.log(u"Exception while refreshing XEM data for show " + str(indexer_id) + " on " + sickbeard.indexerApi(
            indexer).name + ": " + ex(e), logger.WARNING)
        logger.log(traceback.format_exc(), logger.DEBUG)
        return None

    if ql:
        cacheDB.mass_action(ql)


def get_xem_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    if _xem_refresh_needed(indexer_id, indexer):
        _xem_refresh(indexer_id, indexer)

    cacheDB = db.DBConnection('cache.db')

    rows = cacheDB.select(
        'SELECT season, episode, absolute_number, scene_season, scene_episode, scene_absolute_number FROM xem_numbering WHERE indexer = ? and indexer_id = ? ORDER BY season, episode',
        [indexer, indexer_id])

    result = {}
    for row in rows:
        season = int(row['season'])
        episode = int(row['episode'])
        scene_season = int(row['scene_season'])
        scene_episode = int(row['scene_episode'])
        scene_absolute_number = int(row['scene_absolute_number'])

        result[(season, episode)] = (scene_season, scene_episode, scene_absolute_number)

    return result


def get_xem_numbering_for_season(indexer_id, indexer, season):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    if indexer_id is None or season is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    if _xem_refresh_needed(indexer_id, indexer):
        _xem_refresh(indexer_id, indexer)

    cacheDB = db.DBConnection('cache.db')

    rows = cacheDB.select(
        'SELECT season, scene_season FROM xem_numbering WHERE indexer = ? and indexer_id = ? AND season = ? ORDER BY season',
        [indexer, indexer_id, season])

    result = {}
    if rows:
        for row in rows:
            result.setdefault(int(row['season']), []).append(int(row['scene_season']))
    else:
        result.setdefault(int(season), []).append(int(season))

    return result

def fix_scene_numbering():
    ql = []

    myDB = db.DBConnection()

    sqlResults = myDB.select(
        "SELECT showid, indexerid, indexer, episode_id, season, episode FROM tv_episodes WHERE scene_season = -1 OR scene_episode = -1")

    for epResult in sqlResults:
        indexerid = int(epResult["showid"])
        indexer = int(epResult["indexer"])
        season = int(epResult["season"])
        episode = int(epResult["episode"])
        absolute_number = int(epResult["absolute_number"])

        logger.log(
            u"Repairing any scene numbering issues for showid: " + str(epResult["showid"]) + u" season: " + str(
                epResult["season"]) + u" episode: " + str(epResult["episode"]), logger.DEBUG)

        scene_season, scene_episode, scene_absolute_number = sickbeard.scene_numbering.get_scene_numbering(indexerid,
                                                                                                           indexer,
                                                                                                           season,
                                                                                                           episode,
                                                                                                           absolute_number)

        ql.append(
            ["UPDATE tv_episodes SET scene_season = ? WHERE indexerid = ?", [scene_season, epResult["indexerid"]]])
        ql.append(
            ["UPDATE tv_episodes SET scene_episode = ? WHERE indexerid = ?", [scene_episode, epResult["indexerid"]]])
        ql.append(
            ["UPDATE tv_episodes SET scene_absolute_number = ? WHERE indexerid = ?",
             [scene_absolute_number, epResult["indexerid"]]])

    if ql:
        myDB.mass_action(ql)

def get_ep_mapping(epObj, parse_result):
    # scores
    indexer_numbering = 0
    scene_numbering = 0
    absolute_numbering = 0

    _possible_seasons = sickbeard.scene_exceptions.get_scene_exception_by_name_multiple(parse_result.series_name)

    # indexer numbering
    if epObj.season == parse_result.season_number:
        indexer_numbering += 1
    elif epObj.episode in parse_result.episode_numbers:
        indexer_numbering += 1

    # scene numbering
    if epObj.scene_season == parse_result.season_number:
        scene_numbering += 1
    elif epObj.scene_episode in parse_result.episode_numbers:
        scene_numbering += 1

    # absolute numbering
    if epObj.show.is_anime and parse_result.is_anime:

        if epObj.absolute_number in parse_result.ab_episode_numbers:
            absolute_numbering +=1
        elif epObj.scene_absolute_number in parse_result.ab_episode_numbers:
            absolute_numbering += 1

    if indexer_numbering == 2:
        print "indexer numbering"
    elif scene_numbering == 2:
        print "scene numbering"
    elif absolute_numbering == 1:
        print "indexer numbering"
    else:
        print "could not determin numbering"