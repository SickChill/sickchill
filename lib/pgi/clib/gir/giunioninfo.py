# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from ..glib import gint, gboolean, gchar_p, gsize
from .gibaseinfo import GIInfoType, GIBaseInfo
from .gifieldinfo import GIFieldInfo
from .gicallableinfo import GIFunctionInfo
from .gitypeinfo import GITypeInfo
from .giconstantinfo import GIConstantInfo
from .giregisteredtypeinfo import GIRegisteredTypeInfo
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


@GIBaseInfo._register(GIInfoType.UNION)
class GIUnionInfo(GIRegisteredTypeInfo):

    def get_methods(self):
        return map(self.get_method, xrange(self.n_methods))

    def get_fields(self):
        for i in xrange(self.n_fields):
            yield self.get_field(i)

    def _get_repr(self):
        values = super(GIUnionInfo, self)._get_repr()
        values = {}
        values["n_fields"] = repr(self.n_fields)
        values["is_discriminated"] = repr(self.is_discriminated)
        values["discriminator_offset"] = repr(self.discriminator_offset)
        values["discriminator_type"] = repr(self.get_discriminator_type())
        values["size"] = repr(self.size)
        values["alignment"] = repr(self.alignment)
        values["n_methods"] = repr(self.n_methods)

        return values

_methods = [
    ("get_n_fields", gint, [GIUnionInfo]),
    ("get_field", GIFieldInfo, [GIUnionInfo, gint], True),
    ("get_n_methods", gint, [GIUnionInfo]),
    ("get_method", GIFunctionInfo, [GIUnionInfo, gint], True),
    ("is_discriminated", gboolean, [GIUnionInfo]),
    ("get_discriminator_offset", gint, [GIUnionInfo]),
    ("get_discriminator_type", GITypeInfo, [GIUnionInfo], True),
    ("get_discriminator", GIConstantInfo, [GIUnionInfo, gint], True),
    ("find_method", GIFunctionInfo, [GIUnionInfo, gchar_p], True),
    ("get_size", gsize, [GIUnionInfo]),
    ("get_alignment", gsize, [GIUnionInfo]),
]

wrap_class(_gir, GIUnionInfo, GIUnionInfo, "g_union_info_", _methods)

__all__ = ["GIUnionInfo"]
