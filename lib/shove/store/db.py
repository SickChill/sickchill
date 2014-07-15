# -*- coding: utf-8 -*-
'''
Database object store.

The shove psuedo-URL used for database object stores is the format used by
SQLAlchemy:

<driver>://<username>:<password>@<host>:<port>/<database>

<driver> is the database engine. The engines currently supported SQLAlchemy are
sqlite, mysql, postgres, oracle, mssql, and firebird.
<username> is the database account user name
<password> is the database accound password
<host> is the database location
<port> is the database port
<database> is the name of the specific database

For more information on specific databases see:

http://www.sqlalchemy.org/docs/dbengine.myt#dbengine_supported
'''

try:
    from sqlalchemy import MetaData, Table, Column, String, Binary, select
    from shove import BaseStore, DbBase
except ImportError, e:
    raise ImportError('Error: ' + e + ' Requires SQLAlchemy >= 0.4')


class DbStore(BaseStore, DbBase):

    '''Database cache backend.'''

    def __init__(self, engine, **kw):
        super(DbStore, self).__init__(engine, **kw)
        # Get tablename
        tablename = kw.get('tablename', 'store')
        # Bind metadata
        self._metadata = MetaData(engine)
        # Make store table
        self._store = Table(tablename, self._metadata,
            Column('key', String(255), primary_key=True, nullable=False),
            Column('value', Binary, nullable=False),
        )
        # Create store table if it does not exist
        if not self._store.exists():
            self._store.create()

    def __getitem__(self, key):
        row = select(
            [self._store.c.value], self._store.c.key == key,
        ).execute().fetchone()
        if row is not None:
            return self.loads(str(row.value))
        raise KeyError(key)

    def __setitem__(self, k, v):
        v, store = self.dumps(v), self._store
        # Update database if key already present
        if k in self:
            store.update(store.c.key == k).execute(value=v)
        # Insert new key if key not present
        else:
            store.insert().execute(key=k, value=v)

    def keys(self):
        '''Returns a list of keys in the store.'''
        return list(i[0] for i in select(
            [self._store.c.key]
        ).execute().fetchall())


__all__ = ['DbStore']
