import datetime
import threading
import time

import sickchill
from sickchill import adba, logger, settings

from . import db, helpers

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

    if indexer_id not in exceptionsCache or season not in exceptionsCache[indexer_id]:
        cache_db_con = db.DBConnection('cache.db')
        exceptions = cache_db_con.select("SELECT show_name FROM scene_exceptions WHERE indexer_id = ? and season = ?",
                                         [indexer_id, season])
        if exceptions:
            exceptionsList = list({cur_exception["show_name"] for cur_exception in exceptions})
            if indexer_id not in exceptionsCache:
                exceptionsCache[indexer_id] = {}
            exceptionsCache[indexer_id][season] = exceptionsList

    results = []
    if indexer_id in exceptionsCache and season in exceptionsCache[indexer_id]:
        results += exceptionsCache[indexer_id][season]

    # Add generic exceptions regardless of the season if there is no exception for season
    if season != -1:
        get_scene_exceptions(indexer_id, season=-1)
        if indexer_id in exceptionsCache and -1 in exceptionsCache[indexer_id]:
            results += exceptionsCache[indexer_id][-1]

    return list({result for result in results})


def get_all_scene_exceptions(indexer_id):
    """
    Get all scene exceptions for a show ID

    :param indexer_id: ID to check
    :return: dict of exceptions
    """
    exceptionsDict = {}

    cache_db_con = db.DBConnection('cache.db')
    exceptions = cache_db_con.select("SELECT show_name,season,custom FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])

    if exceptions:
        for cur_exception in exceptions:
            if not cur_exception["season"] in exceptionsDict:
                exceptionsDict[cur_exception["season"]] = []
            exceptionsDict[cur_exception["season"]].append({
                "show_name": cur_exception["show_name"],
                "custom": bool(cur_exception["custom"])
            })

    return exceptionsDict


def get_scene_seasons(indexer_id):
    """
    return a list of season numbers that have scene exceptions
    """
    if indexer_id not in exceptionsSeasonCache:
        cache_db_con = db.DBConnection('cache.db')
        sql_results = cache_db_con.select("SELECT DISTINCT(season) as season FROM scene_exceptions WHERE indexer_id = ?",
                                          [indexer_id])
        if sql_results:
            exceptions_season_list = list({int(x["season"]) for x in sql_results})

            if indexer_id not in exceptionsSeasonCache:
                exceptionsSeasonCache[indexer_id] = []

            exceptionsSeasonCache[indexer_id] = exceptions_season_list

    return exceptionsSeasonCache.get(indexer_id, [])


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
                sickchill.oldbeard.helpers.sanitizeSceneName(cur_exception_name).lower().replace('.', ' ')):

            logger.debug("Scene exception lookup got indexer id {0}, using that".format
                         (cur_indexer_id))

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
    for indexer, instance in sickchill.indexer:
        if shouldRefresh(instance.name):
            do_refresh = True

    if do_refresh:
        loc = 'https://sickchill.github.io/scene_exceptions/scene_exceptions.json'
        logger.info("Checking for scene exception updates from {0}".format(loc))

        session = helpers.make_session()
        proxy = settings.PROXY_SETTING
        if proxy and settings.PROXY_INDEXERS:
            session.proxies = {
                "http": proxy,
                "https": proxy,
            }

        try:
            jdata = helpers.getURL(loc, session=session, returns='json')
        except Exception:
            jdata = None

        if not jdata:
            # When jdata is None, trouble connecting to github, or reading file failed
            logger.debug("Check scene exceptions update failed. Unable to update from {0}".format(loc))
        else:
            for indexer, instance in sickchill.indexer:
                try:
                    setLastRefresh(instance.name)
                    if instance.slug not in jdata:
                        continue

                    for indexer_id in jdata[instance.slug]:
                        alias_list = [
                            {scene_exception: int(scene_season)}
                            for scene_season in jdata[instance.slug][indexer_id]
                            for scene_exception in jdata[instance.slug][indexer_id][scene_season]
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
            for ex in cur_exception_dict.items():
                cur_exception, curSeason = ex
                if cur_exception not in existing_exceptions:
                    queries.append(
                        ["INSERT OR IGNORE INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?);",
                         [cur_indexer_id, cur_exception, curSeason]])
    if queries:
        cache_db_con.mass_action(queries)
        logger.debug("Updated scene exceptions")

    # cleanup
    exception_dict.clear()
    anidb_exception_dict.clear()
    xem_exception_dict.clear()


def update_scene_exceptions(indexer_id, scene_exceptions):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    """
    cache_db_con = db.DBConnection('cache.db')
    cache_db_con.action('DELETE FROM scene_exceptions WHERE indexer_id=? and custom=1', [indexer_id])

    logger.info("Updating scene exceptions")

    for season in scene_exceptions:
        for cur_exception in scene_exceptions[season]:
            cache_db_con.action("INSERT INTO scene_exceptions (indexer_id, show_name, season, custom) VALUES (?,?,?,?)",
                                [indexer_id, cur_exception["show_name"], season, cur_exception["custom"]])

    rebuild_exception_cache(indexer_id)


def _anidb_exceptions_fetcher():
    if shouldRefresh('anidb'):
        logger.info("Checking for scene exception updates for AniDB")
        for show in settings.showList:
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
        for indexer, instance in sickchill.indexer:
            logger.info("Checking for XEM scene exception updates for {0}".format(instance.name))

            url = "http://thexem.de/map/allNames?origin={0}&seasonNumbers=1".format(instance.slug)

            parsed_json = helpers.getURL(url, session=xem_session, timeout=90, returns='json')
            if not parsed_json:
                logger.debug("Check scene exceptions update failed for {0}, Unable to get URL: {1}".format
                             ('theTVDB', url))
                continue

            if parsed_json['result'] == 'failure':
                continue

            if parsed_json['data']:
                for indexerid, names in parsed_json['data'].items():
                    try:
                        xem_exception_dict[int(indexerid)] = names
                    except Exception as error:
                        logger.warning("XEM: Rejected entry: indexerid:{0}; names:{1}".format(indexerid, names))
                        logger.debug("XEM: Rejected entry error message:{0}".format(error))

        setLastRefresh('xem')

    return xem_exception_dict


def getSceneSeasons(indexer_id):
    """get a list of season numbers that have scene exceptions"""
    cache_db_con = db.DBConnection('cache.db')
    seasons = cache_db_con.select("SELECT DISTINCT season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])
    return [cur_exception["season"] for cur_exception in seasons]


def rebuild_exception_cache(indexer_id):
    if indexer_id not in exceptionsCache:
        exceptionsCache[indexer_id] = {}

    cache_db_con = db.DBConnection('cache.db')
    results = cache_db_con.action('SELECT show_name, season FROM scene_exceptions WHERE indexer_id=?', [indexer_id])

    for result in results:
        if result["season"] not in exceptionsCache[indexer_id]:
            exceptionsCache[indexer_id][result["season"]] = []

        exceptionsCache[indexer_id][result["season"]].append(result["show_name"])
