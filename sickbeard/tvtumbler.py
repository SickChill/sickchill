'''
Created on Aug 26, 2013

Wrappers around tvtumbler access.

@author: dermot@buckley.ie
'''
import time

from sickbeard import helpers
from sickbeard import logger

try:
    import json
except ImportError:
    from lib import simplejson as json

UPDATE_INTERVAL = 432000  # 5 days
SHOW_LOOKUP_URL = 'http://show-api.tvtumbler.com/api/show'
_tvtumber_cache = {}


def show_info(indexer_id):
    try:
        cachedResult = _tvtumber_cache[str(indexer_id)]
        if time.time() < (cachedResult['mtime'] + UPDATE_INTERVAL):
            # cached result is still considered current, use it
            return cachedResult['response']
            # otherwise we just fall through to lookup
    except KeyError:
        pass  # no cached value, just fall through to lookup

    url = SHOW_LOOKUP_URL + '?indexer_id=' + str(indexer_id)
    data = helpers.getURL(url, timeout=60)  # give this a longer timeout b/c it may take a while
    result = json.loads(data)
    if not result:
        logger.log(u"Empty lookup result -> failed to find show id", logger.DEBUG)
        return None
    if result['error']:
        logger.log(u"Lookup failed: " + result['errorMessage'], logger.DEBUG)
        return None

    # result is good, store it for later
    _tvtumber_cache[str(indexer_id)] = {'mtime': time.time(),
                                        'response': result['show']}

    return result['show']
