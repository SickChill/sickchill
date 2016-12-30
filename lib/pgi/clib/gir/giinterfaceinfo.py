# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from ..glib import gint, gchar_p
from .gibaseinfo import GIInfoType, GIBaseInfo
from .gipropertyinfo import GIPropertyInfo
from .gicallableinfo import GIFunctionInfo, GISignalInfo, GIVFuncInfo
from .giconstantinfo import GIConstantInfo
from .gistructinfo import GIStructInfo
from .giregisteredtypeinfo import GIRegisteredTypeInfo
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


@GIBaseInfo._register(GIInfoType.INTERFACE)
class GIInterfaceInfo(GIRegisteredTypeInfo):

    def get_methods(self):
        for i in xrange(self.n_methods):
            yield self.get_method(i)

    def get_properties(self):
        for i in xrange(self.n_properties):
            yield self.get_property(i)

    def get_signals(self):
        for i in xrange(self.n_signals):
            yield self.get_signal(i)

    def get_constants(self):
        for i in xrange(self.n_constants):
            yield self.get_constant(i)

    def get_vfuncs(self):
        for i in xrange(self.n_vfuncs):
            yield self.get_vfunc(i)

    def get_prerequisite(self, i):
        res = self._get_prerequisite(i)
        return GIBaseInfo._cast(res)

    def get_prerequisites(self):
        for i in xrange(self.n_prerequisites):
            yield self.get_prerequisite(i)

    def _get_repr(self):
        values = super(GIInterfaceInfo, self)._get_repr()
        values["n_constants"] = repr(self.n_constants)
        values["n_signals"] = repr(self.n_signals)
        values["n_methods"] = repr(self.n_methods)
        values["n_properties"] = repr(self.n_properties)
        values["n_prerequisites"] = repr(self.n_prerequisites)
        return values

_methods = [
    ("get_n_prerequisites", gint, [GIInterfaceInfo]),
    ("_get_prerequisite", GIBaseInfo, [GIInterfaceInfo, gint]),
    ("get_n_properties", gint, [GIInterfaceInfo]),
    ("get_property", GIPropertyInfo, [GIInterfaceInfo, gint], True),
    ("get_n_methods", gint, [GIInterfaceInfo]),
    ("get_method", GIFunctionInfo, [GIInterfaceInfo, gint], True),
    ("find_method", GIFunctionInfo, [GIInterfaceInfo, gchar_p], True),
    ("get_n_signals", gint, [GIInterfaceInfo]),
    ("get_signal", GISignalInfo, [GIInterfaceInfo, gint], True),
    ("find_signal", GISignalInfo, [GIInterfaceInfo, gchar_p], True),
    ("get_n_vfuncs", gint, [GIInterfaceInfo]),
    ("get_vfunc", GIVFuncInfo, [GIInterfaceInfo, gint], True),
    ("get_n_constants", gint, [GIInterfaceInfo]),
    ("get_constant", GIConstantInfo, [GIInterfaceInfo, gint], True),
    ("get_iface_struct", GIStructInfo, [GIInterfaceInfo], True),
    ("find_vfunc", GIVFuncInfo, [GIInterfaceInfo, gchar_p], True),
]

wrap_class(_gir, GIInterfaceInfo, GIInterfaceInfo,
           "g_interface_info_", _methods)

__all__ = ["GIInterfaceInfo"]
