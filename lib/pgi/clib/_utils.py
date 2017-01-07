# Copyright 2012,2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import sys
from weakref import proxy
from ctypes import cdll, c_void_p, c_size_t, c_char_p

from ._compat import PY3


class _BaseFinalizer(object):

    # Set used to keep the proxy around.
    # Deletion automatically removes proxies from the set.
    _objects = set()

    @classmethod
    def track(cls, obj, ptr):
        """
        Track an object which needs destruction when it is garbage collected.
        """
        cls._objects.add(cls(obj, ptr))

    def __init__(self, obj, ptr):
        self.obj = proxy(obj, self.delete)
        self.ptr = ptr

    def delete(self, deadweakproxy):
        type(self)._objects.remove(self)
        self.destructor(deadweakproxy, self.ptr)


# decode a path from glib
if os.name == "nt":
    def fsdecode(path):
        return path.decode("utf-8")
elif PY3:
    _FSENC = sys.getfilesystemencoding()

    def fsdecode(path):
        return path.decode(_FSENC, "surrogateescape")
else:
    def fsdecode(path):
        return path


if os.name == "nt":
    _so_mapping = {
        "glib-2.0": "libglib-2.0-0.dll",
        "gobject-2.0": "libgobject-2.0-0.dll",
        "girepository-1.0": "libgirepository-1.0-1.dll",
    }
elif os.uname()[0] == "Darwin":
    _so_mapping = {
        "glib-2.0": "libglib-2.0.0.dylib",
        "gobject-2.0": "libgobject-2.0.0.dylib",
        "girepository-1.0": "libgirepository-1.0.1.dylib",
    }
else:
    _so_mapping = {
        "glib-2.0": "libglib-2.0.so.0",
        "gobject-2.0": "libgobject-2.0.so.0",
        "girepository-1.0": "libgirepository-1.0.so.1",
    }


if os.name == "nt":
    stdlib = memcpy = cdll.msvcrt
elif os.uname()[0] == "Darwin":
    stdlib = getattr(cdll, "libc.dylib")
else:
    stdlib = getattr(cdll, "libc.so.6")

memcpy = stdlib.memcpy
memcpy.argtypes = [c_void_p, c_void_p, c_size_t]
memcpy.restype = c_void_p

_internal = {}


def find_library(name, cached=True, internal=True):
    """
        cached: Return a new instance
        internal: return a shared instance that's not the ctypes cached one
    """

    # a new one
    if not cached:
        return cdll.LoadLibrary(_so_mapping[name])

    # from the shared internal set or a new one
    if internal:
        if name not in _internal:
            _internal[name] = cdll.LoadLibrary(_so_mapping[name])
        return _internal[name]

    # a shared one
    return getattr(cdll, _so_mapping[name])


class _CProperty(object):
    _cache = {}

    def __init__(self, *args):
        self.args = args

    def __get__(self, instance, owner):
        if instance is None:
            return self

        lib, name, symbol, ret, args = self.args
        assert len(args) == 1

        func = self._cache.get((lib, symbol), None)
        if func is None:
            self._cache[(lib, symbol)] = func = getattr(lib, symbol)
            func.argtypes = args
            func.restype = ret

        value = func(instance)

        if PY3 and issubclass(ret, c_char_p) and value is not None:
            value = value.decode("utf-8")

        setattr(instance, name, value)
        return value


class _CMethod(object):
    def __init__(self, *args):
        self.args = args

    def __get__(self, instance, *args):
        owner, name, lib, symbol, ret, args, wrap, unref = self.args
        func = getattr(lib, symbol)
        func.argtypes = args
        func.restype = ret

        def unref_func(*x):
            instance = func(*x)
            instance._take_ownership()
            return instance

        if instance is None:
            instance = owner

        if wrap:
            if unref:
                setattr(owner, name, unref_func)
            else:
                setattr(owner, name, lambda *x: func(*x))
            return getattr(instance, name)
        else:
            # FIXME: handle unref
            assert not unref
            setattr(owner, name, staticmethod(func))
            return getattr(owner, name)


def wrap_class(lib, base, ptr, prefix, methods):
    for method in methods:
        unref = False
        if len(method) == 3:
            name, ret, args = method
        else:
            name, ret, args, unref = method

        # _get_name -> _name
        # _get_version(*args) -> _get_version(*args)

        attr_name = name
        if name[:1] == "_":
            name = name[1:]

        symbol = prefix + name
        is_method = args and args[0] == ptr
        if is_method:
            # Methods that have no arguments and return no pointer type
            # can be getters and the values can be cached. hurray!
            try:
                is_pointer = hasattr(ret, "contents") or ret is c_void_p or \
                    issubclass(ret, c_void_p)
            except TypeError:
                is_pointer = False
            is_void = ret is None
            if len(args) == 1 and not is_void and not is_pointer:
                is_override = attr_name.startswith("_")
                if name.startswith("get_"):
                    attr_name = name.split("_", 1)[-1]
                elif name.startswith("to_"):
                    attr_name = name.split("_", 1)[-1]
                if is_override:
                    attr_name = "_" + attr_name
                # e.g. conflict with ctypes "contents", "value" attribute
                while hasattr(ptr, attr_name):
                    attr_name += "_"
                prop = _CProperty(lib, attr_name, symbol, ret, args)
                setattr(ptr, attr_name, prop)
            else:
                method = _CMethod(
                    ptr, attr_name, lib, symbol, ret, args, True, unref)
                setattr(ptr, attr_name, method)
        else:
            if base is None:
                base = ptr
            static_method = _CMethod(
                base, attr_name, lib, symbol, ret, args, False, unref)
            setattr(base, attr_name, static_method)
