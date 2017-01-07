# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import POINTER, c_char_p, c_void_p

from ..glib import guint, gchar_p, GErrorPtr, gboolean, gint, unpack_glist
from ..glib import GSListPtr, GOptionGroupPtr, GListPtr, gerror
from ..glib import unpack_nullterm_array
from ..gobject import GType
from .gibaseinfo import GIBaseInfo
from .gitypelib import GITypelib
from .error import GIError
from .._utils import find_library, wrap_class, fsdecode
from .._compat import PY3, xrange

_gir = find_library("girepository-1.0")


class GIRepositoryError(guint):
    TYPELIB_NOT_FOUND = 0
    NAMESPACE_MISMATCH = 1
    NAMESPACE_VERSION_CONFLICT = 2
    LIBRARY_NOT_FOUND = 3


class GIRepositoryLoadFlags(guint):
    LAZY = 1


class GIRepository(c_void_p):

    def get_infos(self, namespace):
        if PY3:
            namespace = namespace.encode("ascii")
        for index in xrange(self._get_n_infos(namespace)):
            res = self._get_info(namespace, index)
            yield GIBaseInfo._cast(res)

    def get_info(self, namespace, index):
        if PY3:
            namespace = namespace.encode("ascii")
        res = self._get_info(namespace, index)
        return GIBaseInfo._cast(res)

    def get_n_infos(self, namespace):
        if PY3:
            namespace = namespace.encode("ascii")
        return self._get_n_infos(namespace)

    def find_by_gtype(self, gtype):
        res = self._find_by_gtype(gtype)
        if not res:
            return None
        return GIBaseInfo._cast(res)

    def find_by_name(self, namespace, name):
        if PY3:
            namespace = namespace.encode("ascii")
            name = name.encode("ascii")
        res = self._find_by_name(namespace, name)
        if not res:
            return None
        return GIBaseInfo._cast(res)

    def require(self, namespace, version, flags):
        if PY3:
            namespace = namespace.encode("ascii")
            if version is not None:
                version = version.encode("ascii")
        with gerror(GIError) as error:
            return self._require(namespace, version, flags, error)

    def require_private(self, typelib_dir, namespace, version, flags):
        if PY3:
            namespace = namespace.encode("ascii")
            if version is not None:
                version = version.encode("ascii")
        with gerror(GIError) as error:
            return self._require_private(
                typelib_dir, namespace, version, flags, error)

    def enumerate_versions(self, namespace):
        if PY3:
            namespace = namespace.encode("ascii")
        glist = self._enumerate_versions(namespace)
        res = unpack_glist(glist, c_char_p)
        if PY3:
            res = [b.decode("ascii") for b in res]
        return res

    def get_loaded_namespaces(self):
        res = self._get_loaded_namespaces()
        res = unpack_nullterm_array(res)
        if PY3:
            res = [b.decode("ascii") for b in res]
        return res

    def get_immediate_dependencies(self, namespace):
        try:
            # https://bugzilla.gnome.org/show_bug.cgi?id=743782
            immediate_dependencies = self._get_immediate_dependencies
        except AttributeError:
            immediate_dependencies = self._get_dependencies

        if PY3:
            namespace = namespace.encode("ascii")
        res = immediate_dependencies(namespace)
        if not res:
            return []
        res = unpack_nullterm_array(res)
        if PY3:
            res = [p.decode("ascii") for p in res]
        return res

    def get_search_path(self):
        res = self._get_search_path()
        paths = unpack_glist(res, c_char_p, transfer_full=False)
        return [fsdecode(p) for p in paths]

    def get_shared_library(self, namespace):
        if PY3:
            namespace = namespace.encode("ascii")
            lib = self._get_shared_library(namespace)
            return lib.decode("ascii") if lib else lib
        return self._get_shared_library(namespace)

    def get_typelib_path(self, namespace):
        if PY3:
            namespace = namespace.encode("ascii")
        path = self._get_typelib_path(namespace)
        if path is not None:
            return fsdecode(path)

    def get_version(self, namespace):
        if PY3:
            namespace = namespace.encode("ascii")
            return self._get_version(namespace).decode("ascii")
        return self._get_version(namespace)

    def is_registered(self, namespace, version=None):
        if PY3:
            namespace = namespace.encode("ascii")
            if version is not None:
                version = version.encode("ascii")
        return self._is_registered(namespace, version)

    def get_c_prefix(self, namespace):
        if PY3:
            namespace = namespace.encode("ascii")
        res = self._get_c_prefix(namespace)
        if PY3:
            res = res.decode("ascii")
        return res

    def load_typelib(self, typelib, flags):
        with gerror(GIError) as error:
            res = self._load_typelib(typelib, flags, error)
        if PY3:
            res = res.decode("ascii")
        return res

_methods = [
    ("get_default", GIRepository, []),
    ("_require", GITypelib, [GIRepository, gchar_p, gchar_p,
                            GIRepositoryLoadFlags,
                            POINTER(GErrorPtr)]),
    ("_find_by_name", GIBaseInfo,
     [GIRepository, gchar_p, gchar_p], False),
    ("prepend_search_path", None, [c_char_p]),
    ("prepend_library_path", None, [c_char_p]),
    ("_get_search_path", GSListPtr, []),
    ("_load_typelib", c_char_p,
        [GIRepository, GITypelib, GIRepositoryLoadFlags,
         POINTER(GErrorPtr)]),
    ("_is_registered", gboolean, [GIRepository, gchar_p, gchar_p]),
    ("_require_private",
        GITypelib, [GIRepository, gchar_p, gchar_p, gchar_p,
                    GIRepositoryLoadFlags, POINTER(GErrorPtr)]),
    ("_get_dependencies", POINTER(gchar_p), [GIRepository, gchar_p]),
    ("_get_immediate_dependencies", POINTER(gchar_p), [GIRepository, gchar_p]),
    ("_get_loaded_namespaces", POINTER(gchar_p), [GIRepository]),
    ("_find_by_gtype", GIBaseInfo, [GIRepository, GType], False),
    ("_get_n_infos", gint, [GIRepository, gchar_p]),
    ("_get_info", GIBaseInfo, [GIRepository, gchar_p, gint], False),
    ("_get_typelib_path", gchar_p, [GIRepository, gchar_p]),
    ("_get_shared_library", gchar_p, [GIRepository, gchar_p]),
    ("_get_version", gchar_p, [GIRepository, gchar_p]),
    ("get_option_group", GOptionGroupPtr, [], True),
    ("_get_c_prefix", gchar_p, [GIRepository, gchar_p]),
    ("_enumerate_versions", GListPtr, [GIRepository, gchar_p]),
]

wrap_class(_gir, None, GIRepository, "g_irepository_", _methods)


__all__ = ["GIRepositoryLoadFlags", "GIRepository", "GIRepositoryError"]
