# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from ._ffi import lib
from .gibaseinfo import GIBaseInfo, GIInfoType
from .giregisteredtypeinfo import GIRegisteredTypeInfo
from .gifieldinfo import GIFieldInfo
from .gifunctioninfo import GIFunctionInfo


@GIBaseInfo._register(GIInfoType.STRUCT)
class GIStructInfo(GIRegisteredTypeInfo):

    @property
    def n_fields(self):
        return lib.g_struct_info_get_n_fields(self._ptr)

    def get_field(self, n):
        return GIFieldInfo(lib.g_struct_info_get_field(self._ptr, n))

    def get_fields(self):
        for i in xrange(self.n_fields):
            yield self.get_field(i)

    @property
    def size(self):
        return lib.g_struct_info_get_size(self._ptr)

    @property
    def alignment(self):
        return lib.g_struct_info_get_alignment(self._ptr)

    @property
    def is_gtype_struct(self):
        return lib.g_struct_info_is_gtype_struct(self._ptr)

    @property
    def is_foreign(self):
        return lib.g_struct_info_is_foreign(self._ptr)

    @property
    def n_methods(self):
        return lib.g_struct_info_get_n_methods(self._ptr)

    def get_method(self, n):
        return GIFunctionInfo(lib.g_struct_info_get_method(self._ptr, n))

    def get_methods(self):
        for i in xrange(self.n_methods):
            yield self.get_method(i)
