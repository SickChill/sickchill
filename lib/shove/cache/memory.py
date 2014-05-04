# -*- coding: utf-8 -*-
'''
Thread-safe in-memory cache.

The shove psuedo-URL for a memory cache is:

memory://
'''

import copy
import threading

from shove import synchronized
from shove.cache.simple import SimpleCache


class MemoryCache(SimpleCache):

    '''Thread-safe in-memory cache backend.'''

    def __init__(self, engine, **kw):
        super(MemoryCache, self).__init__(engine, **kw)
        self._lock = threading.Condition()

    @synchronized
    def __setitem__(self, key, value):
        super(MemoryCache, self).__setitem__(key, value)

    @synchronized
    def __getitem__(self, key):
        return copy.deepcopy(super(MemoryCache, self).__getitem__(key))

    @synchronized
    def __delitem__(self, key):
        super(MemoryCache, self).__delitem__(key)


__all__ = ['MemoryCache']
