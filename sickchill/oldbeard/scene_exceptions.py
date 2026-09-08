import time
from pathlib import Path
from typing import Generator

import sickchill
from sickchill import logger, settings
from sickchill.oldbeard import db, helpers
from sickchill.oldbeard.network_timezones import sc_now
from sickchill.show.Show import Show

# Cache for exceptions (used by rebuild_exception_cache, etc.)
exceptions_cache = {}


def _get_github_session():
    """Return a fresh github session (lazy + respects current settings)."""
    return helpers.make_indexer_session()


def get_xem_session():
    """Return a fresh xem session (lazy + respects current settings)."""
    return helpers.make_indexer_session()


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
        return int(time.mktime(sc_now().timetuple())) > last_refresh + seconds_per_day
    else:
        return True


def set_last_refresh(exception_provider: str) -> None:
    """
    Update last cache update time for shows in list

    :param exception_provider: exception list to set refresh time
    """
    cache_db_con = db.DBConnection("cache.db")
    cache_db_con.upsert("scene_exceptions_refresh", {"last_refreshed": int(time.mktime(sc_now().timetuple()))}, {"list": exception_provider})


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

    exceptions_cache.pop(indexer_id, None)

    for cur_exception in exceptions:
        season = cur_exception["season"]
        show_name = cur_exception["show_name"]
        custom = bool(cur_exception["custom"])

        if season not in all_exceptions_dict:
            all_exceptions_dict[season] = []

        # Deduplication: only add if this exact show_name hasn't been added yet for this season
        if not any(e["show_name"] == show_name for e in all_exceptions_dict[season]):
            all_exceptions_dict[season].append({"show_name": show_name, "custom": custom})

        # Same deduplication for the in-memory cache
        if indexer_id not in exceptions_cache:
            exceptions_cache[indexer_id] = {}
        if season not in exceptions_cache[indexer_id]:
            exceptions_cache[indexer_id][season] = []

        if show_name not in exceptions_cache[indexer_id][season]:
            exceptions_cache[indexer_id][season].append(show_name)

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

            if sanitized_name and sanitized_name not in [e["show_name"] for e in all_exceptions_dict.get(-1, [])]:
                all_exceptions_dict[-1].append({"show_name": sanitized_name, "custom": False})
                if sanitized_name not in exceptions_cache[indexer_id][-1]:
                    exceptions_cache[indexer_id][-1].append(sanitized_name)

            if sanitized_custom_name and sanitized_custom_name not in [e["show_name"] for e in all_exceptions_dict.get(-1, [])]:
                all_exceptions_dict[-1].append({"show_name": sanitized_custom_name, "custom": False})
                if sanitized_custom_name not in exceptions_cache[indexer_id][-1]:
                    exceptions_cache[indexer_id][-1].append(sanitized_custom_name)

        # sort season in exceptions dict by "custom" then "show_name" so alphabetical and custom names are bottom of list
        # sort each season's list
        for season in list(all_exceptions_dict.keys()):
            all_exceptions_dict[season] = sorted(all_exceptions_dict[season], key=lambda x: (x["custom"], x["show_name"].lower()))

    # logger.debug(f"get_all_scene_exceptions: {all_exceptions_dict}")
    # logger.debug(f"exceptions_cache for {indexer_id}: {exceptions_cache.get(indexer_id)}")
    return all_exceptions_dict


def get_scene_exception_by_name(show_name: str) -> tuple:
    return get_scene_exception_by_name_multiple(show_name)[0]


def get_scene_exception_by_name_multiple(show_name) -> list:
    """
    Given a show name, return the indexerid of the exception, None if no exception
    is present.

    Never SELECT the whole scene_exceptions table. Prefer name_cache / exceptions_cache,
    then a targeted equality query; sanitize/dot-space fallback walks exceptions_cache only.
    """
    if not show_name:
        return [(None, None)]

    from sickchill.oldbeard import name_cache

    name_lower = show_name.lower()
    sanitized = helpers.full_sanitizeSceneName(show_name)

    # 1) Sanitized name in name_cache → seasons from exceptions_cache if present
    indexer_id = name_cache.get_id_from_name(show_name)
    if indexer_id is not None:
        out = []
        for season, names in (exceptions_cache.get(int(indexer_id)) or {}).items():
            for cur_name in names:
                if name_lower == cur_name.lower() or sanitized == helpers.full_sanitizeSceneName(cur_name):
                    out.append((int(indexer_id), int(season)))
                    break
        if out:
            return out
        return [(int(indexer_id), -1)]

    # 2) Targeted equality query — never SELECT *
    cache_db_con = db.DBConnection("cache.db")
    exception_result = cache_db_con.select(
        "SELECT indexer_id, season FROM scene_exceptions WHERE LOWER(show_name) = ? ORDER BY season",
        [name_lower],
    )
    if exception_result:
        return [(int(x["indexer_id"]), int(x["season"])) for x in exception_result]

    # 3) Sanitize / dot-space fallback walks exceptions_cache, not the table
    out = []
    for cur_indexer_id, seasons in exceptions_cache.items():
        for season, names in seasons.items():
            for cur_exception_name in names:
                if name_lower in (
                    cur_exception_name.lower(),
                    helpers.sanitizeSceneName(cur_exception_name).lower().replace(".", " "),
                ):
                    out.append((int(cur_indexer_id), int(season)))
                    break

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

    # Keep process-global name cache in sync for this show (no daily-search rebuild path)
    show = Show.find(settings.show_list, indexer_id)
    if show:
        from sickchill.oldbeard import name_cache

        name_cache.build_name_cache(show)


def retrieve_exceptions() -> None:
    """
    Looks up the exceptions on GitHub, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Removes stale official (custom=0) exceptions
    while preserving user custom=1 entries.
    """
    cache_db_con = db.DBConnection("cache.db")

    seen = set()  # (indexerid, name, season)
    updated_shows = set()

    generators = (
        _sickchill_exceptions_generator(),
        _xem_exceptions_generator(),
        _anidb_exceptions_generator(),
    )

    queries = []
    for gen in generators:
        if gen is None:
            continue
        for indexerid, name, season in gen:
            key = (indexerid, name, season)
            if key in seen:
                continue
            seen.add(key)
            updated_shows.add(indexerid)

            # Remove any old official version of this exact exception
            queries.append(["DELETE FROM scene_exceptions WHERE indexer_id = ? AND show_name = ? AND season = ? AND custom = 0;", [indexerid, name, season]])
            # Insert the current official version
            queries.append(["INSERT OR IGNORE INTO scene_exceptions (indexer_id, show_name, season, custom) VALUES (?,?,?, 0);", [indexerid, name, season]])

    if queries:
        cache_db_con.mass_action(queries)

        # Rebuild in-memory cache for affected shows
        for show in list(updated_shows):
            exceptions_cache.pop(show, None)
            rebuild_exception_cache(show)

        logger.debug("Updated scene exceptions")


def _sickchill_exceptions_generator() -> Generator[tuple[int, str, int], None, None]:
    if not should_refresh("sickchill"):
        return

    logger.info("Checking for scene exception updates from sickchill.github.io")
    url = "https://sickchill.github.io/scene_exceptions/scene_exceptions.json"

    # noinspection PyBroadException
    try:
        session = _get_github_session()
        raw = helpers.getURL(url, session=session, returns="json")
        jdata: dict = raw if isinstance(raw, dict) else {}
    except Exception:
        jdata = {}

    if not jdata:
        logger.debug(f"Check scene exceptions update failed (no data). Unable to update from {url}")
        return

    for shows in jdata.values():
        try:
            for indexer_id, exceptions in shows.items():
                for season, names in exceptions.items():
                    for name in names:
                        yield int(indexer_id), name, int(season)
        except Exception:
            logger.debug(f"Check scene exceptions update failed, Unable to update from {url}")
            continue

    set_last_refresh("sickchill")


def _parse_defaulttvdbseason(raw) -> int:
    """ScudLee defaulttvdbseason → scene-exception season.

    ``a`` means absolute / whole-series numbering → generic season -1.
    Missing or non-numeric values default to 1 (ScudLee one-off convention).
    """
    if raw is None:
        return 1
    value = str(raw).strip().lower()
    if not value:
        return 1
    if value == "a":
        return -1
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1


def _show_applicable_tvdb_seasons(show) -> set[int] | None:
    """Seasons that should select among multiple AniDB mappings.

    Optional ``show.default_tvdb_season`` (tests / callers) wins; otherwise
    regular seasons already on the show. ``None`` means “accept all mappings”.
    """
    explicit = getattr(show, "default_tvdb_season", None)
    if explicit is not None:
        try:
            return {int(explicit)}
        except (TypeError, ValueError):
            pass

    episodes = getattr(show, "episodes", None)
    if isinstance(episodes, dict) and episodes:
        seasons = {int(season) for season in episodes if str(season).lstrip("-").isdigit()}
        seasons.discard(0)
        if seasons:
            return seasons
    return None


def _anidb_exceptions_generator() -> Generator[tuple[int, str, int], None, None]:
    """Yield AniDB main titles for local anime shows via ScudLee mapping XMLs.

    This does **not** use the AniDB UDP API. It downloads/parses local caches of
    ``anime-list.xml`` / ``animetitles.xml`` once per refresh, then looks up each
    show. Multiple AniDB ids can share one TVDB id (e.g. 72025 → aid 1 season 1
    and aid 4 season 2); those rows are kept and selected by ``defaulttvdbseason``.
    """
    if not should_refresh("anidb"):
        return

    logger.info("Checking for scene exception updates for AniDB")

    cache_dir = Path(settings.CACHE_DIR) / "anime"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        logger.warning(f"AniDB scene exceptions skipped: cannot create cache dir {cache_dir}: {error}")
        return

    from sickchill.adba import aniDBfileInfo as anidb_files

    anime_list = anidb_files.read_tvdb_map_xml(cache_dir)
    titles_xml = anidb_files.read_anidb_xml(cache_dir)
    if anime_list is None or titles_xml is None:
        logger.warning("AniDB scene exceptions skipped: anime-list/animetitles XML unavailable")
        return

    # tvdb_id -> [(aid, defaulttvdbseason), ...]  — all rows, not first-wins
    tvdb_to_mappings: dict[int, list[tuple[int, int]]] = {}
    for anime in anime_list.findall("anime"):
        try:
            tvdb_id = int(anime.get("tvdbid") or 0)
            aid = int(anime.get("anidbid") or 0)
        except (TypeError, ValueError):
            continue
        if tvdb_id <= 0 or aid <= 0:
            continue
        mapped_season = _parse_defaulttvdbseason(anime.get("defaulttvdbseason"))
        mappings = tvdb_to_mappings.setdefault(tvdb_id, [])
        pair = (aid, mapped_season)
        if pair not in mappings:
            mappings.append(pair)

    aid_to_main_name: dict[int, str] = {}
    xml_lang = "{http://www.w3.org/XML/1998/namespace}lang"
    for anime in titles_xml.findall("anime"):
        try:
            aid = int(anime.get("aid") or 0)
        except (TypeError, ValueError):
            continue
        if not aid:
            continue
        main_name = ""
        for title in anime.findall("title"):
            if title.get("type") == "main" and title.text:
                main_name = title.text
                break
        if not main_name:
            for title in anime.findall("title"):
                if title.get(xml_lang) == "en" and title.text:
                    main_name = title.text
                    break
        if main_name:
            aid_to_main_name[aid] = main_name

    updated = skipped = failed = 0
    for show in settings.show_list:
        if settings.stopping or settings.restarting:
            return

        if not (show.is_anime and show.indexer == 1):
            continue

        try:
            mappings = tvdb_to_mappings.get(int(show.indexerid), [])
            if not mappings:
                skipped += 1
                logger.debug(f"AniDB: no TVDB mapping for {show.name} (tvdb={show.indexerid})")
                continue

            applicable = _show_applicable_tvdb_seasons(show)
            selected: list[tuple[int, int]] = []
            if applicable is None:
                selected = list(mappings)
            else:
                selected = [(aid, season) for aid, season in mappings if season in applicable or season == -1]
                # Absolute/"a" rows already included; if nothing matched, fall back to season 1 then first row
                if not selected:
                    selected = [(aid, season) for aid, season in mappings if season == 1] or mappings[:1]

            yielded = False
            for aid, mapped_season in selected:
                anidb_name = aid_to_main_name.get(aid)
                if not anidb_name:
                    logger.debug(f"AniDB: no title for aid={aid} ({show.name}, tvdb={show.indexerid})")
                    continue
                if anidb_name == show.name:
                    continue
                updated += 1
                yielded = True
                yield int(show.indexerid), anidb_name, mapped_season

            if not yielded:
                skipped += 1
        except Exception as error:
            failed += 1
            logger.debug(f"Could not update anime exceptions from anidb for {show.name}: {error}")

    logger.info(f"AniDB scene exceptions finished: updated={updated}, skipped={skipped}, failed={failed}")
    set_last_refresh("anidb")


def _xem_exceptions_generator() -> Generator[tuple[int, str, int], None, None]:
    if not should_refresh("xem"):
        return

    for indexer, instance in sickchill.indexer:
        logger.info(f"Checking for XEM scene exception updates for {instance.name}")

        url = f"https://thexem.info/map/allNames?origin={instance.slug}&seasonNumbers=1"

        session = get_xem_session()
        parsed_json = helpers.getURL(url, session=session, timeout=90, returns="json")

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
