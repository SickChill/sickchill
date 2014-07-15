# -*- coding: utf-8 -*-
'''
File-based LRU cache

shove's psuedo-URL for file caches follows the form:

file://<path>

Where the path is a URL path to a directory on a local filesystem.
Alternatively, a native pathname to the directory can be passed as the 'engine'
argument.
'''

from shove import FileBase
from shove.cache.simplelru import SimpleLRUCache


class FileCache(FileBase, SimpleLRUCache):

    '''File-based LRU cache backend'''


__all__ = ['FileCache']
