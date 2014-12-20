from __future__ import with_statement

import os
import urllib
import urlparse
import re
import collections

import sickbeard

from sickbeard import logger
from sickbeard import encodingKludge as ek
from sickbeard.exceptions import ex

from feedcache.cache import Cache
from sqliteshelf import SQLiteShelf


class RSSFeeds:
    def __init__(self, db_name):
        try:
            db_name = ek.ek(os.path.join, sickbeard.CACHE_DIR, 'rss', db_name) + '.db'
            if not os.path.exists(os.path.dirname(db_name)):
                sickbeard.helpers.makeDir(os.path.dirname(db_name))

            self.rssDB = SQLiteShelf(db_name)
        except Exception as e:
            logger.log(u"RSS error: " + ex(e), logger.DEBUG)

    def clearCache(self, age=None):
        try:
            fc = Cache(self.rssDB).purge(age)
            fc.purge(age)
        finally:
            self.rssDB.close()

    def getFeed(self, url, post_data=None, request_headers=None, items=[]):
        parsed = list(urlparse.urlparse(url))
        parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one

        if post_data:
            url += urllib.urlencode(post_data)

        data = dict.fromkeys(items, None)

        try:
            fc = Cache(self.rssDB)
            resp = fc.fetch(url, False, False, request_headers=request_headers)

            for item in items:
                try:
                    data[item] = resp[item]
                except:
                    continue

        finally:
            self.rssDB.close()

        return data