# -*- coding: utf-8 -*-

from urllib import url2pathname
from shove.store.simple import SimpleStore


class ClientStore(SimpleStore):

    '''Base class for stores where updates have to be committed.'''

    def __init__(self, engine, **kw):
        super(ClientStore, self).__init__(engine, **kw)
        if engine.startswith(self.init):
            self._engine = url2pathname(engine.split('://')[1])

    def __getitem__(self, key):
        return self.loads(super(ClientStore, self).__getitem__(key))

    def __setitem__(self, key, value):
        super(ClientStore, self).__setitem__(key, self.dumps(value))


class SyncStore(ClientStore):

    '''Base class for stores where updates have to be committed.'''

    def __getitem__(self, key):
        return self.loads(super(SyncStore, self).__getitem__(key))

    def __setitem__(self, key, value):
        super(SyncStore, self).__setitem__(key, value)
        try:
            self.sync()
        except AttributeError:
            pass

    def __delitem__(self, key):
        super(SyncStore, self).__delitem__(key)
        try:
            self.sync()
        except AttributeError:
            pass


__all__ = [
    'bsdb', 'db', 'dbm', 'durusdb', 'file', 'ftp', 'memory', 's3', 'simple',
    'svn', 'zodb', 'redisdb', 'hdf5db', 'leveldbstore', 'cassandra',
]
