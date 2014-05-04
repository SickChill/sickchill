# -*- coding: utf-8 -*-
'''
Durus object database frontend.

shove's psuedo-URL for Durus stores follows the form:

durus://<path>


Where the path is a URL path to a durus FileStorage database. Alternatively, a
native pathname to a durus database can be passed as the 'engine' parameter.
'''

try:
    from durus.connection import Connection
    from durus.file_storage import FileStorage
except ImportError:
    raise ImportError('Requires Durus library')

from shove.store import SyncStore


class DurusStore(SyncStore):

    '''Class for Durus object database frontend.'''

    init = 'durus://'

    def __init__(self, engine, **kw):
        super(DurusStore, self).__init__(engine, **kw)
        self._db = FileStorage(self._engine)
        self._connection = Connection(self._db)
        self.sync = self._connection.commit
        self._store = self._connection.get_root()

    def close(self):
        '''Closes all open storage and connections.'''
        self.sync()
        self._db.close()
        super(DurusStore, self).close()


__all__ = ['DurusStore']
