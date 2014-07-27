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
        self.db_name = ek.ek(os.path.join, sickbeard.CACHE_DIR, 'rss', db_name + '.db')
        if not os.path.exists(os.path.dirname(self.db_name)):
            sickbeard.helpers.makeDir(os.path.dirname(self.db_name))

    def clearCache(self, age=None):
        try:
            with closing(Shove('sqlite:///' + self.db_name, compress=True)) as fs:
                fc = cache.Cache(fs)
                fc.purge(age)
        except Exception as e:
            logger.log(u"RSS error clearing cache: " + ex(e), logger.DEBUG)

    def getFeed(self, url, post_data=None, request_headers=None):
        parsed = list(urlparse.urlparse(url))
        parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one

        if post_data:
            url += urllib.urlencode(post_data)

        try:
            with closing(Shove('sqlite:///' + self.db_name, compress=True)) as fs:
                fc = cache.Cache(fs)
                feed = fc.fetch(url, False, False, request_headers)

                if not feed or not feed.entries:
                    logger.log(u"RSS error loading url: " + url, logger.DEBUG)
                    return
                elif 'error' in feed.feed:
                    err_code = feed.feed['error']['code']
                    err_desc = feed.feed['error']['description']

                    logger.log(
                        u"RSS ERROR:[%s] CODE:[%s]" % (err_desc, err_code), logger.DEBUG)
                    return
                else:
                    return feed
        except Exception as e:
            logger.log(u"RSS error: " + ex(e), logger.DEBUG)