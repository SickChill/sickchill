# -*- coding: utf-8 -*-
'''
Zope Object Database store frontend.

shove's psuedo-URL for ZODB stores follows the form:

zodb:<path>


Where the path is a URL path to a ZODB FileStorage database. Alternatively, a
native pathname to a ZODB database can be passed as the 'engine' argument.
'''

try:
    import transaction
    from ZODB import FileStorage, DB
except ImportError:
    raise ImportError('Requires ZODB library')

from shove.store import SyncStore


class ZodbStore(SyncStore):

    '''ZODB store front end.'''

    init = 'zodb://'

    def __init__(self, engine, **kw):
        super(ZodbStore, self).__init__(engine, **kw)
        # Handle psuedo-URL
        self._storage = FileStorage.FileStorage(self._engine)
        self._db = DB(self._storage)
        self._connection = self._db.open()
        self._store = self._connection.root()
        # Keeps DB in synch through commits of transactions
        self.sync = transaction.commit

    def close(self):
        '''Closes all open storage and connections.'''
        self.sync()
        super(ZodbStore, self).close()
        self._connection.close()
        self._db.close()
        self._storage.close()


__all__ = ['ZodbStore']
