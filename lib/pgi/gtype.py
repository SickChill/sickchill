# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import byref

from . import _compat
from .clib.gir import GIRepository
from .clib.gobject import GType, GTypeFlags, GTypeFundamentalFlags
from .clib.glib import guint, free
from .util import import_attribute, cached_property


class PGType(object):

    _PYTYPES = {}
    _REGISTRY = {}

    def __init__(self, type_):
        if isinstance(type_, _compat.integer_types):
            type_ = GType(type_)
        elif isinstance(type_, type(self)):
            type_ = type_._type
        elif hasattr(type_, "__gtype__"):
            type_ = type_.__gtype__._type
        self._type = type_

    def __get_gtype_list(self, function):
        length = guint()
        array = getattr(self._type, function)(byref(length))
        # copy the gtypes and free the array so we don't leak
        items = [PGType(GType(v.value)) for v in array[:length.value]]
        free(array)
        return items

    @cached_property
    def children(self):
        return self.__get_gtype_list("children")

    @cached_property
    def interfaces(self):
        return self.__get_gtype_list("interfaces")

    @classmethod
    def from_name(self, name):
        if isinstance(name, _compat.text_type):
            name = name.encode("ascii")
        if not isinstance(name, bytes):
            raise TypeError
        type_ = GType.from_name(name)
        if type_.value == 0:
            # to match gi
            raise RuntimeError("unknown type name")
        return PGType(type_)

    @cached_property
    def fundamental(self):
        return PGType(self._type.fundamental)

    def has_value_table(self):
        return bool(self._type.value_table_peek)

    def is_a(self, type_):
        return self._type.is_a(type_._type)

    def is_abstract(self):
        return self._type.test_flags(GTypeFlags.ABSTRACT)

    def is_classed(self):
        return self._type.test_flags(GTypeFundamentalFlags.CLASSED)

    def is_deep_derivable(self):
        return self._type.test_flags(GTypeFundamentalFlags.DEEP_DERIVABLE)

    def is_derivable(self):
        return self._type.test_flags(GTypeFundamentalFlags.DERIVABLE)

    def is_instantiatable(self):
        return self._type.test_flags(GTypeFundamentalFlags.INSTANTIATABLE)

    def is_interface(self):
        return self.fundamental._type.value == (2 << 2)

    def is_value_abstract(self):
        return self._type.test_flags(GTypeFlags.VALUE_ABSTRACT)

    def is_value_type(self):
        return self._type.check_is_value_type

    @cached_property
    def parent(self):
        return PGType(self._type.parent)

    @cached_property
    def name(self):
        return self._type.name or "invalid"

    @cached_property
    def depth(self):
        return self._type.depth

    @cached_property
    def pytype(self):
        type_ = self._type
        if type_.value == 0:
            return None

        repo = GIRepository.get_default()
        base_info = repo.find_by_gtype(type_)
        if not base_info:
            # look if it's a basic type
            name = type_.name
            if name in self._PYTYPES:
                return self._PYTYPES[name]

            if name in self._REGISTRY:
                return self._REGISTRY[name]

            from pgi.obj import new_class_from_gtype
            cls = new_class_from_gtype(self)
            self._REGISTRY[name] = cls
            return cls
        name = base_info.name
        namespace = base_info.namespace

        return import_attribute(namespace, name)

    def __hash__(self):
        return hash(self._type.value)

    def __eq__(self, other):
        try:
            return self._type.value == other._type.value
        except AttributeError:
            return False

    def __neq__(self, other):
        return not self == other

    def __cmp__(self, other):
        try:
            return cmp(self._type.value, other._type.value)
        except AttributeError:
            return 1

    def __repr__(self):
        return "<GType %s (%d)>" % (self.name, self._type.value)

PGType.__name__ = "GType"
PGType.__module__ = "GObject"

PGType._PYTYPES = {
    "gchararray": str,
    "gboolean": bool,
    "gint": int,
    "guint": int,
    "guint64": int,
    "gfloat": float,
    "gdouble": float,
    "GStrv": [str],
    "gpointer": int,  # ?
    "gulong": int,
    "gint64": int,
    "GType": PGType,
}
