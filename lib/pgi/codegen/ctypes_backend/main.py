# Copyright 2012-2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import ctypes
import textwrap

from pgi.clib.gir import GIRepository
from pgi.clib.gobject import GCallback, GType
from pgi.clib import find_library
from pgi import _compat
from pgi.util import load_ctypes_library

from ..backend import Backend
from ..utils import parse_with_objects, VariableFactory

from . import types_basic, types_container, types_interface, types_other
from .utils import registry, typeinfo_to_ctypes


# pyflakes
types_basic
types_container
types_interface
types_other


class CTypesCodeGen(object):
    def __init__(self, var):
        self.var = var

    def parse(self, code, **kwargs):
        assert "_" not in kwargs
        kwargs["_"] = _compat.builtins

        assert "ctypes" not in kwargs
        kwargs["ctypes"] = ctypes

        code = textwrap.dedent(code)
        block, var = parse_with_objects(code, self.var, **kwargs)
        return block, var


class CTypesBackend(Backend):
    NAME = "ctypes"
    _libs = {}

    def __init__(self):
        Backend.__init__(self)
        self._gen = CTypesCodeGen(VariableFactory())

    @property
    def var(self):
        return self._gen.var

    def get_type(self, type_, desc="", may_be_null=False,
                 may_return_null=False):
        try:
            cls = registry.get_type(type_)
        except LookupError as e:
            raise NotImplementedError(e)
        else:
            return cls(self._gen, type_, desc, may_be_null, may_return_null)

    def get_library(self, namespace):
        if namespace not in self._libs:
            paths = GIRepository().get_shared_library(namespace)
            if not paths:
                return
            path = paths.split(",")[0]
            lib = load_ctypes_library(path)
            self._libs[namespace] = lib
        return self._libs[namespace]

    def _get_signature(self, args, ret, method, throws):
        if ret:
            restype = typeinfo_to_ctypes(ret.type, return_value=True)
        else:
            restype = None

        argtypes = []
        if method:
            argtypes.append(ctypes.c_void_p)

        if throws:
            args = args[:-1]

        for arg in args:
            type_ = typeinfo_to_ctypes(arg.type)
            if arg.is_direction_out() and type_ != ctypes.c_void_p:
                type_ = ctypes.POINTER(type_)
            argtypes.append(type_)

        if throws:
            argtypes.append(ctypes.c_void_p)

        return restype, argtypes

    def get_function(self, lib, symbol, args, ret, method=False, throws=False):
        try:
            h = getattr(lib, symbol)
        except AttributeError:
            raise NotImplementedError(
                "Library doesn't provide symbol: %s" % symbol)

        h.restype, h.argtypes = self._get_signature(args, ret, method, throws)

        block, var = self.parse("""
            # args: $args
            # ret: $ret
            """, args=repr([n.__name__ for n in h.argtypes]),
            ret=repr(h.restype))

        return block, h

    def get_callback(self, func, args, ret, is_signal=False):
        if func is None:
            return ctypes.cast(None, GCallback)

        arg_types = [typeinfo_to_ctypes(a.type) for a in args]
        # skip the first arg, we pass the signal's object manually
        if is_signal:
            arg_types.insert(0, ctypes.c_void_p)
        ret_type = typeinfo_to_ctypes(ret.type)
        cb_object_type = ctypes.CFUNCTYPE(ret_type, *arg_types)
        return ctypes.cast(cb_object_type(func), GCallback)

    def get_constructor(self, gtype, args):
        # we need to create a new library, or the argtypes change for all
        # instances
        lib = find_library("gobject-2.0", cached=False)
        h = getattr(lib, "g_object_new")

        arg_types = [GType]
        for arg in args:
            arg_types.append(ctypes.c_char_p)
            arg_types.append(typeinfo_to_ctypes(arg.type))
        arg_types.append(ctypes.c_void_p)
        h.argtypes = arg_types
        h.restype = ctypes.c_void_p

        values = []
        for arg in args:
            values.append("b'%s'" % arg.name)
            values.append(arg.out_var)
        values.append("None")
        type_ = gtype._type

        block, var = self.parse("""
            # args: $args
            # ret: $ret
            $out = $func($type_num, $values)
            """, args=repr([n.__name__ for n in h.argtypes]),
            ret=repr(h.restype), type_num=type_,
            values=", ".join(values), func=h)

        return block, var["out"]

    def parse(self, code, **kwargs):
        return self._gen.parse(code, **kwargs)

    def cast_pointer(self, name, type_):
        block, var = self.parse("""
            $value = $ctypes.cast($value, $ctypes.POINTER($type))
            """, value=name, type=typeinfo_to_ctypes(type_))

        return block, name

    def deref_pointer(self, name):
        block, var = self.parse("""
            $value = $value.contents
            """, value=name)

        return block, var["value"]

    def assign_pointer(self, ptr, value):
        block, var = self.parse("""
            $ptr[0] = $value
            """, ptr=ptr, value=value)

        return block
