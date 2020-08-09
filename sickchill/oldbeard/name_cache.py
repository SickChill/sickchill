import threading

from sickchill import settings
from sickchill.oldbeard import helpers, scene_exceptions

from . import db

# from . import logger

nameCache = {}
nameCacheLock = threading.Lock()


def addNameToCache(name, indexer_id=0):
    """
    Adds the show & tvdb id to the scene_names table in cache.db.

    :param name: The show name to cache
    :param indexer_id: the TVDB id that this show should be cached with (can be None/0 for unknown)
    """
    cache_db_con = db.DBConnection('cache.db')

    # standardize the name we're using to account for small differences in providers
    name = helpers.full_sanitizeSceneName(name)
    if name not in nameCache:
        nameCache[name] = int(indexer_id)
        cache_db_con.action("INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)", [indexer_id, name])


def retrieveNameFromCache(name):
    """
    Looks up the given name in the scene_names table in cache.db.

    :param name: The show name to look up.
    :return: the TVDB id that resulted from the cache lookup or None if the show wasn't found in the cache
    """
    name = helpers.full_sanitizeSceneName(name)
    if name in nameCache:
        return int(nameCache[name])


def clearCache(indexerid=0):
    """
    Deletes all "unknown" entries from the cache (names with indexer_id of 0).
    """
    cache_db_con = db.DBConnection('cache.db')
    cache_db_con.action("DELETE FROM scene_names WHERE indexer_id = ? OR indexer_id = ?", (indexerid, 0))

    toRemove = [key for key, value in nameCache.items() if value in (0, indexerid)]
    for key in toRemove:
        del nameCache[key]


def saveNameCacheToDb():
    """Commit cache to database file"""
    cache_db_con = db.DBConnection('cache.db')

    for name, indexer_id in nameCache.items():
        cache_db_con.action("INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)", [indexer_id, name])


def buildNameCache(show=None):
    """Build internal name cache

    :param show: Specify show to build name cache for, if None, just do all shows
    """
    with nameCacheLock:
        scene_exceptions.retrieve_exceptions()

    if not show:
        # logger.info("Building internal name cache for all shows")
        for show in settings.showList:
            buildNameCache(show)
    else:
        # logger.debug("Building internal name cache for " + show.name)
        clearCache(show.indexerid)
        for curSeason in [-1] + scene_exceptions.get_scene_seasons(show.indexerid):
            for name in set(scene_exceptions.get_scene_exceptions(show.indexerid, season=curSeason) + [show.name]):
                name = helpers.full_sanitizeSceneName(name)
                if name in nameCache:
                    continue

                nameCache[name] = int(show.indexerid)
        # logger.debug("Internal name cache for " + show.name + " set to: [ " + ', '.join([key for key, value in nameCache.items() if value == show.indexerid]) + " ]")
