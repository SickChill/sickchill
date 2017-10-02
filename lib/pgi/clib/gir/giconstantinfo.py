# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import POINTER

from ..glib import gint
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gitypeinfo import GITypeInfo
from .giargument import GIArgument
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


@GIBaseInfo._register(GIInfoType.CONSTANT)
class GIConstantInfo(GIBaseInfo):

    def _get_repr(self):
        values = super(GIConstantInfo, self)._get_repr()
        values["type"] = repr(self.get_type())
        return values

_methods = [
    ("get_type", GITypeInfo, [GIConstantInfo], True),
    ("get_value", gint, [GIConstantInfo, POINTER(GIArgument)]),
]

wrap_class(_gir, GIConstantInfo, GIConstantInfo,
           "g_constant_info_", _methods)

__all__ = ["GIConstantInfo"]
