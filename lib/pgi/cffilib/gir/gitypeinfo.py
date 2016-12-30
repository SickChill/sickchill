# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .. import _create_enum_class

from ._ffi import ffi, lib
from .gibaseinfo import GIBaseInfo


GIArrayType = _create_enum_class(ffi, "GIArrayType", "GI_ARRAY_TYPE_")


GITypeTag = _create_enum_class(ffi, "GITypeTag", "GI_TYPE_TAG_")


def _g_type_tag_to_string(self):
    res = lib.g_type_tag_to_string(self)
    return ffi.string(res)

GITypeTag.to_string = _g_type_tag_to_string


def _is_basic(self):
    return self < GITypeTag.ARRAY or self == GITypeTag.UNICHAR

GITypeTag.is_basic = property(_is_basic)


class GITypeInfo(GIBaseInfo):

    @property
    def is_pointer(self):
        return lib.g_type_info_is_pointer(self._ptr)

    @property
    def tag(self):
        return GITypeTag(lib.g_type_info_get_tag(self._ptr))

    def get_param_type(self, n):
        return GITypeInfo(lib.g_type_info_get_param_type(self._ptr, n))

    def get_interface(self):
        res = lib.g_type_info_get_interface(self._ptr)
        if res:
            cls = GIBaseInfo._get_type(res)
            return cls(res)

    @property
    def array_length(self):
        return lib.g_type_info_get_array_length(self._ptr)

    @property
    def array_fixed_size(self):
        return lib.g_type_info_get_array_fixed_size(self._ptr)

    @property
    def is_zero_terminated(self):
        return lib.g_type_info_is_zero_terminated(self._ptr)

    @property
    def array_type(self):
        return GIArrayType(lib.g_type_info_get_array_type(self._ptr))
