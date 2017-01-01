# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ..glib import gchar_p
from ..gobject import GType
from .gibaseinfo import GIBaseInfo
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


class GIRegisteredTypeInfo(GIBaseInfo):

    def _get_repr(self):
        values = super(GIRegisteredTypeInfo, self)._get_repr()
        values["type_name"] = repr(self.type_name)
        values["type_init"] = repr(self.type_init)
        values["g_type"] = repr(self.g_type)
        return values

_methods = [
    ("get_type_name", gchar_p, [GIRegisteredTypeInfo]),
    ("get_type_init", gchar_p, [GIRegisteredTypeInfo]),
    ("get_g_type", GType, [GIRegisteredTypeInfo]),
]

wrap_class(_gir, GIRegisteredTypeInfo, GIRegisteredTypeInfo,
           "g_registered_type_info_", _methods)

__all__ = ["GIRegisteredTypeInfo"]
