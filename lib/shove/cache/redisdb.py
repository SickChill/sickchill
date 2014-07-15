# -*- coding: utf-8 -*-
'''
Redis-based object cache

The shove psuedo-URL for a redis cache is:

redis://<host>:<port>/<db>
'''

import urlparse

try:
    import redis
except ImportError:
    raise ImportError('This store requires the redis library')

from shove import Base


class RedisCache(Base):

    '''Redis cache backend'''

    init = 'redis://'

    def __init__(self, engine, **kw):
        super(RedisCache, self).__init__(engine, **kw)
        spliturl = urlparse.urlsplit(engine)
        host, port = spliturl[1].split(':')
        db = spliturl[2].replace('/', '')
        self._store = redis.Redis(host, int(port), db)
        # Set timeout
        self.timeout = kw.get('timeout', 300)

    def __getitem__(self, key):
        return self.loads(self._store[key])

    def __setitem__(self, key, value):
        self._store.setex(key, self.dumps(value), self.timeout)

    def __delitem__(self, key):
        self._store.delete(key)


__all__ = ['RedisCache']
