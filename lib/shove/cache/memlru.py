# -*- coding: utf-8 -*-
'''
Thread-safe in-memory cache using LRU.

The shove psuedo-URL for a memory cache is:

memlru://
'''

import copy
import threading

from shove import synchronized
from shove.cache.simplelru import SimpleLRUCache


class MemoryLRUCache(SimpleLRUCache):

    '''Thread-safe in-memory cache backend using LRU.'''

    def __init__(self, engine, **kw):
        super(MemoryLRUCache, self).__init__(engine, **kw)
        self._lock = threading.Condition()

    @synchronized
    def __setitem__(self, key, value):
        super(MemoryLRUCache, self).__setitem__(key, value)

    @synchronized
    def __getitem__(self, key):
        return copy.deepcopy(super(MemoryLRUCache, self).__getitem__(key))

    @synchronized
    def __delitem__(self, key):
        super(MemoryLRUCache, self).__delitem__(key)


__all__ = ['MemoryLRUCache']
