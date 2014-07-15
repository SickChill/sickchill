# -*- coding: utf-8 -*-
'''
LevelDB Database Store.

shove's psuedo-URL for LevelDB stores follows the form:

leveldb://<path>

Where <path> is a URL path to a LevelDB database. Alternatively, the native
pathname to a LevelDB database can be passed as the 'engine' parameter.
'''

try:
    import leveldb
except ImportError:
    raise ImportError('This store requires py-leveldb library')

from shove.store import ClientStore


class LevelDBStore(ClientStore):

    '''LevelDB based store'''

    init = 'leveldb://'

    def __init__(self, engine, **kw):
        super(LevelDBStore, self).__init__(engine, **kw)
        self._store = leveldb.LevelDB(self._engine)

    def __getitem__(self, key):
        item = self.loads(self._store.Get(key))
        if item is not None:
            return item
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._store.Put(key, self.dumps(value))

    def __delitem__(self, key):
        self._store.Delete(key)

    def keys(self):
        return list(k for k in self._store.RangeIter(include_value=False))


__all__ = ['LevelDBStore']
