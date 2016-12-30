# Copyright 2012,2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import POINTER, Structure, CFUNCTYPE

from .glib import Flags, gulong, gchar_p, guint, gboolean, gpointer, guint32
from .glib import guint64, gchar, guchar, gint, glong, gint64, gfloat
from .glib import gdouble
from ._utils import find_library, wrap_class

_gobject = find_library("gobject-2.0")


class GParamFlags(Flags):
    READABLE = 1 << 0
    WRITABLE = 1 << 1
    CONSTRUCT = 1 << 2
    CONSTRUCT_ONLY = 1 << 3
    LAX_VALIDATION = 1 << 4
    STATIC_NAME = 1 << 5
    STATIC_NICK = 1 << 6
    STATIC_BLURB = 1 << 7
    DEPRECATED = 1 << 31


class GTypeFundamentalFlags(Flags):
    CLASSED = 1 << 0
    INSTANTIATABLE = 1 << 1
    DERIVABLE = 1 << 2
    DEEP_DERIVABLE = 1 << 3


class GTypeFlags(Flags):
    ABSTRACT = 1 << 4
    VALUE_ABSTRACT = 1 << 5


class GFlagsValue(Structure):
    _fields_ = [
        ("value", guint),
        ("value_name", gchar_p),
        ("value_nick", gchar_p),
    ]


class GFlagsValuePtr(POINTER(GFlagsValue)):
    _type_ = GFlagsValue


class GFlagsClass(Structure):
    pass


class GFlagsClassPtr(POINTER(GFlagsClass)):
    _type_ = GFlagsClass


_methods = [
    ("get_first_value", GFlagsValuePtr, [GFlagsClassPtr, guint]),
]

wrap_class(_gobject, GFlagsClass, GFlagsClassPtr, "g_flags_", _methods)


class GEnumValue(Structure):
    _fields_ = [
        ("value", gint),
        ("value_name", gchar_p),
        ("value_nick", gchar_p),
    ]


class GEnumValuePtr(POINTER(GEnumValue)):
    _type_ = GEnumValue


class GEnumClass(Structure):
    pass


class GEnumClassPtr(POINTER(GEnumClass)):
    _type_ = GEnumClass


_methods = [
    ("get_value", GEnumValuePtr, [GEnumClassPtr, gint]),
]

wrap_class(_gobject, GEnumClass, GEnumClassPtr, "g_enum_", _methods)


class GType(gulong):
    def __repr__(self):
        return "<GType %r>" % repr(self.value)


class GTypeInterface(Structure):
    _fields_ = [
        ("g_type", GType),
        ("g_instance_type", GType),
    ]


class GTypeInterfacePtr(POINTER(GTypeInterface)):
    _type_ = GTypeInterface


class GObjectClass(Structure):
    pass


class GObjectClassPtr(POINTER(GObjectClass)):
    _type_ = GObjectClass


_methods = [
    ("name", gchar_p, [GType]),
    ("depth", guint, [GType]),
    ("parent", GType, [GType]),
    ("from_name", GType, [gchar_p]),
    ("check_is_value_type", gboolean, [GType]),
    ("test_flags", gboolean, [GType, GTypeFlags]),
    ("value_table_peek", gpointer, [GType]),  # returns GTypeValueTable
    ("is_a", gboolean, [GType, GType]),
    ("fundamental", GType, [GType]),
    ("children", POINTER(GType), [GType, POINTER(guint)]),
    ("interfaces", POINTER(GType), [GType, POINTER(guint)]),
    ("class_peek", gpointer, [GType]),
    ("class_ref", gpointer, [GType]),
    ("class_unref", None, [gpointer]),
    ("class_peek_parent", gpointer, [gpointer]),
    ("default_interface_ref", GTypeInterfacePtr, [GType]),
    ("default_interface_peek", GTypeInterfacePtr, [GType]),
    ("default_interface_unref", None, [GTypeInterfacePtr]),
]

wrap_class(_gobject, GType, GType, "g_type_", _methods)


class GTypeClass(Structure):
    _fields_ = [
        ("g_type", GType),
    ]


class GTypeClassPtr(POINTER(GTypeClass)):
    _type_ = GTypeClass


class GTypeInstance(Structure):
    _fields_ = [
        ("g_class", GTypeClassPtr),
    ]


class GTypeInstancePtr(POINTER(GTypeInstance)):
    _type_ = GTypeInstance


class GParamSpec(Structure):
    _fields_ = [
        ("g_type_instance", GTypeInstance),
        ("name", gchar_p),
        ("flags", GParamFlags),
        ("value_type", GType),
        ("owner_type", GType),
    ]


class GParamSpecPtr(POINTER(GParamSpec)):
    _type_ = GParamSpec


_methods = [
    ("find_property", GParamSpecPtr, [GTypeInterfacePtr, gchar_p]),
    ("install_property", None, [GTypeInterfacePtr, GParamSpecPtr]),
    ("list_properties ", POINTER(GParamSpecPtr),
     [GTypeInterfacePtr, POINTER(guint)]),
]

wrap_class(_gobject, GTypeInterface, GTypeInterfacePtr,
           "g_object_interface_", _methods)


class GSignalFlags(Flags):
    RUN_FIRST = 1 << 0
    RUN_LAST = 1 << 1
    RUN_CLEANUP = 1 << 2
    NO_RECURSE = 1 << 3
    DETAILED = 1 << 4
    ACTION = 1 << 5
    NO_HOOKS = 1 << 6
    MUST_COLLECT = 1 << 7

g_type_init = _gobject.g_type_init
g_type_init.argtypes = []
g_type_init.restype = None


class GObject(Structure):
    _fields_ = [
        ("g_type_instance", GTypeInstance),
        ("ref_count", guint32),
    ]

GObjectPtr = POINTER(GObject)


class GValue(Structure):
    _fields_ = [
        ("g_type", GType),
        ("dummy", guint64 * 2),
    ]


class GValuePtr(POINTER(GValue)):
    _type_ = GValue

GValueTransform = CFUNCTYPE(None, GValuePtr, GValuePtr)

_methods = [
    ("init", GValuePtr, [GValuePtr, GType]),
    ("copy", None, [GValuePtr, GValuePtr]),
    ("reset", GValuePtr, [GValuePtr]),
    ("unset", None, [GValuePtr]),
    ("set_instance", None, [GValuePtr, gpointer]),
    ("fits_pointer", gboolean, [GValuePtr]),
    ("peek_pointer", gpointer, [GValuePtr]),
    ("type_compatible", gboolean, [GType, GType]),
    ("type_transformable", gboolean, [GType, GType]),
    ("transform", gboolean, [GValuePtr, GValuePtr]),
    ("register_transform_func", None, [GType, GType, GValueTransform]),
    ("set_string", None, [GValuePtr, gchar_p]),
    ("set_boxed", None, [GValuePtr, gpointer]),
    ("set_pointer", None, [GValuePtr, gpointer]),
    ("set_object", None, [GValuePtr, gpointer]),
    ("set_boolean", None, [GValuePtr, gboolean]),
    ("set_char", None, [GValuePtr, gchar]),
    ("set_uchar", None, [GValuePtr, guchar]),
    ("set_int", None, [GValuePtr, gint]),
    ("set_uint", None, [GValuePtr, guint]),
    ("set_long", None, [GValuePtr, glong]),
    ("set_ulong", None, [GValuePtr, gulong]),
    ("set_int64", None, [GValuePtr, gint64]),
    ("set_uint64", None, [GValuePtr, guint64]),
    ("set_float", None, [GValuePtr, gfloat]),
    ("set_double", None, [GValuePtr, gdouble]),
    ("set_enum", None, [GValuePtr, gint]),
    ("set_flags", None, [GValuePtr, guint]),
    ("get_string", gchar_p, [GValuePtr]),
    ("get_int", gint, [GValuePtr]),
    ("get_boolean", gboolean, [GValuePtr]),
    ("get_enum", gint, [GValuePtr]),
    ("get_float", gfloat, [GValuePtr]),
    ("get_object", gpointer, [GValuePtr]),
]

wrap_class(_gobject, GValue, GValuePtr, "g_value_", _methods)


set_property = _gobject.g_object_set_property
set_property.argtypes = [gpointer, gchar_p, GValuePtr]
set_property.restype = None

get_property = _gobject.g_object_get_property
get_property.argtypes = [gpointer, gchar_p, GValuePtr]
get_property.restype = None


_methods = [
    ("get_name", gchar_p, [GParamSpecPtr]),
    ("get_nick", gchar_p, [GParamSpecPtr]),
    ("get_blurb", gchar_p, [GParamSpecPtr]),
    ("get_default_value", GValuePtr, [GParamSpecPtr]),
    ("ref", GParamSpecPtr, [GParamSpecPtr]),
    ("unref", None, [GParamSpecPtr]),
]

wrap_class(_gobject, GParamSpec, GParamSpecPtr, "g_param_spec_", _methods)

_methods = [
    ("set_default", None, [GParamSpecPtr, GValuePtr]),
]

wrap_class(_gobject, GParamSpec, GParamSpecPtr, "g_param_value_", _methods)


class GParameter(Structure):
    _fields_ = [
        ("name", gchar_p),
        ("value", GValue),
    ]


class GParameterPtr(POINTER(GParameter)):
    _type_ = GParameter


_methods = [
    ("newv", gpointer, [GType, guint, GParameterPtr]),
    ("new", gpointer, []),
    ("unref", None, [gpointer]),
    ("ref_sink", gpointer, [gpointer]),
    ("ref", gpointer, [gpointer]),
    ("is_floating", gboolean, [gpointer]),
]

for (name, ret, args) in _methods:
    h = getattr(_gobject, "g_object_" + name)
    h.argtypes = args
    h.restype = ret
    globals()[name] = h


_methods = [
    ("find_property", GParamSpecPtr, [GObjectClassPtr, gchar_p]),
]

wrap_class(_gobject, GObjectClass, GObjectClassPtr,
           "g_object_class_", _methods)


def G_TYPE_FROM_INSTANCE(instance):
    return instance.g_class.contents.g_type


class GConnectFlags(Flags):
    CONNECT_AFTER = 1 << 0
    CONNECT_SWAPPED = 1 << 1


class GSignalQuery(Structure):
    _fields_ = [
        ("signal_id", guint),
        ("signal_name", gchar_p),
        ("itype", GType),
        ("signal_flags", GSignalFlags),
        ("return_type", GType),
        ("n_params", guint),
        ("param_types", POINTER(GType)),
    ]


signal_query = _gobject.g_signal_query
signal_query.argtypes = [guint, POINTER(GSignalQuery)]
signal_query.restype = None

signal_list_ids = _gobject.g_signal_list_ids
signal_list_ids.argtypes = [GType, POINTER(guint)]
signal_list_ids.restype = POINTER(guint)

GCallback = CFUNCTYPE(None)
GClosureNotify = CFUNCTYPE(None, gpointer, gpointer)

signal_connect_data = _gobject.g_signal_connect_data
signal_connect_data.argtypes = [gpointer, gchar_p, GCallback, gpointer,
                                GClosureNotify, GConnectFlags]
signal_connect_data.restype = gulong

signal_handler_disconnect = _gobject.g_signal_handler_disconnect
signal_handler_disconnect.argtypes = [gpointer, gulong]
signal_handler_disconnect.restype = None

signal_handler_block = _gobject.g_signal_handler_block
signal_handler_block.argtypes = [gpointer, gulong]
signal_handler_block.restype = None

signal_handler_unblock = _gobject.g_signal_handler_unblock
signal_handler_unblock.argtypes = [gpointer, gulong]
signal_handler_unblock.restype = None

signal_lookup = _gobject.g_signal_lookup
signal_lookup.argtypes = [gchar_p, GType]
signal_lookup.restype = guint

GBoxedCopyFunc = CFUNCTYPE(gpointer, gpointer)
GBoxedFreeFunc = CFUNCTYPE(None, gpointer)
boxed_type_register_static = _gobject.g_boxed_type_register_static
boxed_type_register_static.argtypes = [gchar_p, GBoxedCopyFunc, GBoxedFreeFunc]
boxed_type_register_static.restype = GType

strv_get_type = _gobject.g_strv_get_type
strv_get_type.argtypes = []
signal_lookup.restype = GType

g_type_init()
strv_get_type()

__all__ = ["GType", "g_type_init", "GParamFlags", "GValue", "GValuePtr",
           "GValueTransform", "GSignalFlags", "GTypeFlags", "GParameter",
           "GTypeFundamentalFlags", "GObjectPtr", "GParamSpec",
           "GParamSpecPtr", "GObjectClassPtr", "G_TYPE_FROM_INSTANCE",
           "GParameterPtr", "signal_connect_data", "GCallback",
           "GClosureNotify", "signal_handler_disconnect", "GConnectFlags",
           "signal_handler_unblock", "signal_handler_block", "signal_lookup",
           "GTypeInterface", "GTypeInterfacePtr", "boxed_type_register_static",
           "GBoxedCopyFunc", "GBoxedFreeFunc", "GEnumClassPtr", "GEnumValue",
           "GEnumClass", "GEnumValue", "GFlagsClass", "GFlagsClassPtr",
           "GFlagsValue", "GFlagsValuePtr", "signal_query",
           "GSignalQuery",
           ]
