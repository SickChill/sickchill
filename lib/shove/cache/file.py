# -*- coding: utf-8 -*-
'''
File-based cache

shove's psuedo-URL for file caches follows the form:

file://<path>

Where the path is a URL path to a directory on a local filesystem.
Alternatively, a native pathname to the directory can be passed as the 'engine'
argument.
'''

import time

from shove import FileBase
from shove.cache.simple import SimpleCache


class FileCache(FileBase, SimpleCache):

    '''File-based cache backend'''

    def __init__(self, engine, **kw):
        super(FileCache, self).__init__(engine, **kw)

    def __getitem__(self, key):
        try:
            exp, value = super(FileCache, self).__getitem__(key)
            # Remove item if time has expired.
            if exp < time.time():
                del self[key]
                raise KeyError(key)
            return value
        except:
            raise KeyError(key)

    def __setitem__(self, key, value):
        if len(self) >= self._max_entries:
            self._cull()
        super(FileCache, self).__setitem__(
            key, (time.time() + self.timeout, value)
        )


__all__ = ['FileCache']
