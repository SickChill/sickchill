# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from ._ffi import lib
from .giregisteredtypeinfo import GIRegisteredTypeInfo
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gifunctioninfo import GIFunctionInfo
from .gipropertyinfo import GIPropertyInfo
from .gistructinfo import GIStructInfo
from .gisignalinfo import GISignalInfo, GIVFuncInfo
from .giconstantinfo import GIConstantInfo


@GIBaseInfo._register(GIInfoType.INTERFACE)
class GIInterfaceInfo(GIRegisteredTypeInfo):

    @property
    def n_methods(self):
        return lib.g_interface_info_get_n_methods(self._ptr)

    def get_method(self, n):
        return GIFunctionInfo(lib.g_interface_info_get_method(self._ptr, n))

    def get_methods(self):
        for i in xrange(self.n_methods):
            yield self.get_method(i)

    @property
    def n_vfuncs(self):
        return lib.g_interface_info_get_n_vfuncs(self._ptr)

    def get_vfunc(self, n):
        return GIVFuncInfo(lib.g_interface_info_get_vfunc(self._ptr, n))

    def get_vfuncs(self):
        for i in xrange(self.n_vfuncs):
            yield self.get_vfunc(i)

    @property
    def n_signals(self):
        return lib.g_interface_info_get_n_signals(self._ptr)

    def get_signal(self, n):
        return GISignalInfo(lib.g_interface_info_get_signal(self._ptr, n))

    def get_signals(self):
        for i in xrange(self.n_signals):
            yield self.get_signal(i)

    @property
    def n_constants(self):
        return lib.g_interface_info_get_n_constants(self._ptr)

    def get_constant(self, n):
        return GIConstantInfo(lib.g_interface_info_get_constant(self._ptr, n))

    def get_constants(self):
        for i in xrange(self.n_constants):
            yield self.get_constant(i)

    @property
    def n_properties(self):
        return lib.g_interface_info_get_n_properties(self._ptr)

    def get_property(self, n):
        return GIPropertyInfo(lib.g_interface_info_get_property(self._ptr, n))

    def get_properties(self):
        for i in xrange(self.n_properties):
            yield self.get_property(i)

    @property
    def n_prerequisites(self):
        return lib.g_interface_info_get_n_prerequisites(self._ptr)

    def get_prerequisite(self, n):
        res = lib.g_interface_info_get_prerequisite(self._ptr, n)
        type_ = GIBaseInfo._get_type(res)
        return type_(res)

    def get_prerequisites(self):
        for i in xrange(self.n_prerequisites):
            yield self.get_prerequisite(i)

    def get_iface_struct(self):
        res = lib.g_interface_info_get_iface_struct(self._ptr)
        if res:
            return GIStructInfo(res)
