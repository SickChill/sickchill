# -*- coding: utf-8 -*-
'''
FTP-accessed stores

shove's URL for FTP accessed stores follows the standard form for FTP URLs
defined in RFC-1738:

ftp://<user>:<password>@<host>:<port>/<url-path>
'''

import urlparse
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from ftplib import FTP, error_perm

from shove import BaseStore


class FtpStore(BaseStore):

    def __init__(self, engine, **kw):
        super(FtpStore, self).__init__(engine, **kw)
        user = kw.get('user', 'anonymous')
        password = kw.get('password', '')
        spliturl = urlparse.urlsplit(engine)
        # Set URL, path, and strip 'ftp://' off
        base, path = spliturl[1], spliturl[2] + '/'
        if '@' in base:
            auth, base = base.split('@')
            user, password = auth.split(':')
        self._store = FTP(base, user, password)
        # Change to remote path if it exits
        try:
            self._store.cwd(path)
        except error_perm:
            self._makedir(path)
        self._base, self._user, self._password = base, user, password
        self._updated, self ._keys = True, None

    def __getitem__(self, key):
        try:
            local = StringIO()
            # Download item
            self._store.retrbinary('RETR %s' % key, local.write)
            self._updated = False
            return self.loads(local.getvalue())
        except:
            raise KeyError(key)

    def __setitem__(self, key, value):
        local = StringIO(self.dumps(value))
        self._store.storbinary('STOR %s' % key, local)
        self._updated = True

    def __delitem__(self, key):
        try:
            self._store.delete(key)
            self._updated = True
        except:
            raise KeyError(key)

    def _makedir(self, path):
        '''Makes remote paths on an FTP server.'''
        paths = list(reversed([i for i in path.split('/') if i != '']))
        while paths:
            tpath = paths.pop()
            self._store.mkd(tpath)
            self._store.cwd(tpath)

    def keys(self):
        '''Returns a list of keys in a store.'''
        if self._updated or self._keys is None:
            rlist, nlist = list(), list()
            # Remote directory listing
            self._store.retrlines('LIST -a', rlist.append)
            for rlisting in rlist:
                # Split remote file based on whitespace
                rfile = rlisting.split()
                # Append tuple of remote item type & name
                if rfile[-1] not in ('.', '..') and rfile[0].startswith('-'):
                    nlist.append(rfile[-1])
            self._keys = nlist
        return self._keys


__all__ = ['FtpStore']
