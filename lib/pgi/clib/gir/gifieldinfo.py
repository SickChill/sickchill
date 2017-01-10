# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import POINTER

from ..glib import Flags, gint, gboolean, gpointer
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gitypeinfo import GITypeInfo
from .giargument import GIArgument
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


class GIFieldInfoFlags(Flags):
    IS_READABLE = 1 << 0
    IS_WRITABLE = 1 << 1


@GIBaseInfo._register(GIInfoType.FIELD)
class GIFieldInfo(GIBaseInfo):

    def _get_repr(self):
        values = super(GIFieldInfo, self)._get_repr()
        values["flags"] = repr(self.flags)
        values["size"] = repr(self.size)
        values["offset"] = repr(self.offset)
        values["type"] = repr(self.get_type())
        return values

_methods = [
    ("get_flags", GIFieldInfoFlags, [GIFieldInfo]),
    ("get_size", gint, [GIFieldInfo]),
    ("get_offset", gint, [GIFieldInfo]),
    ("get_type", GITypeInfo, [GIFieldInfo], True),
    ("get_field", gboolean, [GIFieldInfo, gpointer, POINTER(GIArgument)]),
    ("set_field", gboolean, [GIFieldInfo, gpointer, POINTER(GIArgument)]),
]

wrap_class(_gir, GIFieldInfo, GIFieldInfo, "g_field_info_", _methods)

__all__ = ["GIFieldInfo", "GIFieldInfoFlags"]
