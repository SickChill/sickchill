# -*- coding: utf-8 -*-
'''
Thread-safe in-memory store.

The shove psuedo-URL for a memory store is:

memory://
'''

import copy
import threading

from shove import synchronized
from shove.store.simple import SimpleStore


class MemoryStore(SimpleStore):

    '''Thread-safe in-memory store.'''

    def __init__(self, engine, **kw):
        super(MemoryStore, self).__init__(engine, **kw)
        self._lock = threading.Condition()

    @synchronized
    def __getitem__(self, key):
        return copy.deepcopy(super(MemoryStore, self).__getitem__(key))

    @synchronized
    def __setitem__(self, key, value):
        super(MemoryStore, self).__setitem__(key, value)

    @synchronized
    def __delitem__(self, key):
        super(MemoryStore, self).__delitem__(key)


__all__ = ['MemoryStore']
