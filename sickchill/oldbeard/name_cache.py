import threading

from sickchill import settings
from sickchill.oldbeard import helpers, scene_exceptions
from sickchill.show.Show import Show

from .. import logger
from . import db

name_cache = {}
name_cache_lock = threading.Lock()


def add_name(name, indexer_id=0):
    """
    Adds the show & tvdb id to the scene_names table in cache.db.

    :param name: The show name to cache
    :param indexer_id: the TVDB id that this show should be cached with (can be None/0 for unknown)
    """

    # standardize the name we're using to account for small differences in providers
    name = helpers.full_sanitizeSceneName(name)
    if name not in name_cache:
        name_cache[name] = int(indexer_id)
        cache_db_con = db.DBConnection("cache.db")
        cache_db_con.action("INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)", [indexer_id, name])


def get_id_from_name(name):
    """
    Looks up the given name in the scene_names table in cache.db.

    :param name: The show name to look up.
    :return: the TVDB id that resulted from the cache lookup or None if the show wasn't found in the cache
    """
    name = helpers.full_sanitizeSceneName(name)
    if name not in name_cache:
        cache_db_con = db.DBConnection("cache.db")
        results = cache_db_con.select_one("SELECT indexer_id FROM scene_names WHERE name = ?", [name])
        if results:
            indexer_id = results["indexer_id"]
            show = Show.find(settings.showList, indexer_id)
            if show:
                build_name_cache(show)
    else:
        return int(name_cache[name])


def clear_cache(indexerid=0):
    """
    Deletes all "unknown" entries from the cache (names with indexer_id of 0).
    """
    cache_db_con = db.DBConnection("cache.db")
    cache_db_con.action("DELETE FROM scene_names WHERE indexer_id = ? OR indexer_id = ?", (indexerid, 0))

    to_remove = [key for key, value in name_cache.items() if value in (0, indexerid)]
    for key in to_remove:
        del name_cache[key]


def save_all_cached_names():
    """Commit cache to database file"""
    cache_db_con = db.DBConnection("cache.db")

    for name, indexer_id in name_cache.items():
        cache_db_con.action("INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)", [indexer_id, name])


def build_name_cache(show=None):
    """Build internal name cache

    :param show: Specify show to build name cache for, if None, just do all shows
    """
    with name_cache_lock:
        scene_exceptions.retrieve_exceptions()

    if not show:
        # logger.info("Building internal name cache for all shows")
        for show in settings.showList:
            build_name_cache(show)
    else:
        logger.debug("Building internal name cache for " + show.name)
        clear_cache(show.indexerid)
        for season in scene_exceptions.get_all_scene_exceptions(show.indexerid).values():
            for exception in season:
                name_cache[helpers.full_sanitizeSceneName(exception["show_name"])] = int(show.indexerid)

        name_cache[helpers.full_sanitizeSceneName(show.show_name)] = int(show.indexerid)
        if show.custom_name:
            name_cache[helpers.full_sanitizeSceneName(show.custom_name)] = int(show.indexerid)

        logger.debug(
            "Internal name cache for " + show.name + " set to: [ " + ", ".join([key for key, value in name_cache.items() if value == show.indexerid]) + " ]"
        )
