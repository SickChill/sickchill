import threading

from sickchill import logger, settings
from sickchill.oldbeard import db, helpers, scene_exceptions

name_cache = {}
names_by_indexer = {}
name_cache_lock = threading.Lock()


def _add_mapping(name, indexer_id):
    """Sanitize once and write both maps. Skip empty names. Caller must hold name_cache_lock."""
    name = helpers.full_sanitizeSceneName(name)
    if not name:
        return None

    indexer_id = int(indexer_id)
    name_cache[name] = indexer_id
    names_by_indexer.setdefault(indexer_id, set()).add(name)
    return name


def _drop_indexer(indexer_id):
    """Remove that id's names from both maps. Caller must hold name_cache_lock. Returns removed names."""
    indexer_id = int(indexer_id)
    names = names_by_indexer.pop(indexer_id, None)
    if not names:
        return set()

    for name in names:
        if name_cache.get(name) == indexer_id:
            del name_cache[name]
    return names


def _log_show_cache(show):
    """Log cached names for a show via reverse map (no full-dict scan). Caller may hold the lock."""
    names = names_by_indexer.get(int(show.indexerid), set())
    logger.debug("Internal name cache for " + show.name + " set to: [ " + ", ".join(sorted(names)) + " ]")


def _load_persisted_names(indexer_id=None):
    """Load scene_names rows into both maps. Caller must hold name_cache_lock."""
    cache_db_con = db.DBConnection("cache.db")
    if indexer_id is None:
        rows = cache_db_con.select("SELECT name, indexer_id FROM scene_names")
    else:
        rows = cache_db_con.select("SELECT name, indexer_id FROM scene_names WHERE indexer_id = ?", [int(indexer_id)])

    for row in rows:
        _add_mapping(row["name"], row["indexer_id"])


def add_name(name, indexer_id=0):
    """
    Adds the show & tvdb id to the scene_names table in cache.db.

    :param name: The show name to cache
    :param indexer_id: the TVDB id that this show should be cached with (can be None/0 for unknown)
    """
    with name_cache_lock:
        sanitized = helpers.full_sanitizeSceneName(name)
        if not sanitized or sanitized in name_cache:
            return

        _add_mapping(sanitized, indexer_id)
        cache_db_con = db.DBConnection("cache.db")
        cache_db_con.action("INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)", [int(indexer_id), sanitized])
        logger.debug(f"Internal name cache add: {sanitized!r} -> {int(indexer_id)}")


def get_id_from_name(name):
    """
    Looks up the given name in the process-global name cache (dict only).

    :param name: The show name to look up.
    :return: the TVDB id that resulted from the cache lookup or None if the show wasn't found in the cache
    """
    name = helpers.full_sanitizeSceneName(name)
    if not name:
        return None

    with name_cache_lock:
        if name in name_cache:
            return int(name_cache[name])
    return None


def drop_indexer(indexer_id):
    """Remove one indexer_id from both in-memory maps and persisted scene_names rows."""
    indexer_id = int(indexer_id)
    with name_cache_lock:
        cache_db_con = db.DBConnection("cache.db")
        cache_db_con.action("DELETE FROM scene_names WHERE indexer_id = ?", [indexer_id])
        removed = _drop_indexer(indexer_id)
        if removed:
            logger.debug("Internal name cache removed for indexer_id " + str(indexer_id) + ": [ " + ", ".join(sorted(removed)) + " ]")


def clear_cache(indexerid=0):
    """
    Deletes entries for indexerid (and unknown id 0) from cache.db and both in-memory maps.
    Uses the reverse map — no full-dict scan.
    """
    indexerid = int(indexerid)
    cache_db_con = db.DBConnection("cache.db")
    cache_db_con.action("DELETE FROM scene_names WHERE indexer_id = ? OR indexer_id = ?", (indexerid, 0))

    with name_cache_lock:
        _drop_indexer(indexerid)
        if indexerid != 0:
            _drop_indexer(0)


def save_all_cached_names():
    """Commit cache to database file in one mass_action write.

    Holds name_cache_lock through the write so a concurrent drop_indexer cannot
    leave a stale snapshot that recreates deleted scene_names rows.
    """
    with name_cache_lock:
        items = list(name_cache.items())
        if not items:
            return

        cache_db_con = db.DBConnection("cache.db")
        cache_db_con.mass_action([["INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)", [indexer_id, name]] for name, indexer_id in items])


def build_name_cache(show=None):
    """Build internal name cache

    :param show: Specify show to build name cache for, if None, just do all shows
    """
    with name_cache_lock:
        scene_exceptions.retrieve_exceptions()

        if not show:
            logger.debug("Building internal name cache for all shows")
            name_cache.clear()
            names_by_indexer.clear()

            for cur_show in settings.show_list:
                if settings.stopping or settings.restarting:
                    break
                _build_show_name_cache_locked(cur_show)

            # Remaining scene_names rows (after per-show stale purge) e.g. indexer_id 0
            _load_persisted_names()
            for cur_show in settings.show_list:
                if settings.stopping or settings.restarting:
                    break
                _log_show_cache(cur_show)
        else:
            _build_show_name_cache_locked(show)
            _load_persisted_names(show.indexerid)
            _log_show_cache(show)


def _build_show_name_cache_locked(show):
    """Refresh in-memory mappings for one show. Caller must hold name_cache_lock.

    Purges persisted scene_names aliases for this indexer that are no longer in the
    active set (scene exceptions + show_name + custom_name) so deleted aliases cannot
    return via _load_persisted_names or after restart.
    """
    indexer_id = int(show.indexerid)
    active = set()

    for season in scene_exceptions.get_all_scene_exceptions(indexer_id).values():
        for exception in season:
            name = helpers.full_sanitizeSceneName(exception["show_name"])
            if name:
                active.add(name)

    for candidate in (show.show_name, show.custom_name):
        if not candidate:
            continue
        name = helpers.full_sanitizeSceneName(candidate)
        if name:
            active.add(name)

    # Drop memory first, then purge stale DB aliases, then re-add active mappings
    _drop_indexer(indexer_id)

    cache_db_con = db.DBConnection("cache.db")
    if active:
        placeholders = ",".join("?" * len(active))
        cache_db_con.action(
            f"DELETE FROM scene_names WHERE indexer_id = ? AND name NOT IN ({placeholders})",
            [indexer_id, *active],
        )
    else:
        cache_db_con.action("DELETE FROM scene_names WHERE indexer_id = ?", [indexer_id])

    for name in active:
        _add_mapping(name, indexer_id)
