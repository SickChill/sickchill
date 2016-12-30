# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .. import _create_enum_class
from ._ffi import ffi, lib
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gitypeinfo import GITypeInfo


GIFieldInfoFlags = _create_enum_class(
    ffi, "GIFieldInfoFlags", "GI_FIELD_", flags=True)


@GIBaseInfo._register(GIInfoType.FIELD)
class GIFieldInfo(GIBaseInfo):

    @property
    def flags(self):
        return GIFieldInfoFlags(lib.g_field_info_get_flags(self._ptr))

    @property
    def size(self):
        return lib.g_field_info_get_size(self._ptr)

    @property
    def offset(self):
        return lib.g_field_info_get_offset(self._ptr)

    def get_type(self):
        return GITypeInfo(lib.g_field_info_get_type(self._ptr))

    def get_field(self, mem, value):
        return lib.g_field_info_get_field(self._ptr, mem, value)

    def set_field(self, mem, value):
        return lib.g_field_info_set_field(self._ptr, mem, value)
