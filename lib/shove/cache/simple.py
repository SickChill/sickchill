# -*- coding: utf-8 -*-
'''
Single-process in-memory cache.

The shove psuedo-URL for a simple cache is:

simple://
'''

import time
import random

from shove import SimpleBase


class SimpleCache(SimpleBase):

    '''Single-process in-memory cache.'''

    def __init__(self, engine, **kw):
        super(SimpleCache, self).__init__(engine, **kw)
        # Get random seed
        random.seed()
        # Set maximum number of items to cull if over max
        self._maxcull = kw.get('maxcull', 10)
        # Set max entries
        self._max_entries = kw.get('max_entries', 300)
        # Set timeout
        self.timeout = kw.get('timeout', 300)

    def __getitem__(self, key):
        exp, value = super(SimpleCache, self).__getitem__(key)
        # Delete if item timed out.
        if exp < time.time():
            super(SimpleCache, self).__delitem__(key)
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        # Cull values if over max # of entries
        if len(self) >= self._max_entries:
            self._cull()
        # Set expiration time and value
        exp = time.time() + self.timeout
        super(SimpleCache, self).__setitem__(key, (exp, value))

    def _cull(self):
        '''Remove items in cache to make room.'''
        num, maxcull = 0, self._maxcull
        # Cull number of items allowed (set by self._maxcull)
        for key in self.keys():
            # Remove only maximum # of items allowed by maxcull
            if num <= maxcull:
                # Remove items if expired
                try:
                    self[key]
                except KeyError:
                    num += 1
            else:
                break
        # Remove any additional items up to max # of items allowed by maxcull
        while len(self) >= self._max_entries and num <= maxcull:
            # Cull remainder of allowed quota at random
            del self[random.choice(self.keys())]
            num += 1


__all__ = ['SimpleCache']
