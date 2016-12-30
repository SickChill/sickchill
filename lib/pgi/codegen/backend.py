# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

_BACKENDS = []
_ACTIVE_BACKENDS = []


def init_backends():
    """Loads all backends"""

    global _BACKENDS, _ACTIVE_BACKENDS

    try:
        from .cffi_backend import CFFIBackend
    except ImportError:
        pass
    else:
        _BACKENDS.append(CFFIBackend)

    from .ctypes_backend import CTypesBackend
    from .null_backend import NullBackend

    _BACKENDS.append(CTypesBackend)
    _ACTIVE_BACKENDS = _BACKENDS[:]
    # null isn't active by default
    _BACKENDS.append(NullBackend)


def list_backends():
    """Returns a list of backends ordered by priority"""

    return _ACTIVE_BACKENDS


def get_backend(name):
    """Returns the backend by name or raises KeyError"""

    for backend in _BACKENDS:
        if backend.NAME == name:
            return backend
    raise KeyError("Backend %r not available" % name)


def set_backend(name=None):
    """Set a prefered ffi backend (cffi, ctypes).

    set_backend() -- default
    set_backend("cffi") -- cffi first, others as fallback
    set_backend("ctypes") -- ctypes first, others as fallback
    """

    possible = list(_BACKENDS)
    if name is None:
        names = []
    else:
        names = name.split(",")

    for name in reversed(names):
        for backend in list(possible):
            if backend.NAME == name:
                possible.remove(backend)
                possible.insert(0, backend)
                break
        else:
            raise LookupError("Unkown backend: %r" % name)

    # only add null as fallback it explicitly specified
    if "null" not in names:
        possible = [b for b in possible if b.NAME != "null"]

    _ACTIVE_BACKENDS[:] = possible


class Backend(object):
    """The backend interface."""

    def get_library(self, namespace):
        raise NotImplementedError

    def get_function(self, lib, symbol, args, ret, method=False, throws=False):
        raise NotImplementedError

    def get_constructor(self, gtype, args):
        raise NotImplementedError

    def get_callback(self, func, args, ret):
        raise NotImplementedError

    def get_type(self, type_, desc="", may_be_null=False,
                 may_return_null=False):
        raise NotImplementedError
