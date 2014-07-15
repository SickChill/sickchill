# -*- coding: utf-8 -*-
'''
Filesystem-based object store

shove's psuedo-URL for filesystem-based stores follows the form:

file://<path>

Where the path is a URL path to a directory on a local filesystem.
Alternatively, a native pathname to the directory can be passed as the 'engine'
argument.
'''

from shove import BaseStore, FileBase


class FileStore(FileBase, BaseStore):

    '''File-based store.'''

    def __init__(self, engine, **kw):
        super(FileStore, self).__init__(engine, **kw)


__all__ = ['FileStore']
