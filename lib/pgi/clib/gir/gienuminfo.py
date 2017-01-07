# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from ..glib import gint64, gint, gchar_p
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gicallableinfo import GIFunctionInfo
from .gitypeinfo import GITypeTag
from .giregisteredtypeinfo import GIRegisteredTypeInfo
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


@GIBaseInfo._register(GIInfoType.VALUE)
class GIValueInfo(GIBaseInfo):

    def _get_repr(self):
        values = super(GIValueInfo, self)._get_repr()
        values["value"] = repr(self.value_)
        return values

_methods = [
    ("get_value", gint64, [GIValueInfo]),
]

wrap_class(_gir, GIValueInfo, GIValueInfo, "g_value_info_", _methods)


@GIBaseInfo._register(GIInfoType.FLAGS)
@GIBaseInfo._register(GIInfoType.ENUM)
class GIEnumInfo(GIRegisteredTypeInfo):

    def get_values(self):
        for i in xrange(self.n_values):
            yield self.get_value(i)

    def get_methods(self):
        for i in xrange(self.n_methods):
            yield self.get_method(i)

    def _get_repr(self):
        values = super(GIEnumInfo, self)._get_repr()
        values["n_values"] = repr(self.n_values)
        values["n_methods"] = repr(self.n_methods)
        values["storage_type"] = repr(self.storage_type)
        return values

_methods = [
    ("get_n_values", gint, [GIEnumInfo]),
    ("get_value", GIValueInfo, [GIEnumInfo, gint], True),
    ("get_n_methods", gint, [GIEnumInfo]),
    ("get_method", GIFunctionInfo, [GIEnumInfo], True),
    ("get_storage_type", GITypeTag, [GIEnumInfo]),
    ("get_error_domain", gchar_p, [GIEnumInfo]),
]

wrap_class(_gir, GIEnumInfo, GIEnumInfo, "g_enum_info_", _methods)

__all__ = ["GIEnumInfo", "GIValueInfo"]
