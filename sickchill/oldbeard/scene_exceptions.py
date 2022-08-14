import datetime
import time
from pathlib import Path

import sickchill
from sickchill import adba, logger, settings
from sickchill.show.Show import Show

from . import db, helpers

exceptions_cache = {}


def should_refresh(exception_list):
    """
    Check if we should refresh cache for items in exception_list

    :param exception_list: exception list to check if needs a refresh
    :return: True if refresh is needed
    """
    seconds_per_day = 24 * 60 * 60

    cache_db_con = db.DBConnection("cache.db")
    rows = cache_db_con.select("SELECT last_refreshed FROM scene_exceptions_refresh WHERE list = ?", [exception_list])
    if rows:
        last_refresh = int(rows[0]["last_refreshed"])
        return int(time.mktime(datetime.datetime.today().timetuple())) > last_refresh + seconds_per_day
    else:
        return True


def set_last_refresh(exception_list):
    """
    Update last cache update time for shows in list

    :param exception_list: exception list to set refresh time
    """
    cache_db_con = db.DBConnection("cache.db")
    cache_db_con.upsert("scene_exceptions_refresh", {"last_refreshed": int(time.mktime(datetime.datetime.today().timetuple()))}, {"list": exception_list})


def get_scene_exceptions(indexer_id, season=-1):
    """
    Given a indexer_id, return a list of all the scene exceptions.
    """

    if indexer_id not in exceptions_cache or season not in exceptions_cache[indexer_id]:
        cache_db_con = db.DBConnection("cache.db")
        exceptions = cache_db_con.select("SELECT show_name FROM scene_exceptions WHERE indexer_id = ? and season = ?", [indexer_id, season])
        if exceptions:
            exeptions_list = list({cur_exception["show_name"] for cur_exception in exceptions})
            if indexer_id not in exceptions_cache:
                exceptions_cache[indexer_id] = {}
            exceptions_cache[indexer_id][season] = exeptions_list

    results = []
    if indexer_id in exceptions_cache and season in exceptions_cache[indexer_id]:
        results += exceptions_cache[indexer_id][season]

    # Add generic exceptions regardless of the season if there is no exception for season
    if season != -1:
        get_scene_exceptions(indexer_id)
        if indexer_id in exceptions_cache and -1 in exceptions_cache[indexer_id]:
            results += exceptions_cache[indexer_id][-1]
    else:
        show = Show.find(settings.showList, indexer_id)
        if show:
            if show.show_name:
                results.append(helpers.full_sanitizeSceneName(show.show_name))
            if show.custom_name:
                results.append(helpers.full_sanitizeSceneName(show.custom_name))

    response = list({result for result in results})
    logger.debug(f"get_scene_exceptions: {response}")
    logger.debug(f"exceptions_cache: {exceptions_cache.get(indexer_id)}")
    return response


def get_all_scene_exceptions(indexer_id):
    """
    Get all scene exceptions for a show ID

    :param indexer_id: ID to check
    :return: dict of exceptions
    """
    all_exceptions_dict = {}

    cache_db_con = db.DBConnection("cache.db")
    exceptions = cache_db_con.select("SELECT show_name, season, custom FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])

    if indexer_id in exceptions_cache:
        del exceptions_cache[indexer_id]

    for cur_exception in exceptions:
        if cur_exception["season"] not in all_exceptions_dict:
            all_exceptions_dict[cur_exception["season"]] = []
        all_exceptions_dict[cur_exception["season"]].append({"show_name": cur_exception["show_name"], "custom": bool(cur_exception["custom"])})

        if indexer_id not in exceptions_cache:
            exceptions_cache[indexer_id] = {}

        if cur_exception["season"] not in exceptions_cache[indexer_id]:
            exceptions_cache[indexer_id][cur_exception["season"]] = []

        exceptions_cache[indexer_id][cur_exception["season"]].append(cur_exception["show_name"])

    show = Show.find(settings.showList, indexer_id)
    if show:
        sanitized_name = helpers.full_sanitizeSceneName(show.show_name)
        sanitized_custom_name = helpers.full_sanitizeSceneName(show.custom_name)

        if sanitized_name or sanitized_custom_name:

            if -1 not in all_exceptions_dict:
                all_exceptions_dict[-1] = []

            if indexer_id not in exceptions_cache:
                exceptions_cache[indexer_id] = {}

            if -1 not in exceptions_cache[indexer_id]:
                exceptions_cache[indexer_id][-1] = []

            if sanitized_name:
                all_exceptions_dict[-1].append({"show_name": sanitized_name, "custom": False})
                if sanitized_name not in exceptions_cache[indexer_id][-1]:
                    exceptions_cache[indexer_id][-1].append(sanitized_name)
            if sanitized_custom_name:
                all_exceptions_dict[-1].append({"show_name": sanitized_custom_name, "custom": False})
                if sanitized_custom_name not in exceptions_cache[indexer_id][-1]:
                    exceptions_cache[indexer_id][-1].append(sanitized_custom_name)

    logger.debug(f"get_all_scene_exceptions: {all_exceptions_dict}")
    logger.debug(f"exceptions_cache for {indexer_id}: {exceptions_cache.get(indexer_id)}")
    return all_exceptions_dict


def get_scene_exception_by_name(show_name):
    return get_scene_exception_by_name_multiple(show_name)[0]


def get_scene_exception_by_name_multiple(show_name):
    """
    Given a show name, return the indexerid of the exception, None if no exception
    is present.
    """

    # try the obvious case first
    cache_db_con = db.DBConnection("cache.db")
    exception_result = cache_db_con.select("SELECT indexer_id, season FROM scene_exceptions WHERE LOWER(show_name) = ? ORDER BY season", [show_name.lower()])
    if exception_result:
        return [(int(x["indexer_id"]), int(x["season"])) for x in exception_result]

    out = []
    all_exception_results = cache_db_con.select("SELECT show_name, indexer_id, season FROM scene_exceptions")

    for cur_exception in all_exception_results:

        cur_exception_name = cur_exception["show_name"]
        cur_indexer_id = int(cur_exception["indexer_id"])

        if show_name.lower() in (cur_exception_name.lower(), sickchill.oldbeard.helpers.sanitizeSceneName(cur_exception_name).lower().replace(".", " ")):

            logger.debug(f"Scene exception lookup got indexer id {cur_indexer_id}, using that")

            out.append((cur_indexer_id, int(cur_exception["season"])))

    if out:
        return out

    return [(None, None)]


def retrieve_exceptions():  # pylint:disable=too-many-locals, too-many-branches
    """
    Looks up the exceptions on github, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Also clears the scene name cache.
    """
    # SC exceptions
    exception_dict = _sickchill_exceptions_fetcher()

    # XEM scene exceptions
    xem_exception_dict = _xem_exceptions_fetcher()
    for xem_ex in xem_exception_dict:
        if xem_ex in exception_dict:
            exception_dict[xem_ex] += exception_dict[xem_ex]
        else:
            exception_dict[xem_ex] = xem_exception_dict[xem_ex]

    # AniDB scene exceptions
    anidb_exception_dict = _anidb_exceptions_fetcher()
    for anidb_ex in anidb_exception_dict:
        if anidb_ex in exception_dict:
            exception_dict[anidb_ex] += anidb_exception_dict[anidb_ex]
        else:
            exception_dict[anidb_ex] = anidb_exception_dict[anidb_ex]

    queries = []
    cache_db_con = db.DBConnection("cache.db")
    for cur_indexer_id, cur_exception_list in exception_dict.items():
        sql_ex = cache_db_con.select("SELECT show_name FROM scene_exceptions WHERE indexer_id = ?;", [cur_indexer_id])
        existing_exceptions = (x["show_name"] for x in sql_ex)

        for cur_exception_dict in cur_exception_list:
            for cur_exception, cur_season in cur_exception_dict.items():
                if cur_exception not in existing_exceptions:
                    queries.append(
                        ["INSERT OR IGNORE INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?);", [cur_indexer_id, cur_exception, cur_season]]
                    )
    if queries:
        cache_db_con.mass_action(queries)
        main_db_con = db.DBConnection("sickchill.db")
        sql_ex = main_db_con.select("SELECT indexer_id FROM tv_shows")
        for result in sql_ex:
            rebuild_exception_cache(result["indexer_id"])
        logger.debug("Updated scene exceptions")


def update_custom_scene_exceptions(indexer_id, scene_exceptions):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    """
    cache_db_con = db.DBConnection("cache.db")
    cache_db_con.action("DELETE FROM scene_exceptions WHERE indexer_id = ? and custom = 1", [indexer_id])

    logger.info("Updating scene exceptions")

    for season in scene_exceptions:
        for cur_exception in scene_exceptions[season]:
            cache_db_con.action(
                "INSERT INTO scene_exceptions (indexer_id, show_name, season, custom) VALUES (?,?,?,?)",
                [indexer_id, cur_exception["show_name"], season, cur_exception["custom"]],
            )

    rebuild_exception_cache(indexer_id)


def _sickchill_exceptions_fetcher():
    sickchill_exception_dict = {}

    do_refresh = False
    for indexer, instance in sickchill.indexer:
        if should_refresh(instance.name):
            do_refresh = True
            break

    if do_refresh:
        loc = "https://sickchill.github.io/scene_exceptions/scene_exceptions.json"
        logger.info(f"Checking for scene exception updates from {loc}")

        session = helpers.make_session()
        proxy = settings.PROXY_SETTING
        if proxy and settings.PROXY_INDEXERS:
            session.proxies = {
                "http": proxy,
                "https": proxy,
            }

        try:
            jdata = helpers.getURL(loc, session=session, returns="json")
        except Exception:
            jdata = None

        if not jdata:
            # When jdata is None, trouble connecting to github, or reading file failed
            logger.debug(f"Check scene exceptions update failed. Unable to update from {loc}")
        else:
            for indexer, instance in sickchill.indexer:
                try:
                    set_last_refresh(instance.name)
                    if instance.slug not in jdata:
                        continue

                    for indexer_id in jdata[instance.slug]:
                        alias_list = [
                            {scene_exception: int(scene_season)}
                            for scene_season in jdata[instance.slug][indexer_id]
                            for scene_exception in jdata[instance.slug][indexer_id][scene_season]
                        ]
                        sickchill_exception_dict[indexer_id] = alias_list
                except Exception:
                    continue
    return sickchill_exception_dict


def _anidb_exceptions_fetcher():
    anidb_exception_dict = {}

    if should_refresh("anidb"):
        logger.info("Checking for scene exception updates for AniDB")
        for show in settings.showList:
            if show.is_anime and show.indexer == 1:
                try:
                    anime = adba.Anime(None, name=show.name, tvdbid=show.indexerid, autoCorrectName=True, cache_dir=Path(settings.CACHE_DIR))
                except Exception:
                    continue
                else:
                    if anime.name and anime.name != show.name:
                        anidb_exception_dict[show.indexerid] = [{anime.name: -1}]

        set_last_refresh("anidb")
    return anidb_exception_dict


xem_session = helpers.make_session()


def _xem_exceptions_fetcher():
    xem_exception_dict = {}

    if should_refresh("xem"):
        for indexer, instance in sickchill.indexer:
            logger.info(f"Checking for XEM scene exception updates for {instance.name}")

            url = f"http://thexem.info/map/allNames?origin={instance.slug}&seasonNumbers=1"

            parsed_json = helpers.getURL(url, session=xem_session, timeout=90, returns="json")
            if not parsed_json:
                logger.debug(f'Check scene exceptions update failed for "theTVDB", Unable to get URL: {url}')
                continue

            if parsed_json["result"] == "failure":
                continue

            if parsed_json["data"]:
                for indexerid, names in parsed_json["data"].items():
                    try:
                        xem_exception_dict[int(indexerid)] = names
                    except Exception as error:
                        logger.warning(f"XEM: Rejected entry: indexerid:{indexerid}; names:{names}")
                        logger.debug(f"XEM: Rejected entry error message:{error}")

        set_last_refresh("xem")

    return xem_exception_dict


def rebuild_exception_cache(indexer_id):
    cache_db_con = db.DBConnection("cache.db")
    results = cache_db_con.action("SELECT show_name, season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])

    exceptions_cache_list = {}
    for result in results:
        if result["season"] not in exceptions_cache_list:
            exceptions_cache_list[result["season"]] = []

        exceptions_cache_list[result["season"]].append(result["show_name"])

    exceptions_cache[indexer_id] = exceptions_cache_list
