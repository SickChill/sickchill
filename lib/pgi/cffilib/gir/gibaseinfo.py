# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .. import _create_enum_class

from ._ffi import ffi, lib
from .._utils import string_decode
from .gitypelib import GITypelib


GIInfoType = _create_enum_class(ffi, "GIInfoType", "GI_INFO_TYPE_")


def _g_info_type_to_string(self):
    res = lib.g_info_type_to_string(self)
    return string_decode(ffi, res)

GIInfoType.string = property(_g_info_type_to_string)


class GIBaseInfo(object):
    __types = {}

    def __init__(self, ptr):
        self._ptr = ptr

        if ptr:
            self._gc = ffi.gc(ptr, lib.g_base_info_unref)

    @classmethod
    def _register(cls, info_type):
        def wrap(reg_cls):
            cls.__types[info_type] = reg_cls
            return reg_cls
        return wrap

    @classmethod
    def _get_type(cls, ptr):
        """Get the subtype class for a pointer"""

        # fall back to the base class if unknown
        return cls.__types.get(lib.g_base_info_get_type(ptr), cls)

    def ref(self):
        lib.g_base_info_ref(self._ptr)

    def unref(self):
        lib.g_base_info_unref(self._ptr)

    @property
    def type(self):
        assert self._ptr, type(self)
        return GIInfoType(lib.g_base_info_get_type(self._ptr))

    @property
    def name(self):
        res = lib.g_base_info_get_name(self._ptr)
        return string_decode(ffi, res)

    @property
    def namespace(self):
        res = lib.g_base_info_get_namespace(self._ptr)
        return string_decode(ffi, res)

    @property
    def is_deprecated(self):
        return lib.g_base_info_is_deprecated(self._ptr)

    def get_attribute(self, name):
        res = lib.g_base_info_get_attribute(self._ptr, name)
        if res:
            return ffi.string(res)

    def iterate_attributes(self):
        it = ffi.new("GIAttributeIter*")
        name = ffi.new("char**")
        value = ffi.new("char**")
        while lib.g_base_info_iterate_attributes(self._ptr, it, name, value):
            yield (ffi.string(name[0]), ffi.string(value[0]))

    def get_container(self):
        res = lib.g_base_info_get_container(self._ptr)
        if res:
            type_ = self._get_type(res)
            inst = type_(res)
            inst.ref()
            return inst

    def get_typelib(self):
        return GITypelib(lib.g_base_info_get_typelib(self._ptr))

    def equal(self, other):
        return bool(lib.g_base_info_equal(self._ptr, other._ptr))

    def __eq__(self, other):
        if not isinstance(other, GIBaseInfo):
            return False
        if not self and not other:
            return True
        elif not self or not other:
            return False
        return self.equal(other)

    def __neq__(self, other):
        return not self.equal(other)

    def __repr__(self):
        return "<%s namespace=%r name=%r>" % (
            type(self).__name__, self.namespace, self.name)
