#
# Created on Sep 20, 2012
# @author: Dermot Buckley <dermot@buckley.ie>
# @copyright: Dermot Buckley
#
import datetime
import time
import traceback

import sickchill
from sickchill import logger, settings
from sickchill.show.Show import Show

from . import db
from .scene_exceptions import xem_session


def get_scene_numbering(indexer_id, indexer, season, episode, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode), with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise
    returns the indexer numbering.
    (so the return values will always be set)

    :param indexer_id: int
    :param season: int
    :param episode: int
    :param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    :return: (int, int) a tuple with (season, episode)
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    showObj = Show.find(settings.showList, int(indexer_id))
    if showObj and not showObj.is_scene:
        return season, episode

    result = find_scene_numbering(int(indexer_id), int(indexer), season, episode)
    if result:
        return result
    else:
        if fallback_to_xem:
            xem_result = find_xem_numbering(int(indexer_id), int(indexer), season, episode)
            if xem_result:
                return xem_result
        return season, episode


def find_scene_numbering(indexer_id, indexer, season, episode):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        "SELECT scene_season, scene_episode FROM scene_numbering WHERE indexer = ? and indexer_id = ? and season = ? and episode = ? and (scene_season or scene_episode) != 0",
        [indexer, indexer_id, season, episode])

    if rows:
        return int(rows[0]["scene_season"]), int(rows[0]["scene_episode"])


def get_scene_absolute_numbering(indexer_id, indexer, absolute_number, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode), with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise
    returns the indexer numbering.
    (so the return values will always be set)

    :param indexer_id: int
    :param indexer: int
    :param absolute_number: int
    :param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    :return: (int, int) a tuple with (season, episode)
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    showObj = Show.find(settings.showList, indexer_id)
    if showObj and not showObj.is_scene:
        return absolute_number

    result = find_scene_absolute_numbering(indexer_id, indexer, absolute_number)
    if result:
        return result
    else:
        if fallback_to_xem:
            xem_result = find_xem_absolute_numbering(indexer_id, indexer, absolute_number)
            if xem_result:
                return xem_result
        return absolute_number


def find_scene_absolute_numbering(indexer_id, indexer, absolute_number):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        "SELECT scene_absolute_number FROM scene_numbering WHERE indexer = ? and indexer_id = ? and absolute_number = ? and scene_absolute_number != 0",
        [indexer, indexer_id, absolute_number])

    if rows:
        return int(rows[0]["scene_absolute_number"])


def get_indexer_numbering(indexer_id, indexer, sceneSeason, sceneEpisode, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode) with the indexer numbering for (sceneSeason, sceneEpisode)
    (this works like the reverse of get_scene_numbering)
    """
    if indexer_id is None or sceneSeason is None or sceneEpisode is None:
        return sceneSeason, sceneEpisode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        "SELECT season, episode FROM scene_numbering WHERE indexer = ? and indexer_id = ? and scene_season = ? and scene_episode = ?",
        [indexer, indexer_id, sceneSeason, sceneEpisode])

    if rows:
        return int(rows[0]["season"]), int(rows[0]["episode"])
    else:
        if fallback_to_xem:
            return get_indexer_numbering_for_xem(indexer_id, indexer, sceneSeason, sceneEpisode)
        return sceneSeason, sceneEpisode


def get_indexer_absolute_numbering(indexer_id, indexer, sceneAbsoluteNumber, fallback_to_xem=True, scene_season=None):
    """
    Returns a tuple, (season, episode, absolute_number) with the show absolute numbering for (sceneAbsoluteNumber)
    (this works like the reverse of get_absolute_numbering)
    """
    if indexer_id is None or sceneAbsoluteNumber is None:
        return sceneAbsoluteNumber

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    main_db_con = db.DBConnection()
    if scene_season is None:
        rows = main_db_con.select(
            "SELECT absolute_number FROM scene_numbering WHERE indexer = ? and indexer_id = ? and scene_absolute_number = ?",
            [indexer, indexer_id, sceneAbsoluteNumber])
    else:
        rows = main_db_con.select(
            "SELECT absolute_number FROM scene_numbering WHERE indexer = ? and indexer_id = ? and scene_absolute_number = ? and scene_season = ?",
            [indexer, indexer_id, sceneAbsoluteNumber, scene_season])

    if rows:
        return int(rows[0]["absolute_number"])
    else:
        if fallback_to_xem:
            return get_indexer_absolute_numbering_for_xem(indexer_id, indexer, sceneAbsoluteNumber, scene_season)
        return sceneAbsoluteNumber


def set_scene_numbering(indexer_id, indexer, season=None, episode=None,
                        absolute_number=None, sceneSeason=None,
                        sceneEpisode=None, sceneAbsolute=None):
    """
    Set scene numbering for a season/episode.
    To clear the scene numbering, leave both sceneSeason and sceneEpisode as None.
    """
    if indexer_id is None:
        return

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    main_db_con = db.DBConnection()
    if season and episode:
        main_db_con.action(
            "INSERT OR IGNORE INTO scene_numbering (indexer, indexer_id, season, episode) VALUES (?,?,?,?)",
            [indexer, indexer_id, season, episode])

        main_db_con.action(
            "UPDATE scene_numbering SET scene_season = ?, scene_episode = ? WHERE indexer = ? and indexer_id = ? and season = ? and episode = ?",
            [sceneSeason, sceneEpisode, indexer, indexer_id, season, episode])
    elif absolute_number:
        main_db_con.action(
            "INSERT OR IGNORE INTO scene_numbering (indexer, indexer_id, absolute_number) VALUES (?,?,?)",
            [indexer, indexer_id, absolute_number])

        main_db_con.action(
            "UPDATE scene_numbering SET scene_absolute_number = ? WHERE indexer = ? and indexer_id = ? and absolute_number = ?",
            [sceneAbsolute, indexer, indexer_id, absolute_number])

    # Reload data from DB so that cache and db are in sync
    show = Show.find(settings.showList, indexer_id)
    show.flushEpisodes()


def find_xem_numbering(indexer_id, indexer, season, episode):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    :param indexer_id: int
    :param indexer: int
    :param season: int
    :param episode: int
    :return: (int, int) a tuple of scene_season, scene_episode, or None if there is no special mapping.
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        "SELECT scene_season, scene_episode FROM tv_episodes WHERE indexer = ? and showid = ? and season = ? and episode = ? and (scene_season or scene_episode) != 0",
        [indexer, indexer_id, season, episode])

    if rows:
        return int(rows[0]["scene_season"]), int(rows[0]["scene_episode"])


def find_xem_absolute_numbering(indexer_id, indexer, absolute_number):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    :param indexer_id: int
    :param absolute_number: int
    :return: int
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        "SELECT scene_absolute_number FROM tv_episodes WHERE indexer = ? and showid = ? and absolute_number = ? and scene_absolute_number != 0",
        [indexer, indexer_id, absolute_number])

    if rows:
        return int(rows[0]["scene_absolute_number"])


def get_indexer_numbering_for_xem(indexer_id, indexer, sceneSeason, sceneEpisode):
    """
    Reverse of find_xem_numbering: lookup a show season and episode using scene numbering

    :param indexer_id: int
    :param indexer: int
    :param sceneSeason: int
    :param sceneEpisode: int
    :return: (int, int) a tuple of (season, episode)
    """
    if indexer_id is None or sceneSeason is None or sceneEpisode is None:
        return sceneSeason, sceneEpisode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        "SELECT season, episode FROM tv_episodes WHERE indexer = ? and showid = ? and scene_season = ? and scene_episode = ?",
        [indexer, indexer_id, sceneSeason, sceneEpisode])

    if rows:
        return int(rows[0]["season"]), int(rows[0]["episode"])

    return sceneSeason, sceneEpisode


def get_indexer_absolute_numbering_for_xem(indexer_id, indexer, sceneAbsoluteNumber, scene_season=None):
    """
    Reverse of find_xem_numbering: lookup a show season and episode using scene numbering

    :param indexer_id: int
    :param indexer: int
    :param sceneAbsoluteNumber: int
    :return: int
    """
    if indexer_id is None or sceneAbsoluteNumber is None:
        return sceneAbsoluteNumber

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    main_db_con = db.DBConnection()
    if scene_season is None:
        rows = main_db_con.select(
            "SELECT absolute_number FROM tv_episodes WHERE indexer = ? and showid = ? and scene_absolute_number = ?",
            [indexer, indexer_id, sceneAbsoluteNumber])
    else:
        rows = main_db_con.select(
            "SELECT absolute_number FROM tv_episodes WHERE indexer = ? and showid = ? and scene_absolute_number = ? and scene_season = ?",
            [indexer, indexer_id, sceneAbsoluteNumber, scene_season])

    if rows:
        return int(rows[0]["absolute_number"])

    return sceneAbsoluteNumber


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

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        'SELECT season, episode, scene_season, scene_episode FROM scene_numbering WHERE indexer = ? and indexer_id = ? and (scene_season or scene_episode) != 0 ORDER BY season, episode',
        [indexer, indexer_id])

    result = {}
    for row in rows:
        season = int(row['season'])
        episode = int(row['episode'])
        scene_season = int(row['scene_season'])
        scene_episode = int(row['scene_episode'])

        result[(season, episode)] = (scene_season, scene_episode)

    return result


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

    xem_refresh(indexer_id, indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        'SELECT season, episode, scene_season, scene_episode FROM tv_episodes WHERE indexer = ? and showid = ? and (scene_season or scene_episode) != 0 ORDER BY season, episode',
        [indexer, indexer_id])

    result = {}
    for row in rows:
        season = int(row['season'])
        episode = int(row['episode'])
        scene_season = int(row['scene_season'])
        scene_episode = int(row['scene_episode'])

        result[(season, episode)] = (scene_season, scene_episode)

    return result


def get_scene_absolute_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        'SELECT absolute_number, scene_absolute_number FROM scene_numbering WHERE indexer = ? and indexer_id = ? and scene_absolute_number != 0 ORDER BY absolute_number',
        [indexer, indexer_id])

    result = {}
    for row in rows:
        absolute_number = int(row['absolute_number'])
        scene_absolute_number = int(row['scene_absolute_number'])

        result[absolute_number] = scene_absolute_number

    return result


def get_xem_absolute_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    result = {}
    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        'SELECT absolute_number, scene_absolute_number FROM tv_episodes WHERE indexer = ? and showid = ? and scene_absolute_number != 0 ORDER BY absolute_number',
        [indexer, indexer_id])

    for row in rows:
        __absolute_number = row['absolute_number']
        __scene_absolute_number = row['scene_absolute_number']
        if not (__absolute_number and __scene_absolute_number):
            continue

        result[int(__absolute_number)] = int(__scene_absolute_number)

    return result


def xem_refresh(indexer_id, indexer, force=False):
    """
    Refresh data from xem for a tv show

    :param indexer_id: int
    """
    if not indexer_id or indexer_id < 1:
        return

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    MAX_REFRESH_AGE_SECS = 86400  # 1 day

    main_db_con = db.DBConnection()
    rows = main_db_con.select("SELECT last_refreshed FROM xem_refresh WHERE indexer = ? and indexer_id = ?",
                              [indexer, indexer_id])
    if rows:
        lastRefresh = int(rows[0]['last_refreshed'])
        refresh = int(time.mktime(datetime.datetime.today().timetuple())) > lastRefresh + MAX_REFRESH_AGE_SECS
    else:
        refresh = True

    if refresh or force:
        logger.debug(
            'Looking up XEM scene mapping for show {0} on {1}'.format(indexer_id, sickchill.indexer.name(indexer)))

        # mark refreshed
        main_db_con.upsert(
            "xem_refresh",
            {'indexer': indexer,
             'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple()))},
            {'indexer_id': indexer_id}
        )

        try:
            # XEM MAP URL
            url = "http://thexem.de/map/havemap?origin={0}".format(sickchill.indexer.slug(indexer))
            parsed_json = sickchill.oldbeard.helpers.getURL(url, session=xem_session, returns='json')
            if not parsed_json or 'result' not in parsed_json or 'success' not in parsed_json['result'] or 'data' not in parsed_json or str(indexer_id) not in parsed_json['data']:
                return

            # XEM API URL
            url = "http://thexem.de/map/all?id={0}&origin={1}&destination=scene".format(indexer_id, sickchill.indexer.slug(indexer))

            parsed_json = sickchill.oldbeard.helpers.getURL(url, session=xem_session, returns='json')
            if not parsed_json or 'result' not in parsed_json or 'success' not in parsed_json['result']:
                logger.info('No XEM data for show "{0} on {1}"'.format(indexer_id, sickchill.indexer.name(indexer)))
                return

            cl = []
            for entry in parsed_json['data']:
                if 'scene' in entry:
                    cl.append([
                        "UPDATE tv_episodes SET scene_season = ?, scene_episode = ?, scene_absolute_number = ? WHERE showid = ? AND season = ? AND episode = ?",
                        [entry['scene']['season'], entry['scene']['episode'],
                         entry['scene']['absolute'], indexer_id,
                         entry[sickchill.indexer.slug(indexer)]['season'],
                         entry[sickchill.indexer.slug(indexer)]['episode']]
                    ])
                    cl.append([
                        "UPDATE tv_episodes SET absolute_number = ? WHERE showid = ? AND season = ? AND episode = ? AND absolute_number = 0",
                        [entry[sickchill.indexer.slug(indexer)]['absolute'], indexer_id,
                         entry[sickchill.indexer.slug(indexer)]['season'],
                         entry[sickchill.indexer.slug(indexer)]['episode']]
                    ])
                if 'scene_2' in entry:  # for doubles
                    cl.append([
                        "UPDATE tv_episodes SET scene_season = ?, scene_episode = ?, scene_absolute_number = ? WHERE showid = ? AND season = ? AND episode = ?",
                        [entry['scene_2']['season'], entry['scene_2']['episode'],
                         entry['scene_2']['absolute'], indexer_id,
                         entry[sickchill.indexer.slug(indexer)]['season'],
                         entry[sickchill.indexer.slug(indexer)]['episode']]
                    ])

            if cl:
                main_db_con = db.DBConnection()
                main_db_con.mass_action(cl)

        except Exception as e:
            logger.warning("Exception while refreshing XEM data for show {} on {}: {}".format(
                indexer_id, sickchill.indexer.name(indexer), str(e)))
            logger.debug(traceback.format_exc())


def fix_xem_numbering(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    main_db_con = db.DBConnection()
    rows = main_db_con.select(
        'SELECT season, episode, absolute_number, scene_season, scene_episode, scene_absolute_number FROM tv_episodes WHERE indexer = ? and showid = ?',
        [indexer, indexer_id])

    last_absolute_number = None
    last_scene_season = None
    last_scene_episode = None
    last_scene_absolute_number = None

    update_absolute_number = False
    update_scene_season = False
    update_scene_episode = False
    update_scene_absolute_number = False

    logger.debug('Fixing any XEM scene mapping issues for show {0} on {1}'.format(indexer_id, sickchill.indexer.name(indexer)))

    cl = []
    for row in rows:
        season = int(row['season'])
        episode = int(row['episode'])

        if not int(row['scene_season']) and last_scene_season:
            scene_season = last_scene_season + 1
            update_scene_season = True
        else:
            scene_season = int(row['scene_season'])
            if last_scene_season and scene_season < last_scene_season:
                scene_season = last_scene_season + 1
                update_scene_season = True

        if not int(row['scene_episode']) and last_scene_episode:
            scene_episode = last_scene_episode + 1
            update_scene_episode = True
        else:
            scene_episode = int(row['scene_episode'])
            if last_scene_episode and scene_episode < last_scene_episode:
                scene_episode = last_scene_episode + 1
                update_scene_episode = True

        # check for unset values and correct them
        if not int(row['absolute_number']) and last_absolute_number:
            absolute_number = last_absolute_number + 1
            update_absolute_number = True
        else:
            absolute_number = int(row['absolute_number'])
            if last_absolute_number and absolute_number < last_absolute_number:
                absolute_number = last_absolute_number + 1
                update_absolute_number = True

        if not int(row['scene_absolute_number']) and last_scene_absolute_number:
            scene_absolute_number = last_scene_absolute_number + 1
            update_scene_absolute_number = True
        else:
            scene_absolute_number = int(row['scene_absolute_number'])
            if last_scene_absolute_number and scene_absolute_number < last_scene_absolute_number:
                scene_absolute_number = last_scene_absolute_number + 1
                update_scene_absolute_number = True

        # store values for lookup on next iteration
        last_absolute_number = absolute_number
        last_scene_season = scene_season
        last_scene_episode = scene_episode
        last_scene_absolute_number = scene_absolute_number

        if update_absolute_number:
            cl.append([
                "UPDATE tv_episodes SET absolute_number = ? WHERE showid = ? AND season = ? AND episode = ?",
                [absolute_number, indexer_id, season, episode]
            ])
            update_absolute_number = False

        if update_scene_season:
            cl.append([
                "UPDATE tv_episodes SET scene_season = ? WHERE showid = ? AND season = ? AND episode = ?",
                [scene_season, indexer_id, season, episode]
            ])
            update_scene_season = False

        if update_scene_episode:
            cl.append([
                "UPDATE tv_episodes SET scene_episode = ? WHERE showid = ? AND season = ? AND episode = ?",
                [scene_episode, indexer_id, season, episode]
            ])
            update_scene_episode = False

        if update_scene_absolute_number:
            cl.append([
                "UPDATE tv_episodes SET scene_absolute_number = ? WHERE showid = ? AND season = ? AND episode = ?",
                [scene_absolute_number, indexer_id, season, episode]
            ])
            update_scene_absolute_number = False

    if cl:
        main_db_con = db.DBConnection()
        main_db_con.mass_action(cl)
