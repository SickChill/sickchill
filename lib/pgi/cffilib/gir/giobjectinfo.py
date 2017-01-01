# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from .._utils import string_decode
from ._ffi import ffi, lib
from .giregisteredtypeinfo import GIRegisteredTypeInfo
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gifunctioninfo import GIFunctionInfo
from .gipropertyinfo import GIPropertyInfo
from .gifieldinfo import GIFieldInfo
from .giconstantinfo import GIConstantInfo
from .gisignalinfo import GISignalInfo, GIVFuncInfo
from .gistructinfo import GIStructInfo
from .giinterfaceinfo import GIInterfaceInfo


@GIBaseInfo._register(GIInfoType.OBJECT)
class GIObjectInfo(GIRegisteredTypeInfo):

    @property
    def abstract(self):
        return lib.g_object_info_get_abstract(self._ptr)

    @property
    def fundamental(self):
        return lib.g_object_info_get_fundamental(self._ptr)

    @property
    def n_methods(self):
        return lib.g_object_info_get_n_methods(self._ptr)

    def get_method(self, n):
        return GIFunctionInfo(lib.g_object_info_get_method(self._ptr, n))

    def get_methods(self):
        for i in xrange(self.n_methods):
            yield self.get_method(i)

    @property
    def n_fields(self):
        return lib.g_object_info_get_n_fields(self._ptr)

    def get_field(self, n):
        return GIFieldInfo(lib.g_object_info_get_field(self._ptr, n))

    def get_fields(self):
        for i in xrange(self.n_fields):
            yield self.get_field(i)

    @property
    def n_constants(self):
        return lib.g_object_info_get_n_constants(self._ptr)

    def get_constant(self, n):
        return GIConstantInfo(lib.g_object_info_get_constant(self._ptr, n))

    def get_constants(self):
        for i in xrange(self.n_constants):
            yield self.get_constant(i)

    @property
    def n_vfuncs(self):
        return lib.g_object_info_get_n_vfuncs(self._ptr)

    def get_vfunc(self, n):
        return GIVFuncInfo(lib.g_object_info_get_vfunc(self._ptr, n))

    def get_vfuncs(self):
        for i in xrange(self.n_vfuncs):
            yield self.get_vfunc(i)

    @property
    def n_signals(self):
        return lib.g_object_info_get_n_signals(self._ptr)

    def get_signal(self, n):
        return GISignalInfo(lib.g_object_info_get_signal(self._ptr, n))

    def get_signals(self):
        for i in xrange(self.n_signals):
            yield self.get_signal(i)

    @property
    def n_interfaces(self):
        return lib.g_object_info_get_n_interfaces(self._ptr)

    def get_interface(self, n):
        return GIInterfaceInfo(lib.g_object_info_get_interface(self._ptr, n))

    def get_interfaces(self):
        for i in xrange(self.n_interfaces):
            yield self.get_interface(i)

    @property
    def n_properties(self):
        return lib.g_object_info_get_n_properties(self._ptr)

    def get_property(self, n):
        return GIPropertyInfo(lib.g_object_info_get_property(self._ptr, n))

    def get_properties(self):
        for i in xrange(self.n_properties):
            yield self.get_property(i)

    @property
    def type_name(self):
        res = lib.g_object_info_get_type_name(self._ptr)
        return string_decode(ffi, res)

    @property
    def type_init(self):
        res = lib.g_object_info_get_type_init(self._ptr)
        return string_decode(ffi, res)

    @property
    def ref_function(self):
        res = lib.g_object_info_get_ref_function(self._ptr)
        return string_decode(ffi, res)

    @property
    def unref_function(self):
        res = lib.g_object_info_get_unref_function(self._ptr)
        return string_decode(ffi, res)

    @property
    def set_value_function(self):
        res = lib.g_object_info_get_set_value_function(self._ptr)
        return string_decode(ffi, res)

    @property
    def get_value_function(self):
        res = lib.g_object_info_get_get_value_function(self._ptr)
        return string_decode(ffi, res)

    def get_class_struct(self):
        res = lib.g_object_info_get_class_struct(self._ptr)
        if res:
            return GIStructInfo(res)
