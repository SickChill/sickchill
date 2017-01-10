# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ..gobject import GParamFlags
from .gibaseinfo import GIBaseInfo
from .gitypeinfo import GITypeInfo, GIInfoType
from .giarginfo import GITransfer
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


@GIBaseInfo._register(GIInfoType.PROPERTY)
class GIPropertyInfo(GIBaseInfo):

    def _get_repr(self):
        values = super(GIPropertyInfo, self)._get_repr()
        values["flags"] = repr(self.flags)
        values["type"] = repr(self.get_type())
        values["ownership_transfer"] = repr(self.ownership_transfer)
        return values

_methods = [
    ("get_flags", GParamFlags, [GIPropertyInfo]),
    ("get_type", GITypeInfo, [GIPropertyInfo], True),
    ("get_ownership_transfer", GITransfer, [GIPropertyInfo]),
]

wrap_class(_gir, GIPropertyInfo, GIPropertyInfo,
           "g_property_info_", _methods)

__all__ = ["GIPropertyInfo"]
