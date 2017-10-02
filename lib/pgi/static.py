# Copyright 2012,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import ctypes

from .gtype import PGType as GType
from .enum import GEnumBase as GEnum, EnumBase as Enum
from .enum import GFlagsBase as GFlags, FlagsBase as Flags
from .gerror import PGError as GError
from .obj import InterfaceBase as GInterface
from .properties import list_properties
from . import version_info as pygobject_version


def _init_glib(glib_module):
    global OptionContext, OptionGroup, spawn_async

    OptionContext = glib_module.OptionContext
    OptionGroup = glib_module.OptionGroup
    spawn_async = glib_module.spawn_async


GType, GEnum, GFlags, GError, GInterface, list_properties, pygobject_version
Flags, Enum

GBoxed = None
GObject = None
GObjectWeakRef = None
GParamSpec = None
GPointer = None
Warning = None
TYPE_INVALID = None
OptionContext = None
OptionGroup = None
spawn_async = None

features = {'generic-c-marshaller': True}


def _gvalue_set(self, boxed):
    # XXX
    return type(self).__mro__[1].set_boxed(self, boxed)


def _gvalue_get(self):
    # XXX
    return type(self).__mro__[1].get_boxed(self)


def type_register(class_):
    """
    :param class_: a Python class that is a descendant of :obj:`GObject.Object`

    The GObject.type_register() function registers the specified Python class
    as a GObject type. `class_` must be a descendant of GObject.Object.
    The function generates a name for the new type.
    """

    raise NotImplementedError


def new(gtype_or_similar, **kwargs):
    """
    :param type: a Python GObject type
    :type type: :obj:`GObject.Object`

    :param kwargs: set of property-value pairs

    :returns: a new object of the specified `type`

    The Gobject.new() function returns a new object of the specified type.
    `type` must specify a type that is a descendant of gobject.GObject.
    GObject properties can set via keyword arguments.
    """

    return GType(gtype_or_similar).pytype(**kwargs)


def _min_value(ctypes_type):
    signed = ctypes_type(-1).value == -1
    if signed:
        return - 2 ** (ctypes.sizeof(ctypes_type) * 8 - 1)
    return 0


def _max_value(ctypes_type):
    signed = ctypes_type(-1).value == -1
    return 2 ** (ctypes.sizeof(ctypes_type) * 8 - signed) - 1


G_MINDOUBLE = 2.2250738585072014e-308
G_MAXDOUBLE = 1.7976931348623157e+308
G_MINFLOAT = 1.1754943508222875e-38
G_MAXFLOAT = 3.4028234663852886e+38
G_MINSHORT = _min_value(ctypes.c_short)
G_MAXSHORT = _max_value(ctypes.c_short)
G_MAXUSHORT = _max_value(ctypes.c_ushort)
G_MININT = _min_value(ctypes.c_int)
G_MAXINT = _max_value(ctypes.c_int)
G_MAXUINT = _max_value(ctypes.c_uint)
G_MINLONG = _min_value(ctypes.c_long)
G_MAXLONG = _max_value(ctypes.c_long)
G_MAXULONG = _max_value(ctypes.c_ulong)
G_MAXSIZE = _max_value(ctypes.c_size_t)
G_MINSSIZE = _min_value(ctypes.c_ssize_t)
G_MAXSSIZE = _max_value(ctypes.c_ssize_t)
G_MINOFFSET = _min_value(ctypes.c_int64)
G_MAXOFFSET = _max_value(ctypes.c_int64)


class Pid(object):

    def __init__(*args, **kwargs):
        raise NotImplementedError


def add_emission_hook(type, name, callback, *user_data):
    """
    :param type: a Python GObject instance or type
    :type type: :obj:`GObject.Object`

    :param name: a signal name
    :type name: :obj:`str`

    :param callback: a function

    :param user_data: zero or more extra arguments that will be passed to callback

    The add_emission_hook() function adds an emission hook for the signal
    specified by name, which will get called for any emission of that signal,
    independent of the instance. This is possible only for signals which don't
    have the :obj:`GObject.SignalFlags.NO_HOOKS` flag set.
    """

    raise NotImplementedError


def signal_new(signal_name, type, flags, return_type, param_types):
    """
    :param signal_name: the name of the signal
    :type signal_name: :obj:`str`

    :param type: a Python GObject instance or type that the signal is associated with
    :type type: :obj:`GObject.Object`

    :param flags: the signal flags
    :type flags: :obj:`GObject.SignalFlags`

    :param return_type: the return type of the signal handler
    :type return_type: :obj:`type`

    :param param_types: the parameter types passed to the signal handler
    :type param_types: [:obj:`type`]

    :returns: a unique integer signal ID
    :rtype: :obj:`int`

    The :obj:`GObject.signal_new`\() function registers a signal with the
    specified `signal_name` for the specified object `type`.

    `return_type` is the type of the return value from a signal handler and may
    be a gobject type, type ID or instance. The `param_types` parameter is a
    list of additional types that are passed to the signal handler. Each
    parameter type may be specified as a gobject type, type ID or instance.
    For example, to add a signal to the :obj:`Gtk.Window` type called "my-signal"
    that calls a handler with a :obj:`Gtk.Button` widget and an integer value and a
    return value that is a boolean, use::

          GObject.signal_new("my_signal", Gtk.Window, GObject.SignalFlags.RUN_LAST, GObject.TYPE_BOOLEAN, (Gtk.Button, GObject.TYPE_INT))

    """

    raise NotImplementedError


def source_new(*args, **kwargs):
    raise NotImplementedError


def source_set_callback(*args, **kwargs):
    raise NotImplementedError


def io_channel_read(*args, **kwargs):
    raise NotImplementedError
