# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
from contextlib import contextmanager

from .. import _compat
from ._cdef import GLIB_CDEF

import cffi


ffi = cffi.FFI()
ffi.cdef(GLIB_CDEF)
if sys.platform == 'win32':
    lib = ffi.dlopen("libglib-2.0-0.dll")
else:
    lib = ffi.dlopen("libglib-2.0.so.0")


class GQuark(object):

    def __init__(self, quark):
        self._ptr = quark

    @classmethod
    def from_string(cls, string):
        return GQuark(lib.g_quark_from_string(string))

    def to_string(self):
        return ffi.string(lib.g_quark_to_string(self._ptr))

    def __repr__(self):
        return "<%s id='%d' string=%r>" % (
            type(self).__name__, self._ptr, self.to_string())

    def __int__(self):
        return self._ptr


class GErrorError(Exception):
    def __init__(self, gerror):
        super(GErrorError, self).__init__()
        self.message = gerror.message
        if _compat.PY3 and self.message is not None:
            self.message = self.message.decode("utf-8")
        self.domain = gerror.domain
        self.code = gerror.code

    def __str__(self):
        return self.message or ""


@contextmanager
def gerror(type_=GErrorError):
    error = ffi.new("GError**")
    yield error
    gerror = GError(error[0])
    if gerror:
        exc = type_(gerror)
        gerror.free()
        raise exc


@_compat.implements_bool
class GError(object):
    def __init__(self, gerror):
        self._ptr = gerror

    def free(self):
        lib.g_error_free(self._ptr)

    @classmethod
    def new(cls, domain, code, format):
        return GError(lib.g_error_new(domain, int(code), format))

    def copy(self):
        return GError(lib.g_error_copy(self._ptr))

    @property
    def domain(self):
        return GQuark(self._ptr.domain)

    @property
    def code(self):
        return self._ptr.code

    @property
    def message(self):
        return ffi.string(self._ptr.message)

    def __bool__(self):
        return bool(self._ptr)

    def __repr__(self):
        return "<%s domain=%r code='%d', message=%r>" % (
            type(self).__name__, self.domain, self.code, self.message)


class GMappedFile(object):
    def __init__(self, mapped_file):
        self._ptr = mapped_file

    @classmethod
    def new(cls, filename, writeable):
        error = ffi.new("GError**")
        res = lib.g_mapped_file_new(filename, writeable, error)
        gerror = GError(error[0])
        if gerror:
            exc = GErrorError(gerror)
            gerror.free()
            raise exc
        return GMappedFile(res)

    def ref(self):
        lib.g_mapped_file_ref(self._ptr)

    def unref(self):
        lib.g_mapped_file_unref(self._ptr)

    def get_length(self):
        return lib.g_mapped_file_get_length(self._ptr)

    def get_contents(self):
        res = lib.g_mapped_file_get_contents(self._ptr)
        if res:
            return ffi.string(res)
        return


class GOptionGroup(object):
    def __init__(self, group):
        self._ptr = group

    def free(self):
        lib.g_option_group_free(self._ptr)


class GSList(object):
    def __init__(self, l):
        self._ptr = l

    @classmethod
    def alloc(cls):
        return GSList(lib.g_slist_alloc())

    @property
    def data(self):
        return self._ptr.data

    @property
    def next(self):
        n = self._ptr.next
        if n:
            return GSList(n)
        return

    def append(self, data):
        return GSList(lib.g_slist_append(self._ptr, data))

    def free(self):
        lib.g_slist_free(self._ptr)

    def foreach(self, func, userdata):
        ffifunc = ffi.callback("GFunc", func)
        lib.g_slist_foreach(self._ptr, ffifunc, userdata)

    def __repr__(self):
        return "<%s data=%r, next=%r>" % (
            type(self).__name__, self.data, self.next)


class GList(object):
    def __init__(self, l):
        self.ptr = l

    @property
    def data(self):
        return self.ptr.data

    @property
    def next(self):
        n = self.ptr.next
        if n:
            return GList(n)
        return

    @property
    def prev(self):
        n = self.ptr.prev
        if n:
            return GList(n)
        return

    def free(self):
        lib.g_slist_free(self.ptr)

    def __repr__(self):
        return "<%s data=%r, next=%r>" % (
            type(self).__name__, self.data, self.next)


def malloc0(n_bytes):
    return lib.g_malloc0(n_bytes)


def free(mem):
    return lib.g_free(mem)


def try_malloc0(n_bytes):
    return lib.g_try_malloc0(n_bytes)


def strdup(string):
    return lib.g_strdup(string)


def memdup(mem, size):
    return lib.g_memdup(mem, size)


def unpack_glist(glist_ptr, cffi_type, transfer_full=True):
    """Takes a glist ptr, copies the values casted to type_ in to a list
    and frees all items and the list.

    If an item is returned all yielded before are invalid.
    """

    current = glist_ptr
    while current:
        yield ffi.cast(cffi_type, current.data)
        if transfer_full:
            free(current.data)
        current = current.next
    if transfer_full:
        lib.g_list_free(glist_ptr)


def unpack_zeroterm_array(ptr):
    """Converts a zero terminated array to a list and frees each element
    and the list itself.

    If an item is returned all yielded before are invalid.
    """

    assert ptr

    index = 0
    current = ptr[index]
    while current:
        yield current
        free(ffi.cast("gpointer", current))
        index += 1
        current = ptr[index]
    free(ffi.cast("gpointer", ptr))
