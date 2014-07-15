# -*- coding: utf-8 -*-
'''
DBM Database Store.

shove's psuedo-URL for DBM stores follows the form:

dbm://<path>

Where <path> is a URL path to a DBM database. Alternatively, the native
pathname to a DBM database can be passed as the 'engine' parameter.
'''

import anydbm

from shove.store import SyncStore


class DbmStore(SyncStore):

    '''Class for variants of the DBM database.'''

    init = 'dbm://'

    def __init__(self, engine, **kw):
        super(DbmStore, self).__init__(engine, **kw)
        self._store = anydbm.open(self._engine, 'c')
        try:
            self.sync = self._store.sync
        except AttributeError:
            pass


__all__ = ['DbmStore']
