# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ._ffi import ffi, lib
from ..glib import memdup, free, gerror
from .._utils import string_decode
from .error import GIError


class GITypelib(object):
    def __init__(self, ptr):
        self._ptr = ptr

    def free(self):
        lib.g_typelib_free(self._ptr)

    @property
    def namespace(self):
        res = lib.g_typelib_get_namespace(self._ptr)
        return string_decode(ffi, res)

    @classmethod
    def new_from_memory(self, data):
        size = len(data)
        mem_ptr = memdup(data, size)
        mem = ffi.cast("uint8_t*", mem_ptr)
        try:
            with gerror(GIError) as error:
                ptr = lib.g_typelib_new_from_memory(mem, size, error)
                return GITypelib(ptr)
        except GIError:
            free(mem_ptr)
            raise

    def __repr__(self):
        return "<%s namespace=%r>" % (type(self).__name__, self.namespace)
