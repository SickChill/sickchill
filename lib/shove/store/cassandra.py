# -*- coding: utf-8 -*-
'''
Cassandra-based object store

The shove psuedo-URL for a cassandra-based store is:

cassandra://<host>:<port>/<keyspace>/<columnFamily>
'''

import urlparse

try:
    import pycassa
except ImportError:
    raise ImportError('This store requires the pycassa library')

from shove import BaseStore


class CassandraStore(BaseStore):

    '''Cassandra based store'''

    init = 'cassandra://'

    def __init__(self, engine, **kw):
        super(CassandraStore, self).__init__(engine, **kw)
        spliturl = urlparse.urlsplit(engine)
        _, keyspace, column_family = spliturl[2].split('/')
        try:
            self._pool = pycassa.connect(keyspace, [spliturl[1]])
            self._store = pycassa.ColumnFamily(self._pool, column_family)
        except pycassa.InvalidRequestException:
            from pycassa.system_manager import SystemManager
            system_manager = SystemManager(spliturl[1])
            system_manager.create_keyspace(
                keyspace,
                pycassa.system_manager.SIMPLE_STRATEGY,
                {'replication_factor': str(kw.get('replication', 1))}
            )
            system_manager.create_column_family(keyspace, column_family)
            self._pool = pycassa.connect(keyspace, [spliturl[1]])
            self._store = pycassa.ColumnFamily(self._pool, column_family)

    def __getitem__(self, key):
        try:
            item = self._store.get(key).get(key)
            if item is not None:
                return self.loads(item)
            raise KeyError(key)
        except pycassa.NotFoundException:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self._store.insert(key, dict(key=self.dumps(value)))

    def __delitem__(self, key):
        # beware eventual consistency
        try:
            self._store.remove(key)
        except pycassa.NotFoundException:
            raise KeyError(key)

    def clear(self):
        # beware eventual consistency
        self._store.truncate()

    def keys(self):
        return list(i[0] for i in self._store.get_range())


__all__ = ['CassandraStore']
