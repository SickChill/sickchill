#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    requests_cache.backends
    ~~~~~~~~~~~~~~~~~~~~~~~

    Classes and functions for cache persistence
"""


from .base import BaseCache

registry = {
    'memory': BaseCache,
}

try:
    # Heroku doesn't allow the SQLite3 module to be installed
    from .sqlite import DbCache
    registry['sqlite'] = DbCache
except ImportError:
    DbCache = None

try:
    from .mongo import MongoCache
    registry['mongo'] = registry['mongodb'] = MongoCache
except ImportError:
    MongoCache = None

try:
    from .redis import RedisCache
    registry['redis'] = RedisCache
except ImportError:
    RedisCache = None


def create_backend(backend_name, cache_name, options):
    if backend_name is None:
        backend_name = _get_default_backend_name()
    try:
        return registry[backend_name](cache_name, **options)
    except KeyError:
        raise ValueError('Unsupported backend "%s" try one of: %s' %
                         (backend_name, ', '.join(registry.keys())))


def _get_default_backend_name():
    if 'sqlite' in registry:
        return 'sqlite'
    return 'memory'