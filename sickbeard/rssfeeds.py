from __future__ import with_statement

import os
import urllib
import urlparse
import re
import sickbeard

from sickbeard import logger
from sickbeard import encodingKludge as ek
from contextlib import closing
from sickbeard.exceptions import ex
from lib.feedcache import cache
from shove import Shove


class RSSFeeds:
    def __init__(self, db_name):
        self.db_name = ek.ek(os.path.join, sickbeard.CACHE_DIR, db_name + '.db')

    def clearCache(self, age=None):
        try:
            with closing(Shove('sqlite:///' + self.db_name, compress=True)) as fs:
                fc = cache.Cache(fs)
                fc.purge(age)
        except:
            os.remove(self.db_name)
            try:
                with closing(Shove('sqlite:///' + self.db_name, compress=True)) as fs:
                    fc = cache.Cache(fs)
                    fc.purge(age)
            except Exception as e:
                logger.log(u"RSS cache error: " + ex(e), logger.DEBUG)

    def getFeed(self, url, post_data=None, request_headers=None):
        parsed = list(urlparse.urlparse(url))
        parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one

        if post_data:
            url += urllib.urlencode(post_data)

        try:
            with closing(Shove('sqlite:///' + self.db_name, compress=True)) as fs:
                fc = cache.Cache(fs)
                feed = fc.fetch(url, False, False, request_headers)
        except:
            os.remove(self.db_name)
            try:
                with closing(Shove('sqlite:///' + self.db_name, compress=True)) as fs:
                    fc = cache.Cache(fs)
                    feed = fc.fetch(url, False, False, request_headers)
            except Exception as e:
                logger.log(u"RSS cache error: " + ex(e), logger.DEBUG)
                feed = None

        if not feed:
            logger.log(u"RSS Error loading URL: " + url, logger.ERROR)
            return
        elif 'error' in feed.feed:
            logger.log(u"RSS ERROR:[%s] CODE:[%s]" % (feed.feed['error']['description'], feed.feed['error']['code']),
                       logger.DEBUG)
            return
        elif not feed.entries:
            logger.log(u"No RSS items found using URL: " + url, logger.WARNING)
            return

        return feed
