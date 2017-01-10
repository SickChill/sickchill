# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import POINTER, c_char_p, cast, c_void_p, byref, Structure

from ..glib import gchar_p, Enum, gboolean, gpointer
from .._utils import wrap_class, find_library, _BaseFinalizer
from .gitypelib import GITypelib

_gir = find_library("girepository-1.0")


class GIInfoType(Enum):
    (INVALID, FUNCTION, CALLBACK, STRUCT, BOXED, ENUM, FLAGS, OBJECT,
     INTERFACE, CONSTANT, INVALID_0, UNION, VALUE, SIGNAL, VFUNC, PROPERTY,
     FIELD, ARG, TYPE, UNRESOLVED) = range(20)

_methods = [
    ("to_string", gchar_p, [GIInfoType]),
]

wrap_class(_gir, GIInfoType, GIInfoType, "g_info_type_", _methods)


class GOptionGroup(Structure):
    pass


class GIAttributeIter(Structure):
    _fields_ = [
        ("data", gpointer),
        ("data2", gpointer),
        ("data3", gpointer),
        ("data4", gpointer),
    ]


class _UnrefFinalizer(_BaseFinalizer):

    def destructor(self, deadweakproxy, ptr):
        ptr.unref()


class GIBaseInfo(c_void_p):
    __types = {}
    __owns = False

    @classmethod
    def _register(cls, info_type):
        """A class decorator to register sub types of GIBaseInfo"""

        def wrap(reg_cls):
            cls.__types[info_type] = reg_cls
            return reg_cls
        return wrap

    def _take_ownership(self):
        """Make the Python instance take ownership of the GIBaseInfo. i.e.
        unref if the python instance gets gc'ed.
        """

        if self:
            ptr = cast(self.value, GIBaseInfo)
            _UnrefFinalizer.track(self, ptr)
            self.__owns = True

    @classmethod
    def _cast(cls, base_info, take_ownership=True):
        """Casts a GIBaseInfo instance to the right sub type.

        The original GIBaseInfo can't have ownership.
        Will take ownership.
        """

        type_value = base_info.type.value
        try:
            new_obj = cast(base_info, cls.__types[type_value])
        except KeyError:
            new_obj = base_info

        if take_ownership:
            assert not base_info.__owns
            new_obj._take_ownership()

        return new_obj

    def _get_repr(self):
        values = {}
        values["info_type"] = repr(self.type)
        real_type = cast(self, GIBaseInfo).type.value
        if real_type != GIInfoType.TYPE and self.name:
            values["name"] = repr(self.name)
        values["namespace"] = repr(self.namespace)
        values["deprecated"] = repr(self.is_deprecated)
        container = self.get_container()
        if container and container.type.value != GIInfoType.TYPE:
            values["container"] = repr(container.name)

        return values

    def get_container(self):
        res = self._get_container()
        if res:
            return self._cast(res, take_ownership=False)

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
        l = ", ".join(("%s=%s" % v for v in sorted(self._get_repr().items())))
        return "<%s %s>" % (type(self).__name__, l)

    def iterate_attributes(self):
        name = c_char_p()
        value = c_char_p()
        it = GIAttributeIter()

        while self._iterate_attributes(byref(it), byref(name), byref(value)):
            yield (name.value, value.value)


_methods = [
    ("ref", GIBaseInfo, [GIBaseInfo], False),
    ("unref", None, [GIBaseInfo]),
    ("get_type", GIInfoType, [GIBaseInfo]),
    ("get_name", gchar_p, [GIBaseInfo]),
    ("get_namespace", gchar_p, [GIBaseInfo]),
    ("is_deprecated", gboolean, [GIBaseInfo]),
    ("get_attribute", gchar_p, [GIBaseInfo, gchar_p]),
    ("_iterate_attributes", gboolean, [GIBaseInfo, POINTER(GIAttributeIter),
                                       POINTER(c_char_p), POINTER(c_char_p)]),
    ("_get_container", GIBaseInfo, [GIBaseInfo]),
    ("get_typelib", GITypelib, [GIBaseInfo]),
    ("equal", gboolean, [GIBaseInfo, GIBaseInfo]),
]

wrap_class(_gir, None, GIBaseInfo, "g_base_info_", _methods)

__all__ = ["GIInfoType", "GIBaseInfo", "GIAttributeIter"]
