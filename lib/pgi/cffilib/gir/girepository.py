# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .. import glib
from ..glib import unpack_zeroterm_array, unpack_glist
from .. import _create_enum_class
from .._utils import fsdecode, string_decode, string_encode
from .._compat import xrange

from ._ffi import ffi, lib
from .gibaseinfo import GITypelib, GIBaseInfo
from .error import GIError


GIRepositoryLoadFlags = _create_enum_class(ffi, "GIRepositoryLoadFlags",
                                           "G_IREPOSITORY_LOAD_FLAG_")


class GIRepository(object):
    def __init__(self, ptr=ffi.NULL):
        self._ptr = ptr

    @classmethod
    def get_default(cls):
        return GIRepository(lib.g_irepository_get_default())

    @classmethod
    def prepend_search_path(cls, directory):
        lib.g_irepository_prepend_search_path(directory)

    @classmethod
    def prepend_library_path(cls, directory):
        lib.g_irepository_prepend_library_path(directory)

    @classmethod
    def get_search_path(cls):
        res = lib.g_irepository_get_search_path()
        return [fsdecode(ffi, p) for p in unpack_glist(res, "gchar*",
                                                       transfer_full=False)]

    def is_registered(self, namespace, version=None):
        version = string_encode(ffi, version, null=True)
        namespace = string_encode(ffi, namespace)
        return bool(lib.g_irepository_is_registered(self._ptr,
                                                    namespace, version))

    def find_by_name(self, namespace, name):
        namespace = string_encode(ffi, namespace)
        name = string_encode(ffi, name)
        res = lib.g_irepository_find_by_name(self._ptr, namespace, name)
        if res == ffi.NULL:
            return
        type_ = GIBaseInfo._get_type(res)
        return type_(res)

    def require(self, namespace, version, flags):
        version = string_encode(ffi, version, null=True)
        namespace = string_encode(ffi, namespace)
        with glib.gerror(GIError) as error:
            res = lib.g_irepository_require(self._ptr, namespace, version,
                                            flags, error)
        return GITypelib(res)

    def require_private(self, typelib_dir, namespace, version, flags):
        version = string_encode(ffi, version, null=True)
        namespace = string_encode(ffi, namespace)
        with glib.gerror(GIError) as error:
            res = lib.g_irepository_require_private(self._ptr, typelib_dir,
                                                    namespace, version,
                                                    flags, error)
        return GITypelib(res)

    def get_immediate_dependencies(self, namespace):
        try:
            get_deps = lib.g_irepository_get_immediate_dependencies
        except AttributeError:
            get_deps = lib.g_irepository_get_dependencies
        namespace = string_encode(ffi, namespace)
        res = get_deps(self._ptr, namespace)
        return [string_decode(ffi, p) for p in unpack_zeroterm_array(res)]

    def get_loaded_namespaces(self):
        res = lib.g_irepository_get_loaded_namespaces(self._ptr)
        return [string_decode(ffi, p) for p in unpack_zeroterm_array(res)]

    def find_by_gtype(self, gtype):
        res = lib.g_irepository_find_by_gtype(self._ptr, gtype)
        if res:
            type_ = GIBaseInfo._get_type(res)
            return type_(res)

    def get_infos(self, namespace):
        namespace = string_encode(ffi, namespace)
        count = lib.g_irepository_get_n_infos(self._ptr, namespace)
        for index in xrange(count):
            res = lib.g_irepository_get_info(self._ptr, namespace, index)
            type_ = GIBaseInfo._get_type(res)
            yield type_(res)

    def get_n_infos(self, namespace):
        namespace = string_encode(ffi, namespace)
        return lib.g_irepository_get_n_infos(self._ptr, namespace)

    def get_info(self, namespace, index):
        namespace = string_encode(ffi, namespace)
        res = lib.g_irepository_get_info(self._ptr, namespace, index)
        type_ = GIBaseInfo._get_type(res)
        return type_(res)

    def get_typelib_path(self, namespace):
        namespace = string_encode(ffi, namespace)
        res = lib.g_irepository_get_typelib_path(self._ptr, namespace)
        return fsdecode(ffi, res)

    def get_shared_library(self, namespace):
        namespace = string_encode(ffi, namespace)
        res = lib.g_irepository_get_shared_library(self._ptr, namespace)
        return fsdecode(ffi, res)

    def get_version(self, namespace):
        namespace = string_encode(ffi, namespace)
        res = lib.g_irepository_get_version(self._ptr, namespace)
        return string_decode(ffi, res)

    def get_c_prefix(self, namespace):
        namespace = string_encode(ffi, namespace)
        res = lib.g_irepository_get_c_prefix(self._ptr, namespace)
        return string_decode(ffi, res)

    def enumerate_versions(self, namespace):
        namespace = string_encode(ffi, namespace)
        res = lib.g_irepository_enumerate_versions(self._ptr, namespace)
        return [string_decode(ffi, p) for p in unpack_glist(res, "gchar*")]

    def load_typelib(self, typelib, flags):
        with glib.gerror(GIError) as error:
            res = lib.g_irepository_load_typelib(
                self._ptr, typelib._ptr, flags, error)
        return string_decode(ffi, res)
