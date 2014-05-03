# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from sickbeard import db
from sickbeard.helpers import sanitizeSceneName


def addNameToCache(name, indexer_id=0):
    """
    Adds the show & tvdb id to the scene_names table in cache.db.
    
    name: The show name to cache
    indexer_id: the TVDB and TVRAGE id that this show should be cached with (can be None/0 for unknown)
    """

    # standardize the name we're using to account for small differences in providers
    name = sanitizeSceneName(name)
    cacheDB = db.DBConnection('cache.db')
    cacheDB.action("INSERT INTO scene_names (indexer_id, name) VALUES (?, ?)", [indexer_id, name])


def retrieveNameFromCache(name):
    """
    Looks up the given name in the scene_names table in cache.db.
    
    name: The show name to look up.
    
    Returns: the TVDB and TVRAGE id that resulted from the cache lookup or None if the show wasn't found in the cache
    """

    # standardize the name we're using to account for small differences in providers
    name = sanitizeSceneName(name)

    cacheDB = db.DBConnection('cache.db')
    cache_results = cacheDB.select("SELECT * FROM scene_names WHERE name = ?", [name])

    if cache_results:
        return int(cache_results[0]["indexer_id"])

def clearCache():
    """
    Deletes all "unknown" entries from the cache (names with indexer_id of 0).
    """
    cacheDB = db.DBConnection('cache.db')
    cacheDB.action("DELETE FROM scene_names WHERE indexer_id = ?", [0])

