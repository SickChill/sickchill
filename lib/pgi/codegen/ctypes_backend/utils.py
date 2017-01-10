# Copyright 2012-2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import ctypes

from pgi import _compat
from pgi.clib import glib
from pgi.clib.glib import gboolean, gpointer, guint, guint32, GErrorPtr, gint8
from pgi.clib.glib import GSListPtr, GListPtr, gchar_p, gunichar, gdouble
from pgi.clib.glib import gfloat, guint64, gint64, gint32, guint16, gint16
from pgi.clib.glib import guint8
from pgi.clib.gobject import GType
from pgi.clib.gir import GITypeTag, GIInfoType
from pgi.clib.gobject import GCallback

from ..utils import CodeBlock, TypeTagRegistry


class BaseType(object):
    GI_TYPE_TAG = None
    py_type = None

    def __init__(self, gen, type_, desc, may_be_null, may_return_null):
        self._gen = gen
        self.block = CodeBlock()
        self.type = type_
        self.may_be_null = may_be_null
        self.return_null = may_return_null
        self.desc = desc

    def get_type(self, type_, desc="", may_be_null=False,
                 may_return_null=False):
        try:
            cls = registry.get_type(type_)
        except LookupError as e:
            raise NotImplementedError(e)
        else:
            return cls(self._gen, type_, desc, may_be_null, may_return_null)

    def var(self):
        return self._gen.var()

    def __getattribute__(self, name):
        try:
            if _compat.PY3:
                return object.__getattribute__(self, name + "_py3")
            else:
                return object.__getattribute__(self, name + "_py2")
        except AttributeError:
            return object.__getattribute__(self, name)

    @classmethod
    def get_class(cls, type_):
        return cls

    def parse(self, code, **kwargs):
        assert "DESC" not in kwargs
        kwargs["DESC"] = self.desc

        block, var = self._gen.parse(code, **kwargs)
        block.write_into(self.block)
        return var

    def get_reference(self, value):
        return self.parse("""
$ptr = $ctypes.byref($value)
""", value=value)["ptr"]

    def free(self, name):
        self.parse("""
$glib.free($ptr)
""", ptr=name, glib=glib)

    def pack_pointer(self, name):
        """Returns a pointer containing the value.

        This only works for int32/uint32/utf-8..
        """

        return self.parse("""
raise $_.TypeError('Can\\'t convert %(type_name)s to pointer: %%r' %% $in_)
""" % {"type_name": type(self).__name__}, in_=name)["in_"]


registry = TypeTagRegistry()


def register_type(type_tag):
    return registry.register(type_tag)


def typeinfo_to_ctypes(info, return_value=False):
    """Maps a GITypeInfo() to a ctypes type.

    The ctypes types have to be different in the case of return values
    since ctypes does 'auto unboxing' in some cases which gives
    us no chance to free memory if there is a ownership transfer.
    """

    tag = info.tag.value
    ptr = info.is_pointer

    mapping = {
        GITypeTag.BOOLEAN: gboolean,
        GITypeTag.INT8: gint8,
        GITypeTag.UINT8: guint8,
        GITypeTag.INT16: gint16,
        GITypeTag.UINT16: guint16,
        GITypeTag.INT32: gint32,
        GITypeTag.UINT32: guint32,
        GITypeTag.INT64: gint64,
        GITypeTag.UINT64: guint64,
        GITypeTag.FLOAT: gfloat,
        GITypeTag.DOUBLE: gdouble,
        GITypeTag.VOID: None,
        GITypeTag.GTYPE: GType,
        GITypeTag.UNICHAR: gunichar,
    }

    if ptr:
        if tag == GITypeTag.INTERFACE:
            return gpointer
        elif tag in (GITypeTag.UTF8, GITypeTag.FILENAME):
            if return_value:
                # ctypes does auto conversion to str and gives us no chance
                # to free the pointer if transfer=everything
                return gpointer
            else:
                return gchar_p
        elif tag == GITypeTag.ARRAY:
            return gpointer
        elif tag == GITypeTag.ERROR:
            return GErrorPtr
        elif tag == GITypeTag.GLIST:
            return GListPtr
        elif tag == GITypeTag.GSLIST:
            return GSListPtr
        else:
            if tag in mapping:
                return ctypes.POINTER(mapping[tag])
    else:
        if tag == GITypeTag.INTERFACE:
            iface = info.get_interface()
            iface_type = iface.type.value
            if iface_type == GIInfoType.ENUM:
                return guint32
            elif iface_type == GIInfoType.OBJECT:
                return gpointer
            elif iface_type == GIInfoType.STRUCT:
                return gpointer
            elif iface_type == GIInfoType.UNION:
                return gpointer
            elif iface_type == GIInfoType.FLAGS:
                return guint
            elif iface_type == GIInfoType.CALLBACK:
                return GCallback

            raise NotImplementedError(
                "Could not convert interface: %r to ctypes type" % iface.type)
        else:
            if tag in mapping:
                return mapping[tag]

    raise NotImplementedError("Could not convert %r to ctypes type" % info.tag)
