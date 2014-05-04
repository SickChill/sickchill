# -*- coding: utf-8 -*-
'''
Berkeley Source Database Store.

shove's psuedo-URL for BSDDB stores follows the form:

bsddb://<path>

Where the path is a URL path to a Berkeley database. Alternatively, the native
pathname to a Berkeley database can be passed as the 'engine' parameter.
'''
try:
    import bsddb
except ImportError:
    raise ImportError('requires bsddb library')

import threading

from shove import synchronized
from shove.store import SyncStore


class BsdStore(SyncStore):

    '''Class for Berkeley Source Database Store.'''

    init = 'bsddb://'

    def __init__(self, engine, **kw):
        super(BsdStore, self).__init__(engine, **kw)
        self._store = bsddb.hashopen(self._engine)
        self._lock = threading.Condition()
        self.sync = self._store.sync

    @synchronized
    def __getitem__(self, key):
        return super(BsdStore, self).__getitem__(key)

    @synchronized
    def __setitem__(self, key, value):
        super(BsdStore, self).__setitem__(key, value)

    @synchronized
    def __delitem__(self, key):
        super(BsdStore, self).__delitem__(key)


__all__ = ['BsdStore']
