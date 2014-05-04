# -*- coding: utf-8 -*-
'''
Single-process in-memory store.

The shove psuedo-URL for a simple store is:

simple://
'''

from shove import BaseStore, SimpleBase


class SimpleStore(SimpleBase, BaseStore):

    '''Single-process in-memory store.'''

    def __init__(self, engine, **kw):
        super(SimpleStore, self).__init__(engine, **kw)


__all__ = ['SimpleStore']
