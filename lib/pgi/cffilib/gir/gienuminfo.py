# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from .._utils import string_decode
from ._ffi import lib, ffi
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gitypeinfo import GITypeTag
from .giregisteredtypeinfo import GIRegisteredTypeInfo
from .gifunctioninfo import GIFunctionInfo


class GIValueInfo(GIBaseInfo):

    @property
    def value_(self):
        return lib.g_value_info_get_value(self._ptr)


@GIBaseInfo._register(GIInfoType.FLAGS)
@GIBaseInfo._register(GIInfoType.ENUM)
class GIEnumInfo(GIRegisteredTypeInfo):

    @property
    def n_values(self):
        return lib.g_enum_info_get_n_values(self._ptr)

    def get_value(self, n):
        res = lib.g_enum_info_get_value(self._ptr, n)
        if res:
            return GIValueInfo(res)

    def get_values(self):
        for i in xrange(self.n_values):
            yield self.get_value(i)

    @property
    def n_methods(self):
        return lib.g_enum_info_get_n_methods(self._ptr)

    def get_method(self, n):
        return GIFunctionInfo(lib.g_enum_info_get_method(self._ptr, n))

    def get_methods(self):
        for i in xrange(self.n_methods):
            yield self.get_method(i)

    @property
    def storage_type(self):
        return GITypeTag(lib.g_enum_info_get_storage_type(self._ptr))

    @property
    def error_domain(self):
        res = lib.g_enum_info_get_error_domain(self._ptr)
        return string_decode(ffi, res)
