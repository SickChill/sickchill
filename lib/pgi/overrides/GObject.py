# -*- Mode: Python; py-indent-offset: 4 -*-
# vim: tabstop=4 shiftwidth=4 expandtab
#
# Copyright (C) 2012 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>
# Copyright (C) 2012-2013 Simon Feltman <sfeltman@src.gnome.org>
# Copyright (C) 2012 Bastian Winkler <buz@netbuz.org>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA

import sys
import warnings
from collections import namedtuple

import pgi
from pgi.overrides import get_introspection_module, override, deprecated_attr
from pgi.repository import GLib
from pgi import propertyhelper
from pgi import signalhelper
from pgi import static as _gobject
from pgi.util import PyGIDeprecationWarning


GObjectModule = get_introspection_module('GObject')
__all__ = []


_gobject.GObject = GObjectModule.Object
_gobject.TYPE_INVALID = GObjectModule.type_from_name('invalid')
Object = GObjectModule.Object


# API aliases for backwards compatibility
for name in ['markup_escape_text', 'get_application_name',
             'set_application_name', 'get_prgname', 'set_prgname',
             'main_depth', 'filename_display_basename',
             'filename_display_name', 'filename_from_utf8',
             'uri_list_extract_uris',
             'MainLoop', 'MainContext', 'main_context_default',
             'source_remove', 'Source', 'Idle', 'Timeout', 'PollFD',
             'idle_add', 'timeout_add', 'timeout_add_seconds',
             'io_add_watch', 'child_watch_add', 'get_current_time',
             'spawn_async']:
    globals()[name] = getattr(GLib, name)
    deprecated_attr("GObject", name, "GLib." + name)
    __all__.append(name)

# deprecated constants
for name in ['PRIORITY_DEFAULT', 'PRIORITY_DEFAULT_IDLE', 'PRIORITY_HIGH',
             'PRIORITY_HIGH_IDLE', 'PRIORITY_LOW',
             'IO_IN', 'IO_OUT', 'IO_PRI', 'IO_ERR', 'IO_HUP', 'IO_NVAL',
             'IO_STATUS_ERROR', 'IO_STATUS_NORMAL', 'IO_STATUS_EOF',
             'IO_STATUS_AGAIN', 'IO_FLAG_APPEND', 'IO_FLAG_NONBLOCK',
             'IO_FLAG_IS_READABLE', 'IO_FLAG_IS_WRITEABLE',
             'IO_FLAG_IS_SEEKABLE', 'IO_FLAG_MASK', 'IO_FLAG_GET_MASK',
             'IO_FLAG_SET_MASK',
             'SPAWN_LEAVE_DESCRIPTORS_OPEN', 'SPAWN_DO_NOT_REAP_CHILD',
             'SPAWN_SEARCH_PATH', 'SPAWN_STDOUT_TO_DEV_NULL',
             'SPAWN_STDERR_TO_DEV_NULL', 'SPAWN_CHILD_INHERITS_STDIN',
             'SPAWN_FILE_AND_ARGV_ZERO',
             'OPTION_FLAG_HIDDEN', 'OPTION_FLAG_IN_MAIN', 'OPTION_FLAG_REVERSE',
             'OPTION_FLAG_NO_ARG', 'OPTION_FLAG_FILENAME', 'OPTION_FLAG_OPTIONAL_ARG',
             'OPTION_FLAG_NOALIAS', 'OPTION_ERROR_UNKNOWN_OPTION',
             'OPTION_ERROR_BAD_VALUE', 'OPTION_ERROR_FAILED', 'OPTION_REMAINING',
             'glib_version']:
    with warnings.catch_warnings():
        # TODO: this uses deprecated Glib attributes, silence for now
        warnings.simplefilter('ignore', PyGIDeprecationWarning)
        globals()[name] = getattr(GLib, name)
    deprecated_attr("GObject", name, "GLib." + name)
    __all__.append(name)


for name in ['G_MININT8', 'G_MAXINT8', 'G_MAXUINT8', 'G_MININT16',
             'G_MAXINT16', 'G_MAXUINT16', 'G_MININT32', 'G_MAXINT32',
             'G_MAXUINT32', 'G_MININT64', 'G_MAXINT64', 'G_MAXUINT64']:
    new_name = name.split("_", 1)[-1]
    globals()[name] = getattr(GLib, new_name)
    deprecated_attr("GObject", name, "GLib." + new_name)
    __all__.append(name)

# these are not currently exported in GLib gir, presumably because they are
# platform dependent; so get them from our static bindings
for name in ['G_MINFLOAT', 'G_MAXFLOAT', 'G_MINDOUBLE', 'G_MAXDOUBLE',
             'G_MINSHORT', 'G_MAXSHORT', 'G_MAXUSHORT', 'G_MININT', 'G_MAXINT',
             'G_MAXUINT', 'G_MINLONG', 'G_MAXLONG', 'G_MAXULONG', 'G_MAXSIZE',
             'G_MINSSIZE', 'G_MAXSSIZE', 'G_MINOFFSET', 'G_MAXOFFSET']:
    new_name = name.split("_", 1)[-1]
    globals()[name] = getattr(GLib, new_name)
    deprecated_attr("GObject", name, "GLib." + new_name)
    __all__.append(name)


TYPE_INVALID = GObjectModule.type_from_name('invalid')
TYPE_NONE = GObjectModule.type_from_name('void')
TYPE_INTERFACE = GObjectModule.type_from_name('GInterface')
TYPE_CHAR = GObjectModule.type_from_name('gchar')
TYPE_UCHAR = GObjectModule.type_from_name('guchar')
TYPE_BOOLEAN = GObjectModule.type_from_name('gboolean')
TYPE_INT = GObjectModule.type_from_name('gint')
TYPE_UINT = GObjectModule.type_from_name('guint')
TYPE_LONG = GObjectModule.type_from_name('glong')
TYPE_ULONG = GObjectModule.type_from_name('gulong')
TYPE_INT64 = GObjectModule.type_from_name('gint64')
TYPE_UINT64 = GObjectModule.type_from_name('guint64')
TYPE_ENUM = GObjectModule.type_from_name('GEnum')
TYPE_FLAGS = GObjectModule.type_from_name('GFlags')
TYPE_FLOAT = GObjectModule.type_from_name('gfloat')
TYPE_DOUBLE = GObjectModule.type_from_name('gdouble')
TYPE_STRING = GObjectModule.type_from_name('gchararray')
TYPE_POINTER = GObjectModule.type_from_name('gpointer')
TYPE_BOXED = GObjectModule.type_from_name('GBoxed')
TYPE_PARAM = GObjectModule.type_from_name('GParam')
TYPE_OBJECT = GObjectModule.type_from_name('GObject')
TYPE_PYOBJECT = GObjectModule.type_from_name('PyObject')
TYPE_GTYPE = GObjectModule.type_from_name('GType')
TYPE_STRV = GObjectModule.type_from_name('GStrv')
TYPE_VARIANT = GObjectModule.type_from_name('GVariant')
TYPE_GSTRING = GObjectModule.type_from_name('GString')
TYPE_VALUE = GObjectModule.Value.__gtype__
TYPE_UNICHAR = TYPE_UINT
__all__ += ['TYPE_INVALID', 'TYPE_NONE', 'TYPE_INTERFACE', 'TYPE_CHAR',
            'TYPE_UCHAR', 'TYPE_BOOLEAN', 'TYPE_INT', 'TYPE_UINT', 'TYPE_LONG',
            'TYPE_ULONG', 'TYPE_INT64', 'TYPE_UINT64', 'TYPE_ENUM', 'TYPE_FLAGS',
            'TYPE_FLOAT', 'TYPE_DOUBLE', 'TYPE_STRING', 'TYPE_POINTER',
            'TYPE_BOXED', 'TYPE_PARAM', 'TYPE_OBJECT', 'TYPE_PYOBJECT',
            'TYPE_GTYPE', 'TYPE_STRV', 'TYPE_VARIANT', 'TYPE_GSTRING',
            'TYPE_UNICHAR', 'TYPE_VALUE']


# Deprecated, use GLib directly
for name in ['Pid', 'GError', 'OptionGroup', 'OptionContext']:
    globals()[name] = getattr(GLib, name)
    deprecated_attr("GObject", name, "GLib." + name)
    __all__.append(name)


# Deprecated, use: GObject.ParamFlags.* directly
for name in ['PARAM_CONSTRUCT', 'PARAM_CONSTRUCT_ONLY', 'PARAM_LAX_VALIDATION',
             'PARAM_READABLE', 'PARAM_WRITABLE']:
    new_name = name.split("_", 1)[-1]
    globals()[name] = getattr(GObjectModule.ParamFlags, new_name)
    deprecated_attr("GObject", name, "GObject.ParamFlags." + new_name)
    __all__.append(name)

# PARAM_READWRITE should come from the gi module but cannot due to:
# https://bugzilla.gnome.org/show_bug.cgi?id=687615
PARAM_READWRITE = GObjectModule.ParamFlags.READABLE | \
    GObjectModule.ParamFlags.WRITABLE
__all__.append("PARAM_READWRITE")

# READWRITE is part of ParamFlags since glib 2.42. Only mark PARAM_READWRITE as
# deprecated in case ParamFlags.READWRITE is available. Also include the glib
# version in the warning so it's clear that this needs a newer glib, unlike
# the other ParamFlags related deprecations.
# https://bugzilla.gnome.org/show_bug.cgi?id=726037
if hasattr(GObjectModule.ParamFlags, "READWRITE"):
    deprecated_attr("GObject", "PARAM_READWRITE",
                    "GObject.ParamFlags.READWRITE (glib 2.42+)")


# Deprecated, use: GObject.SignalFlags.* directly
for name in ['SIGNAL_ACTION', 'SIGNAL_DETAILED', 'SIGNAL_NO_HOOKS',
             'SIGNAL_NO_RECURSE', 'SIGNAL_RUN_CLEANUP', 'SIGNAL_RUN_FIRST',
             'SIGNAL_RUN_LAST']:
    new_name = name.split("_", 1)[-1]
    globals()[name] = getattr(GObjectModule.SignalFlags, new_name)
    deprecated_attr("GObject", name, "GObject.SignalFlags." + new_name)
    __all__.append(name)

# Static types
GBoxed = _gobject.GBoxed
GEnum = _gobject.GEnum
GFlags = _gobject.GFlags
GInterface = _gobject.GInterface
GObject = _gobject.GObject
GObjectWeakRef = _gobject.GObjectWeakRef
GParamSpec = _gobject.GParamSpec
GPointer = _gobject.GPointer
GType = _gobject.GType
Warning = _gobject.Warning
__all__ += ['GBoxed', 'GEnum', 'GFlags', 'GInterface', 'GObject',
            'GObjectWeakRef', 'GParamSpec', 'GPointer', 'GType',
            'Warning']


features = _gobject.features
list_properties = _gobject.list_properties
new = _gobject.new
pygobject_version = _gobject.pygobject_version
threads_init = GLib.threads_init
type_register = _gobject.type_register
__all__ += ['features', 'list_properties', 'new',
            'pygobject_version', 'threads_init', 'type_register']

class Value(GObjectModule.Value):
    # pgi doesn't define this, so put it here...
    _free_on_dealloc = False

    def __init__(self, value_type=None, py_value=None):
        GObjectModule.Value.__init__(self)
        if value_type is not None:
            self.init(value_type)
            if py_value is not None:
                self.set_value(py_value)

    def __del__(self):
        if self._free_on_dealloc and self.g_type != TYPE_INVALID:
            self.unset()

        # We must call base class __del__() after unset.
        super(Value, self).__del__()

    def set_boxed(self, boxed):
        # Workaround the introspection marshalers inability to know
        # these methods should be marshaling boxed types. This is because
        # the type information is stored on the GValue.
        _gobject._gvalue_set(self, boxed)

    def get_boxed(self):
        return _gobject._gvalue_get(self)

    def set_value(self, py_value):
        gtype = self.g_type

        if gtype == _gobject.TYPE_INVALID:
            raise TypeError("GObject.Value needs to be initialized first")
        elif gtype == TYPE_BOOLEAN:
            self.set_boolean(py_value)
        elif gtype == TYPE_CHAR:
            self.set_char(py_value)
        elif gtype == TYPE_UCHAR:
            self.set_uchar(py_value)
        elif gtype == TYPE_INT:
            self.set_int(py_value)
        elif gtype == TYPE_UINT:
            self.set_uint(py_value)
        elif gtype == TYPE_LONG:
            self.set_long(py_value)
        elif gtype == TYPE_ULONG:
            self.set_ulong(py_value)
        elif gtype == TYPE_INT64:
            self.set_int64(py_value)
        elif gtype == TYPE_UINT64:
            self.set_uint64(py_value)
        elif gtype == TYPE_FLOAT:
            self.set_float(py_value)
        elif gtype == TYPE_DOUBLE:
            self.set_double(py_value)
        elif gtype == TYPE_STRING:
            if isinstance(py_value, str):
                py_value = str(py_value)
            elif sys.version_info < (3, 0):
                if isinstance(py_value, unicode):
                    py_value = py_value.encode('UTF-8')
                else:
                    raise ValueError("Expected string or unicode but got %s%s" %
                                     (py_value, type(py_value)))
            else:
                raise ValueError("Expected string but got %s%s" %
                                 (py_value, type(py_value)))
            self.set_string(py_value)
        elif gtype == TYPE_PARAM:
            self.set_param(py_value)
        elif gtype.is_a(TYPE_ENUM):
            self.set_enum(py_value)
        elif gtype.is_a(TYPE_FLAGS):
            self.set_flags(py_value)
        elif gtype.is_a(TYPE_BOXED):
            self.set_boxed(py_value)
        elif gtype == TYPE_POINTER:
            self.set_pointer(py_value)
        elif gtype.is_a(TYPE_OBJECT):
            self.set_object(py_value)
        elif gtype == TYPE_UNICHAR:
            self.set_uint(int(py_value))
        # elif gtype == TYPE_OVERRIDE:
        #     pass
        elif gtype == TYPE_GTYPE:
            self.set_gtype(py_value)
        elif gtype == TYPE_VARIANT:
            self.set_variant(py_value)
        elif gtype == TYPE_PYOBJECT:
            self.set_boxed(py_value)
        else:
            raise TypeError("Unknown value type %s" % gtype)

    def get_value(self):
        gtype = self.g_type

        if gtype == TYPE_BOOLEAN:
            return self.get_boolean()
        elif gtype == TYPE_CHAR:
            return self.get_char()
        elif gtype == TYPE_UCHAR:
            return self.get_uchar()
        elif gtype == TYPE_INT:
            return self.get_int()
        elif gtype == TYPE_UINT:
            return self.get_uint()
        elif gtype == TYPE_LONG:
            return self.get_long()
        elif gtype == TYPE_ULONG:
            return self.get_ulong()
        elif gtype == TYPE_INT64:
            return self.get_int64()
        elif gtype == TYPE_UINT64:
            return self.get_uint64()
        elif gtype == TYPE_FLOAT:
            return self.get_float()
        elif gtype == TYPE_DOUBLE:
            return self.get_double()
        elif gtype == TYPE_STRING:
            return self.get_string()
        elif gtype == TYPE_PARAM:
            return self.get_param()
        elif gtype.is_a(TYPE_ENUM):
            return self.get_enum()
        elif gtype.is_a(TYPE_FLAGS):
            return self.get_flags()
        elif gtype.is_a(TYPE_BOXED):
            return self.get_boxed()
        elif gtype == TYPE_POINTER:
            return self.get_pointer()
        elif gtype.is_a(TYPE_OBJECT):
            return self.get_object()
        elif gtype == TYPE_UNICHAR:
            return self.get_uint()
        elif gtype == TYPE_GTYPE:
            return self.get_gtype()
        elif gtype == TYPE_VARIANT:
            return self.get_variant()
        elif gtype == TYPE_PYOBJECT:
            pass
        else:
            return None

    def __repr__(self):
        return '<Value (%s) %s>' % (self.g_type.name, self.get_value())

Value = override(Value)
__all__.append('Value')


def type_from_name(name):
    type_ = GObjectModule.type_from_name(name)
    if type_ == TYPE_INVALID:
        raise RuntimeError('unknown type name: %s' % name)
    return type_

__all__.append('type_from_name')


def type_parent(type_):
    parent = GObjectModule.type_parent(type_)
    if parent == TYPE_INVALID:
        raise RuntimeError('no parent for type')
    return parent

__all__.append('type_parent')


def _validate_type_for_signal_method(type_):
    if hasattr(type_, '__gtype__'):
        type_ = type_.__gtype__
    if not type_.is_instantiatable() and not type_.is_interface():
        raise TypeError('type must be instantiable or an interface, got %s' % type_)


def signal_list_ids(type_):
    _validate_type_for_signal_method(type_)
    return GObjectModule.signal_list_ids(type_)

__all__.append('signal_list_ids')


def signal_list_names(type_):
    """Returns a list of signal names for the given type

    :param type\\_:
    :type type\\_: :obj:`GObject.GType`
    :returns: A list of signal names
    :rtype: :obj:`list`
    """

    ids = signal_list_ids(type_)
    return tuple(GObjectModule.signal_name(i) for i in ids)

__all__.append('signal_list_names')


def signal_lookup(name, type_):
    _validate_type_for_signal_method(type_)
    return GObjectModule.signal_lookup(name, type_)

__all__.append('signal_lookup')


SignalQuery = namedtuple('SignalQuery',
                         ['signal_id',
                          'signal_name',
                          'itype',
                          'signal_flags',
                          'return_type',
                          # n_params',
                          'param_types'])


def signal_query(id_or_name, type_=None):
    if type_ is not None:
        id_or_name = signal_lookup(id_or_name, type_)

    res = GObjectModule.signal_query(id_or_name)
    if res is None:
        return None

    if res.signal_id == 0:
        return None

    # Return a named tuple to allows indexing which is compatible with the
    # static bindings along with field like access of the gi struct.
    # Note however that the n_params was not returned from the static bindings
    # so we must skip over it.
    return SignalQuery(res.signal_id, res.signal_name, res.itype,
                       res.signal_flags, res.return_type,
                       tuple(res.param_types))

__all__.append('signal_query')


class _HandlerBlockManager(object):
    def __init__(self, obj, handler_id):
        self.obj = obj
        self.handler_id = handler_id

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        GObjectModule.signal_handler_unblock(self.obj, self.handler_id)


def signal_handler_block(obj, handler_id):
    """Blocks the signal handler from being invoked until
    handler_unblock() is called.

    :param GObject.Object obj:
        Object instance to block handlers for.
    :param int handler_id:
        Id of signal to block.
    :returns:
        A context manager which optionally can be used to
        automatically unblock the handler:

    .. code-block:: python

        with GObject.signal_handler_block(obj, id):
            pass
    """
    GObjectModule.signal_handler_block(obj, handler_id)
    return _HandlerBlockManager(obj, handler_id)

__all__.append('signal_handler_block')


def signal_parse_name(detailed_signal, itype, force_detail_quark):
    """Parse a detailed signal name into (signal_id, detail).

    :param str detailed_signal:
        Signal name which can include detail.
        For example: "notify:prop_name"
    :returns:
        Tuple of (signal_id, detail)
    :raises ValueError:
        If the given signal is unknown.
    """
    res, signal_id, detail = GObjectModule.signal_parse_name(detailed_signal, itype,
                                                             force_detail_quark)
    if res:
        return signal_id, detail
    else:
        raise ValueError('%s: unknown signal name: %s' % (itype, detailed_signal))

__all__.append('signal_parse_name')


def remove_emission_hook(obj, detailed_signal, hook_id):
    signal_id, detail = signal_parse_name(detailed_signal, obj, True)
    GObjectModule.signal_remove_emission_hook(signal_id, hook_id)

__all__.append('remove_emission_hook')


# GObject accumulators with pure Python implementations
# These return a tuple of (continue_emission, accumulation_result)

def signal_accumulator_first_wins(ihint, return_accu, handler_return, user_data=None):
    # Stop emission but return the result of the last handler
    return (False, handler_return)

__all__.append('signal_accumulator_first_wins')


def signal_accumulator_true_handled(ihint, return_accu, handler_return, user_data=None):
    # Stop emission if the last handler returns True
    return (not handler_return, handler_return)

__all__.append('signal_accumulator_true_handled')


# Statically bound signal functions which need to clobber GI (for now)

add_emission_hook = _gobject.add_emission_hook
signal_new = _gobject.signal_new

__all__ += ['add_emission_hook', 'signal_new']


class _FreezeNotifyManager(object):
    def __init__(self, obj):
        self.obj = obj

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.obj.thaw_notify()


def _signalmethod(func):
    # Function wrapper for signal functions used as instance methods.
    # This is needed when the signal functions come directly from GI.
    # (they are not already wrapped)
    @pgi.overrides.wraps(func)
    def meth(*args, **kwargs):
        return func(*args, **kwargs)
    return meth


GObject = Object
__all__ += ['Object', 'GObject']


class Binding(GObjectModule.Binding):
    def __call__(self):
        warnings.warn('Using parentheses (binding()) to retrieve the Binding object is no '
                      'longer needed because the binding is returned directly from "bind_property.',
                      PyGIDeprecationWarning, stacklevel=2)
        return self

    def unbind(self):
        if hasattr(self, '_unbound'):
            raise ValueError('binding has already been cleared out')
        else:
            setattr(self, '_unbound', True)
            super(Binding, self).unbind()


Binding = override(Binding)
__all__.append('Binding')


Property = propertyhelper.Property
Signal = signalhelper.Signal
SignalOverride = signalhelper.SignalOverride
# Deprecated naming "property" available for backwards compatibility.
# Keep this at the end of the file to avoid clobbering the builtin.
property = Property
deprecated_attr("GObject", "property", "GObject.Property")
__all__ += ['Property', 'Signal', 'SignalOverride', 'property']
