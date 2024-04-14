import datetime
import time
from pathlib import Path
from typing import Generator, Union

import sickchill
from sickchill import adba, logger, settings
from sickchill.oldbeard import db, helpers
from sickchill.show.Show import Show

exceptions_cache = {}


def should_refresh(exception_provider: str) -> bool:
    """
    Check if we should refresh cache for items in exception_provider

    :param exception_provider: exception list to check if scene exceptions need a refresh
    :return: True if refresh is needed
    """
    seconds_per_day = 24 * 60 * 60

    cache_db_con = db.DBConnection("cache.db")
    rows = cache_db_con.select("SELECT last_refreshed FROM scene_exceptions_refresh WHERE list = ?", [exception_provider])
    if rows:
        last_refresh = int(rows[0]["last_refreshed"])
        return int(time.mktime(datetime.datetime.today().timetuple())) > last_refresh + seconds_per_day
    else:
        return True


def set_last_refresh(exception_provider: str) -> None:
    """
    Update last cache update time for shows in list

    :param exception_provider: exception list to set refresh time
    """
    cache_db_con = db.DBConnection("cache.db")
    cache_db_con.upsert("scene_exceptions_refresh", {"last_refreshed": int(time.mktime(datetime.datetime.today().timetuple()))}, {"list": exception_provider})


def get_scene_exceptions(indexer_id: int, season: int = -1) -> list:
    """
    Given an indexer_id, return a list of all the scene exceptions.
    """

    if indexer_id not in exceptions_cache or season not in exceptions_cache[indexer_id]:
        cache_db_con = db.DBConnection("cache.db")
        exceptions = cache_db_con.select(
            "SELECT show_name FROM scene_exceptions WHERE indexer_id = ? and season = ? ORDER BY show_name COLLATE NOCASE", [indexer_id, season]
        )
        if exceptions:
            exceptions_list = list({cur_exception["show_name"] for cur_exception in exceptions})
            if indexer_id not in exceptions_cache:
                exceptions_cache[indexer_id] = {}
            exceptions_cache[indexer_id][season] = exceptions_list

    results = []
    if indexer_id in exceptions_cache and season in exceptions_cache[indexer_id]:
        results += exceptions_cache[indexer_id][season]

    # Add generic exceptions regardless of the season if there is no exception for season
    if season != -1:
        get_scene_exceptions(indexer_id)
        if indexer_id in exceptions_cache and -1 in exceptions_cache[indexer_id]:
            results += exceptions_cache[indexer_id][-1]
    else:
        show = Show.find(settings.show_list, indexer_id)
        if show:
            if show.show_name:
                results.append(helpers.full_sanitizeSceneName(show.show_name))
            if show.custom_name:
                results.append(helpers.full_sanitizeSceneName(show.custom_name))

    response = list({result for result in results})
    logger.debug(f"get_scene_exceptions: {response}")
    logger.debug(f"exceptions_cache: {exceptions_cache.get(indexer_id)}")
    return response


def get_all_scene_exceptions(indexer_id: int) -> dict:
    """
    Get all scene exceptions for a show ID

    :param indexer_id: ID to check
    :return: dict of exceptions
    """
    all_exceptions_dict = {}

    cache_db_con = db.DBConnection("cache.db")
    exceptions = cache_db_con.select(
        "SELECT show_name, season, custom FROM scene_exceptions WHERE indexer_id = ? ORDER BY show_name COLLATE NOCASE", [indexer_id]
    )

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

    show = Show.find(settings.show_list, indexer_id)
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

    # sort season in exceptions dict by "custom" then "show_name" so alphabetical and custom names are bottom of list
    for ind, ele in enumerate(all_exceptions_dict):
        all_exceptions_dict[ele] = sorted(all_exceptions_dict[ele], key=lambda x: (x["custom"], x["show_name"].lower()))

    logger.debug(f"get_all_scene_exceptions: {all_exceptions_dict}")
    logger.debug(f"exceptions_cache for {indexer_id}: {exceptions_cache.get(indexer_id)}")
    return all_exceptions_dict


def get_scene_exception_by_name(show_name: str) -> tuple:
    return get_scene_exception_by_name_multiple(show_name)[0]


def get_scene_exception_by_name_multiple(show_name) -> list:
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


def update_custom_scene_exceptions(indexer_id, scene_exceptions: dict) -> None:
    """
    Given an indexer_id, and a list of all show scene exceptions, update the db.
    """
    cache_db_con = db.DBConnection("cache.db")
    cache_db_con.action("DELETE FROM scene_exceptions WHERE indexer_id = ? and custom = 1", [indexer_id])

    logger.info("Updating scene exceptions")

    sql_actions = []
    for season, exceptions in scene_exceptions.items():
        for cur_exception in exceptions:
            exists = cache_db_con.select_one(
                "SELECT exception_id FROM scene_exceptions WHERE indexer_id = ? and show_name = ? and season = ?",
                [indexer_id, cur_exception["show_name"], season],
            )
            if not exists:
                sql_actions.append(
                    [
                        "INSERT INTO scene_exceptions (indexer_id, show_name, season, custom) VALUES (?,?,?,?)",
                        [indexer_id, cur_exception["show_name"], season, cur_exception["custom"]],
                    ]
                )
    cache_db_con.mass_action(sql_actions)
    rebuild_exception_cache(indexer_id)


def retrieve_exceptions() -> None:
    """
    Looks up the exceptions on GitHub, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Also clears the scene name cache.
    """
    queries = []
    updated_shows = set()
    cache_db_con = db.DBConnection("cache.db")

    generators = (_sickchill_exceptions_generator(), _xem_exceptions_generator(), _anidb_exceptions_generator())
    for generator in generators:
        for indexerid, name, season in generator:
            queries.append(["DELETE FROM scene_exceptions WHERE indexer_id = ? and show_name = ? and  season = ? and custom = 1;", [indexerid, name, season]])
            queries.append(["INSERT OR IGNORE INTO scene_exceptions (indexer_id, show_name, season, custom) VALUES (?,?,?, 0);", [indexerid, name, season]])
            updated_shows.add(indexerid)

    if queries:
        cache_db_con.mass_action(queries)

        for show in updated_shows:
            rebuild_exception_cache(show)

        logger.debug("Updated scene exceptions")


github_session = helpers.make_indexer_session()


def _sickchill_exceptions_generator() -> Union[Generator[int, str, int], None]:
    if not should_refresh("sickchill"):
        return

    logger.info("Checking for scene exception updates from sickchill.github.io")
    url = "https://sickchill.github.io/scene_exceptions/scene_exceptions.json"

    # noinspection PyBroadException
    try:
        jdata: dict = helpers.getURL(url, session=github_session, returns="json")
    except Exception:
        jdata = {}

    if not jdata:
        # When jdata is None, trouble connecting to GitHub, or reading file failed
        logger.debug(f"Check scene exceptions update failed (no data). Unable to update from {url}")
        return

    for indexer, shows in jdata.items():
        # noinspection PyBroadException
        try:
            for indexer_id, exceptions in shows.items():
                for season, names in exceptions.items():
                    for name in names:
                        yield int(indexer_id), name, int(season)
        except Exception:
            logger.debug(f"Check scene exceptions update failed, Unable to update from {url}")
            continue

    set_last_refresh("sickchill")


def _anidb_exceptions_generator() -> Union[Generator[int, str, int], None]:
    if not should_refresh("anidb"):
        return

    logger.info("Checking for scene exception updates for AniDB")
    for show in settings.show_list:
        if settings.stopping or settings.restarting:
            return

        if show.is_anime and show.indexer == 1:
            # noinspection PyBroadException
            try:
                anime = adba.Anime(None, name=show.name, tvdbid=show.indexerid, autoCorrectName=True, cache_dir=Path(settings.CACHE_DIR))
            except Exception:
                logger.debug(f"Could not update anime exceptions from anidb for {show.name}")
                continue
            else:
                if anime.name and anime.name != show.name:
                    yield int(show.indexerid), anime.name, -1

    set_last_refresh("anidb")


xem_session = helpers.make_indexer_session()


def _xem_exceptions_generator() -> Union[Generator[int, str, int], None]:
    if not should_refresh("xem"):
        return

    for indexer, instance in sickchill.indexer:
        logger.info(f"Checking for XEM scene exception updates for {instance.name}")

        url = f"https://thexem.info/map/allNames?origin={instance.slug}&seasonNumbers=1"

        parsed_json = helpers.getURL(url, session=xem_session, timeout=90, returns="json")
        if not parsed_json:
            logger.debug(f'Check scene exceptions update failed for "theTVDB", Unable to get URL: {url}')
            continue

        if parsed_json.get("result") == "failure":
            continue

        if not parsed_json.get("data"):
            continue

        for indexerid, exception_list in parsed_json["data"].items():
            for exception in exception_list:
                for name, season in exception.items():
                    try:
                        yield int(indexerid), name, int(season)
                    except Exception as error:
                        logger.warning(f"XEM: Rejected entry: indexerid:{indexerid}; names:{name}")
                        logger.debug(f"XEM: Rejected entry error message:{error}")

    set_last_refresh("xem")


def rebuild_exception_cache(indexer_id: int) -> None:
    cache_db_con = db.DBConnection("cache.db")
    results = cache_db_con.action("SELECT show_name, season FROM scene_exceptions WHERE indexer_id = ?", [indexer_id])

    exceptions_cache_list = dict()
    for result in results:
        if result["season"] not in exceptions_cache_list:
            exceptions_cache_list[result["season"]] = []

        exceptions_cache_list[result["season"]].append(result["show_name"])

    exceptions_cache[indexer_id] = exceptions_cache_list
