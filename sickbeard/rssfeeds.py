from __future__ import with_statement

import os
import urllib

import sickbeard

from sickbeard import logger
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex

from feedcache.cache import Cache

from sqliteshelf import SQLiteShelf


class RSSFeeds:
    def __init__(self, db_name='feeds'):
        try:
            db_name = ek(os.path.join, sickbeard.CACHE_DIR, 'rss', db_name) + '.db'
            if not os.path.exists(os.path.dirname(db_name)):
                sickbeard.helpers.makeDir(os.path.dirname(db_name))

            self.rssDB = SQLiteShelf(db_name)
        except Exception as e:
            logger.log(u"FeedParser error: " + ex(e), logger.DEBUG)

    def clearCache(self, age=None):
        try:
            Cache(self.rssDB).purge(age)
        finally:
            self.rssDB.close()

    def getFeed(self, url, post_data=None, request_headers=None, items=None, handlers=[]):

        if post_data:
            url += urllib.urlencode(post_data)

        try:
            resp = Cache(self.rssDB, userAgent=sickbeard.common.USER_AGENT).fetch(url, force_update=True, request_headers=request_headers, handlers=handlers)
        finally:
            self.rssDB.close()

        return resp
