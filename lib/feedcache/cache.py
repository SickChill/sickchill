#!/usr/bin/env python
#
# Copyright 2007 Doug Hellmann.
#
#
#                         All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software and
# its documentation for any purpose and without fee is hereby
# granted, provided that the above copyright notice appear in all
# copies and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of Doug
# Hellmann not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission.
#
# DOUG HELLMANN DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
# NO EVENT SHALL DOUG HELLMANN BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

"""

"""

__module_id__ = "$Id$"

#
# Import system modules
#
from feedparser import feedparser

import logging
import time

#
# Import local modules
#


#
# Module
#

logger = logging.getLogger('feedcache.cache')


class Cache:
    """A class to wrap Mark Pilgrim's Universal Feed Parser module
    (http://www.feedparser.org) so that parameters can be used to
    cache the feed results locally instead of fetching the feed every
    time it is requested. Uses both etag and modified times for
    caching.
    """

    def __init__(self, storage, timeToLiveSeconds=300, userAgent='feedcache'):
        """
        Arguments:

          storage -- Backing store for the cache.  It should follow
          the dictionary API, with URLs used as keys.  It should
          persist data.

          timeToLiveSeconds=300 -- The length of time content should
          live in the cache before an update is attempted.

          userAgent='feedcache' -- User agent string to be used when
          fetching feed contents.

        """
        self.storage = storage
        self.time_to_live = timeToLiveSeconds
        self.user_agent = userAgent
        return

    def purge(self, olderThanSeconds):
        """Remove cached data from the storage if the data is older than the
        date given.  If olderThanSeconds is None, the entire cache is purged.
        """
        if olderThanSeconds is None:
            logger.debug('purging the entire cache')
            for key in self.storage.keys():
                del self.storage[key]
        else:
            now = time.time()
            # Iterate over the keys and load each item one at a time
            # to avoid having the entire cache loaded into memory
            # at one time.
            for url in self.storage.keys():
                (cached_time, cached_data) = self.storage[url]
                age = now - cached_time
                if age >= olderThanSeconds:
                    logger.debug('removing %s with age %d', url, age)
                    del self.storage[url]
        return

    def fetch(self, url, force_update=False, offline=False, request_headers=None, referrer=None, handlers=[]):
        """Return the feed at url.

        url - The URL of the feed.

        force_update=False - When True, update the cache whether the
                                           current contents have
                                           exceeded their time-to-live
                                           or not.

        offline=False - When True, only return data from the local
                                 cache and never access the remote
                                 URL.

        request_headers=None - Add addition request headers to request

        referrer=None - Added a referrer to request

        handlers=None - Urllib2 handlers

        If there is data for that feed in the cache already, check
        the expiration date before accessing the server.  If the
        cached data has not expired, return it without accessing the
        server.

        In cases where the server is accessed, check for updates
        before deciding what to return.  If the server reports a
        status of 304, the previously cached content is returned.

        The cache is only updated if the server returns a status of
        200, to avoid holding redirected data in the cache.
        """
        logger.debug('url="%s"' % url)

        # Convert the URL to a value we can use
        # as a key for the storage backend.
        key = url
        if isinstance(key, unicode):
            key = key.encode('utf-8')

        modified = None
        etag = None
        now = time.time()

        cached_time, cached_content = self.storage.get(key, (None, None))

        # Offline mode support (no networked requests)
        # so return whatever we found in the storage.
        # If there is nothing in the storage, we'll be returning None.
        if offline:
            logger.debug('offline mode')
            return cached_content

        # Does the storage contain a version of the data
        # which is older than the time-to-live?
        logger.debug('cache modified time: %s' % str(cached_time))
        if cached_time is not None and not force_update:
            if self.time_to_live:
                age = now - cached_time
                if age <= self.time_to_live:
                    logger.debug('cache contents still valid')
                    return cached_content
                else:
                    logger.debug('cache contents older than TTL')
            else:
                logger.debug('no TTL value')

            # The cache is out of date, but we have
            # something.  Try to use the etag and modified_time
            # values from the cached content.
            etag = cached_content.get('etag')
            modified = cached_content.get('modified')
            logger.debug('cached etag=%s' % etag)
            logger.debug('cached modified=%s' % str(modified))
        else:
            logger.debug('nothing in the cache, or forcing update')

        # We know we need to fetch, so go ahead and do it.
        logger.debug('fetching...')
        parsed_result = feedparser.parse(url,
                                         agent=self.user_agent,
                                         modified=modified,
                                         etag=etag,
                                         referrer=referrer,
                                         request_headers=request_headers,
                                         handlers = handlers)

        status = parsed_result.get('status', None)
        logger.debug('HTTP status=%s' % status)
        if status == 304:
            # No new data, based on the etag or modified values.
            # We need to update the modified time in the
            # storage, though, so we know that what we have
            # stored is up to date.
            self.storage[key] = (now, cached_content)

            # Return the data from the cache, since
            # the parsed data will be empty.
            parsed_result = cached_content
        elif status == 200:
            # There is new content, so store it unless there was an error.
            error = parsed_result.get('bozo_exception')
            if not error:
                logger.debug('Updating stored data for %s' % url)
                self.storage[key] = (now, parsed_result)
            else:
                logger.warning('Not storing data with exception: %s',
                               error)
        else:
            logger.warning('Not updating cache with HTTP status %s', status)

        return parsed_result
