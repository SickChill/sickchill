import os
import threading
import urllib
import urlparse
import re
import time
import sickbeard

from sickbeard import logger
from sickbeard import encodingKludge as ek
from sickbeard.exceptions import ex
from lib.shove import Shove
from lib.feedcache import cache

feed_lock = threading.Lock()

class RSSFeeds:
    def __init__(self, db_name):
        try:
            self.fs = self.fs = Shove('sqlite:///' + ek.ek(os.path.join, sickbeard.CACHE_DIR, db_name + '.db'), compress=True)
            self.fc = cache.Cache(self.fs)
        except Exception, e:
            logger.log(u"RSS error: " + ex(e), logger.ERROR)
            raise

    def __del__(self):
        self.fs.close()

    def clearCache(self, age=None):
        with feed_lock:
            self.fc.purge(age)

    def getFeed(self, url, post_data=None, request_headers=None):
        with feed_lock:
            parsed = list(urlparse.urlparse(url))
            parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one

            if post_data:
                url += urllib.urlencode(post_data)

            feed = self.fc.fetch(url, False, False, request_headers)
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
