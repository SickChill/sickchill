# Copyright 2012,2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import textwrap
from cffi import FFI

from pgi.clib.gir import GIRepository, GITypeTag, GIInfoType
from .backend import Backend
from .utils import CodeBlock, parse_with_objects, VariableFactory
from .utils import TypeTagRegistry
from .. import _compat


_glib_defs = """
typedef char gchar;
typedef const void * gconstpointer;
typedef double gdouble;
typedef float gfloat;
typedef int gboolean;
typedef int16_t gint16;
typedef int32_t gint32;
typedef int64_t gint64;
typedef int8_t gint8;
typedef int gint;
typedef long glong;
typedef short gshort;
typedef size_t gsize;
typedef uint16_t guint16;
typedef uint32_t guint32;
typedef uint64_t guint64;
typedef uint8_t guint8;
typedef unsigned int guint;
typedef unsigned long gulong;
typedef unsigned short gushort;
typedef intptr_t gpointer;
typedef gulong GType;
"""


def typeinfo_to_cffi(info):
    tag = info.tag.value
    ptr = info.is_pointer

    if not ptr:
        if tag == GITypeTag.UINT32:
            return "guint32"
        elif tag == GITypeTag.INT32:
            return "gint32"
        elif tag == GITypeTag.BOOLEAN:
            return "gboolean"
        elif tag == GITypeTag.VOID:
            return "void"
        elif tag == GITypeTag.GTYPE:
            return "GType"
        elif tag == GITypeTag.INTERFACE:
            iface = info.get_interface()
            iface_type = iface.type.value
            if iface_type == GIInfoType.STRUCT:
                return "gpointer"
            elif iface_type == GIInfoType.ENUM:
                return "guint32"

            raise NotImplementedError(
                "Couldn't convert interface ptr %r to cffi type" % iface.type)
    else:
        if tag == GITypeTag.UTF8 or tag == GITypeTag.FILENAME:
            return "gchar*"
        elif tag == GITypeTag.INTERFACE:
            iface = info.get_interface()
            iface_type = iface.type.value
            if iface_type == GIInfoType.ENUM:
                return "guint32"
            elif iface_type == GIInfoType.OBJECT:
                return "gpointer"
            elif iface_type == GIInfoType.STRUCT:
                return "gpointer"

            raise NotImplementedError(
                "Couldn't convert interface %r to cffi type" % iface.type)

    raise NotImplementedError("Couldn't convert %r to cffi type" % info.tag)


registry = TypeTagRegistry()


def get_type(type_, gen, desc, may_be_null, may_return_null):
    try:
        cls = registry.get_type(type_)
    except LookupError as e:
        raise NotImplementedError(e)

    return cls(gen, type_, desc, may_be_null, may_return_null)


class BaseType(object):
    GI_TYPE_TAG = None
    type = None
    py_type = None

    def __init__(self, gen, type_, desc, may_be_null, may_return_null):
        self._gen = gen
        self.block = CodeBlock()
        self.type = type_
        self.may_be_null = may_be_null
        self.may_return_null = may_return_null
        self.desc = desc

    def get_type(self, type_, may_be_null=False, may_return_null=False):
        return get_type(type_, self._gen, may_be_null, may_return_null)

    def var(self):
        return self._gen.var()

    @classmethod
    def get_class(cls, type_):
        return cls

    def parse(self, code, **kwargs):
        assert "DESC" not in kwargs
        kwargs["DESC"] = self.desc

        code = textwrap.dedent(code)
        block, var = self._gen.parse(code, **kwargs)
        block.write_into(self.block)
        return var

    def get_reference(self, value):
        raise NotImplementedError

    def free(self, name):
        raise NotImplementedError

    def __getattribute__(self, name):
        try:
            if _compat.PY3:
                return object.__getattribute__(self, name + "_py3")
            else:
                return object.__getattribute__(self, name + "_py2")
        except AttributeError:
            return object.__getattribute__(self, name)


class BasicType(BaseType):

    def pack_in(self, value):
        raise NotImplementedError

    def pack_out(self, value):
        raise NotImplementedError

    def unpack_out(self, value):
        raise NotImplementedError

    def unpack_return(self, value):
        raise NotImplementedError

    def new(self):
        raise NotImplementedError


@registry.register(GITypeTag.BOOLEAN)
class Boolean(BasicType):

    def _check(self, name):
        return self.parse("""
            $bool = $_.bool($value)
            """, value=name)["bool"]

    pack_out = _check
    pack_in = _check

    def unpack_return(self, name):
        return self.parse("""
            $bool = $_.bool($value)
            """, value=name)["bool"]

    unpack_out = unpack_return

    def new(self):
        return self.parse("""
            $value = $ffi.cast("gboolean", 0)
            """)["value"]


class BaseInt(BasicType):

    CTYPE = None

    def _check(self, value):
        int_ = self.parse("""
            if not $_.isinstance($value, $basestring):
                $int = $_.int($value)
            else:
                raise $_.TypeError("$DESC: not a number")
            """, value=value, basestring=_compat.string_types)["int"]

        if self.CTYPE.startswith("u"):
            bits = int(self.CTYPE[4:])
            return self.parse("""
                if not 0 <= $int < 2**$bits:
                    raise $_.OverflowError("$DESC: %r not in range" % $int)
                """, int=int_, bits=bits)["int"]
        else:
            bits = int(self.CTYPE[3:])
            return self.parse("""
                if not -2**$bits <= $int < 2**$bits:
                    raise $_.OverflowError("$DESC: %r not in range" % $int)
                """, int=int_, bits=bits - 1)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $value = $ffi.cast("g$ctype", $value)
            """, ctype=self.CTYPE, value=checked)["value"]

    def unpack_return(self, value):
        return value

    def unpack_out(self, value):
        return self.parse("""
            $value = int($value)
            """, value=value)["value"]

    def new(self):
        return self.parse("""
            $value = $ffi.cast("g$ctype", 0)
            """, ctype=self.CTYPE)["value"]


for name in ["Int16", "UInt16", "Int32", "UInt32", "Int64", "UInt64"]:
    cls = type(name, (BaseInt,), {"CTYPE": name.lower()})
    type_tag = getattr(GITypeTag, name.upper())
    registry.register(type_tag)(cls)


@registry.register(GITypeTag.UTF8)
class Utf8(BasicType):

    def _check_py3(self, name):
        if self.may_be_null:
            return self.parse("""
                if $value is not None:
                    if isinstance($value, $_.str):
                        $string = $value.encode("utf-8")
                    else:
                        $string = $value
                else:
                    $string = None
                """, value=name)["string"]

        return self.parse("""
            if isinstance($value, $_.str):
                $string = $value.encode("utf-8")
            elif not isinstance($value, $_.bytes):
                raise TypeError
            else:
                $string = $value
            """, value=name)["string"]

    def _check_py2(self, name):
        if self.may_be_null:
            return self.parse("""
                if $value is not $none:
                    if isinstance($value, $_.unicode):
                        $string = $value.encode("utf-8")
                    elif not isinstance($value, $_.str):
                        raise $_.TypeError("$DESC: %r not a string or None" % $value)
                    else:
                        $string = $value
                else:
                    $string = $none
                """, value=name, none=None)["string"]

        return self.parse("""
            if $_.isinstance($value, $_.unicode):
                $string = $value.encode("utf-8")
            elif not $_.isinstance($value, $_.str):
                raise $_.TypeError("$DESC: %r not a string" % $value)
            else:
                $string = $value
            """, value=name)["string"]

    def pack_in_py2(self, value):
        value = self._check(value)
        return self.parse("""
            if $value:
                $c_value = $value
            else:
                $c_value = $ffi.cast("char*", 0)
            """, value=value)["c_value"]

    def pack_in_py3(self, value):
        value = self._check(value)
        return self.parse("""
            if $value is not None:
                $c_value = $value
            else:
                $c_value = $ffi.cast("char*", 0)
            """, value=value)["c_value"]

    def dup(self, name):
        raise NotImplementedError

    def unpack_out(self, name):
        raise NotImplementedError

    def unpack_return_py2(self, value):
        return self.parse("""
            if $value == $ffi.NULL:
                $value = None
            else:
                $value = $ffi.string($value)
            """, value=value)["value"]

    def unpack_return_py3(self, value):
        return self.parse("""
            if $value == $ffi.NULL:
                $value = None
            else:
                $value = $ffi.string($value).decode("utf-8")
            """, value=value)["value"]

    def new(self):
        raise NotImplementedError


class CFFICodeGen(object):
    def __init__(self, var, ffi):
        self.var = var
        self._ffi = ffi

    def parse(self, code, **kwargs):
        assert "ffi" not in kwargs
        kwargs["ffi"] = self._ffi

        assert "_" not in kwargs
        kwargs["_"] = _compat.builtins

        block, var = parse_with_objects(code, self.var, **kwargs)
        return block, var


class CFFIBackend(Backend):
    NAME = "cffi"

    _libs = {}
    _ffi = FFI()
    _ffi.cdef(_glib_defs)

    def __init__(self):
        Backend.__init__(self)
        self._gen = CFFICodeGen(VariableFactory(), self._ffi)

    @property
    def var(self):
        return self._gen.var

    def get_library(self, namespace):
        if namespace not in self._libs:
            paths = GIRepository().get_shared_library(namespace)
            if not paths:
                raise NotImplementedError("No shared library")
            path = paths.split(",")[0]
            self._libs[namespace] = self._ffi.dlopen(path)
        return self._libs[namespace]

    def get_function(self, lib, symbol, args, ret, method=False, throws=False):
        block = CodeBlock()
        cdef_types = []

        if method:
            cdef_types.append("gpointer")

        for arg in args:
            cdef_types.append(typeinfo_to_cffi(arg.type))

        if ret:
            cffi_ret = typeinfo_to_cffi(ret.type)
        else:
            cffi_ret = "void"

        cdef = "%s %s(%s);" % (cffi_ret, symbol, ", ".join(cdef_types))
        self._ffi.cdef(cdef, override=True)
        block.write_line("# " + cdef)

        try:
            func = getattr(lib, symbol)
        except (KeyError, AttributeError):
            raise NotImplementedError(
                "Library doesn't provide symbol: %s" % symbol)

        return block, func

    def get_type(self, type_, desc="", may_be_null=False,
                 may_return_null=False):
        return get_type(type_, self._gen, desc, may_be_null, may_return_null)

    def parse(self, code, **kwargs):
        return self._gen.parse(code, **kwargs)

    def cast_pointer(self, name, type_):
        block, var = self.parse("""
$value = $ffi.cast("$type*", $value)
""", value=name, type=typeinfo_to_cffi(type_))

        return block, name

    def assign_pointer(self, ptr, value):
        raise NotImplementedError

    def deref_pointer(self, name):
        block, var = self.parse("""
$value = $value[0]
""", value=name)

        return block, var["value"]
