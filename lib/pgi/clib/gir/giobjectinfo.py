# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import c_char_p, CFUNCTYPE, c_void_p

from .._compat import xrange
from ..glib import gchar_p, gboolean, gint
from ..gobject import GValuePtr
from .gibaseinfo import GIInfoType, GIBaseInfo
from .giinterfaceinfo import GIInterfaceInfo
from .gifieldinfo import GIFieldInfo
from .gipropertyinfo import GIPropertyInfo
from .gicallableinfo import GIFunctionInfo, GISignalInfo, GIVFuncInfo
from .giregisteredtypeinfo import GIRegisteredTypeInfo
from .giconstantinfo import GIConstantInfo
from .gistructinfo import GIStructInfo
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


@GIBaseInfo._register(GIInfoType.OBJECT)
class GIObjectInfo(GIRegisteredTypeInfo):

    def get_methods(self):
        for i in xrange(self.n_methods):
            yield self.get_method(i)

    def get_interfaces(self):
        for i in xrange(self.n_interfaces):
            yield self.get_interface(i)

    def get_properties(self):
        for i in xrange(self.n_properties):
            yield self.get_property(i)

    def get_signals(self):
        for i in xrange(self.n_signals):
            yield self.get_signal(i)

    def get_vfuncs(self):
        for i in xrange(self.n_vfuncs):
            yield self.get_vfunc(i)

    def get_fields(self):
        for i in xrange(self.n_fields):
            yield self.get_field(i)

    def get_constants(self):
        for i in xrange(self.n_constants):
            yield self.get_constant(i)

    def _get_repr(self):
        values = super(GIObjectInfo, self)._get_repr()
        values["type_name"] = repr(self.type_name)
        values["type_init"] = repr(self.type_init)
        values["abstract"] = repr(self.abstract)
        values["fundamental"] = repr(self.fundamental)
        parent = self.get_parent()
        if parent:
            values["parent"] = repr(parent.name)
        values["n_interfaces"] = repr(self.n_interfaces)
        values["n_fields"] = repr(self.n_fields)
        values["n_properties"] = repr(self.n_properties)
        values["n_methods"] = repr(self.n_methods)
        values["n_signals"] = repr(self.n_signals)
        values["n_vfuncs"] = repr(self.n_vfuncs)
        values["class_struct"] = repr(self.get_class_struct().name)
        unref_function = self.unref_function
        if unref_function:
            values["unref_function"] = repr(unref_function)
        ref_function = self.ref_function
        if ref_function:
            values["ref_function"] = repr(ref_function)
        set_value_function = self.set_value_function
        if set_value_function:
            values["set_value_function"] = repr(set_value_function)
        get_value_function = self.get_value_function
        if get_value_function:
            values["get_value_function"] = repr(get_value_function)
        return values


GIObjectInfoGetValueFunction = CFUNCTYPE(c_void_p, GValuePtr)
GIObjectInfoRefFunction = CFUNCTYPE(c_void_p, c_void_p)
GIObjectInfoSetValueFunction = CFUNCTYPE(None, GValuePtr, c_void_p)
GIObjectInfoUnrefFunction = CFUNCTYPE(None, c_void_p)

_methods = [
    ("get_type_name", gchar_p, [GIObjectInfo]),
    ("get_type_init", gchar_p, [GIObjectInfo]),
    ("get_abstract", gboolean, [GIObjectInfo]),
    ("get_fundamental", gboolean, [GIObjectInfo]),
    ("get_parent", GIObjectInfo, [GIObjectInfo], True),
    ("get_n_interfaces", gint, [GIObjectInfo]),
    ("get_interface", GIInterfaceInfo, [GIObjectInfo, gint], True),
    ("get_n_fields", gint, [GIObjectInfo]),
    ("get_field", GIFieldInfo, [GIObjectInfo, gint], True),
    ("get_n_properties", gint, [GIObjectInfo]),
    ("get_property", GIPropertyInfo, [GIObjectInfo, gint], True),
    ("get_n_methods", gint, [GIObjectInfo]),
    ("get_method", GIFunctionInfo, [GIObjectInfo, gint], True),
    ("find_method", GIFunctionInfo, [GIObjectInfo, gchar_p], True),
    ("get_n_signals", gint, [GIObjectInfo]),
    ("get_signal", GISignalInfo, [GIObjectInfo, gint], True),
    ("find_signal", GISignalInfo, [GIObjectInfo, gchar_p], True),
    ("get_n_vfuncs", gint, [GIObjectInfo]),
    ("get_vfunc", GIVFuncInfo, [GIObjectInfo, gint], True),
    ("get_n_constants", gint, [GIObjectInfo]),
    ("get_constant", GIConstantInfo, [GIObjectInfo, gint], True),
    ("get_class_struct", GIStructInfo, [GIObjectInfo], True),
    ("find_vfunc", GIVFuncInfo, [GIObjectInfo, gchar_p], True),
    ("get_unref_function", c_char_p, [GIObjectInfo]),
    ("get_unref_function_pointer", GIObjectInfoUnrefFunction,
        [GIObjectInfo]),
    ("get_ref_function", c_char_p, [GIObjectInfo]),
    ("get_ref_function_pointer", GIObjectInfoRefFunction, [GIObjectInfo]),
    ("get_set_value_function", c_char_p, [GIObjectInfo]),
    ("get_set_value_function_pointer", GIObjectInfoSetValueFunction,
        [GIObjectInfo]),
    ("get_get_value_function", c_char_p, [GIObjectInfo]),
    ("get_get_value_function_pointer", GIObjectInfoGetValueFunction,
        [GIObjectInfo]),
]

wrap_class(_gir, GIObjectInfo, GIObjectInfo, "g_object_info_", _methods)

__all__ = ["GIObjectInfo",
           "GIObjectInfoGetValueFunction", "GIObjectInfoRefFunction",
           "GIObjectInfoSetValueFunction", "GIObjectInfoUnrefFunction"]
