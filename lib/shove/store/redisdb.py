# -*- coding: utf-8 -*-
'''
Redis-based object store

The shove psuedo-URL for a redis-based store is:

redis://<host>:<port>/<db>
'''

import urlparse

try:
    import redis
except ImportError:
    raise ImportError('This store requires the redis library')

from shove.store import ClientStore


class RedisStore(ClientStore):

    '''Redis based store'''

    init = 'redis://'

    def __init__(self, engine, **kw):
        super(RedisStore, self).__init__(engine, **kw)
        spliturl = urlparse.urlsplit(engine)
        host, port = spliturl[1].split(':')
        db = spliturl[2].replace('/', '')
        self._store = redis.Redis(host, int(port), db)

    def __contains__(self, key):
        return self._store.exists(key)

    def clear(self):
        self._store.flushdb()

    def keys(self):
        return self._store.keys()

    def setdefault(self, key, default=None):
        return self._store.getset(key, default)

    def update(self, other=None, **kw):
        args = kw if other is not None else other
        self._store.mset(args)


__all__ = ['RedisStore']
