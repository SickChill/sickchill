# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from ._ffi import ffi, lib
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gitypeinfo import GITypeInfo
from .giarginfo import GITransfer, GIArgInfo


class GICallableInfo(GIBaseInfo):

    def get_return_type(self):
        return GITypeInfo(lib.g_callable_info_get_return_type(self._ptr))

    @property
    def caller_owns(self):
        return GITransfer(lib.g_callable_info_get_caller_owns(self._ptr))

    @property
    def can_throw_gerror(self):
        return lib.g_callable_info_can_throw_gerror(self._ptr)

    @property
    def may_return_null(self):
        return lib.g_callable_info_may_return_null(self._ptr)

    def get_return_attribute(self, name):
        res = lib.g_callable_info_get_return_attribute(self._ptr)
        if res:
            return ffi.string(res)

    def iterate_return_attributes(self):
        it = ffi.new("GIAttributeIter*")
        name = ffi.new("char**")
        value = ffi.new("char**")
        while lib.g_callable_info_iterate_return_attributes(
                self._ptr, it, name, value):
            yield (ffi.string(name[0]), ffi.string(value[0]))

    @property
    def n_args(self):
        return lib.g_callable_info_get_n_args(self._ptr)

    def get_arg(self, n):
        return GIArgInfo(lib.g_callable_info_get_arg(self._ptr, n))

    def get_args(self):
        for i in xrange(self.n_args):
            yield self.get_arg(i)

    def load_arg(self, n, args):
        # warning: lifetime bound to this info
        info = ffi.new("GIArgInfo*")
        lib.g_callable_info_load_arg(self._ptr, info)
        return GIArgInfo(info)

    def load_return_type(self):
        # warning: lifetime bound to this info
        info = ffi.new("GITypeInfo*")
        lib.g_callable_info_load_return_type(self._ptr, info)
        return GITypeInfo(info)

    @property
    def skip_return(self):
        return lib.g_callable_info_skip_return(self._ptr)


@GIBaseInfo._register(GIInfoType.CALLBACK)
class GICallbackInfo(GICallableInfo):
    pass
