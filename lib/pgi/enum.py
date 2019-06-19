# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
import ctypes

from .clib.gobject import GEnumClassPtr, GFlagsClassPtr, GType
from .clib.glib import gint
from .gtype import PGType
from .util import cached_property, escape_identifier, decode_return, \
    decode_return_list
from .obj import add_method
from ._compat import integer_types


class EnumBase(int):
    """Base type for all enum types

    :param value:
    :type value: :obj:`int`
    """

    _allowed = {}

    def __init__(self, value):
        super(EnumBase, self).__init__()

    def __new__(cls, value):
        if not isinstance(value, integer_types):
            raise TypeError("int expected, got %r instead" % type(value))
        if value > sys.maxsize:
            raise OverflowError
        instance = int.__new__(cls, value)
        if value in cls._allowed:
            return instance
        raise ValueError("invalid enum value: %r", value)

    def __repr__(self):
        return "<enum %s of type %s>" % (self._allowed[self],
                                         self.__class__.__name__)

    __str__ = __repr__


EnumBase.__name__ = "Enum"
EnumBase.__module__ = "GLib"


class GEnumBase(EnumBase):
    """Base type for all enum types with a GType

    :param value:
    :type value: :obj:`int`
    """

    __gtype__ = PGType.from_name("GEnum")

    def __get_enum_value(self):
        gtype = self.__gtype__._type
        klass = ctypes.cast(gtype.class_ref(), GEnumClassPtr)
        return klass.get_value(self).contents

    @cached_property
    @decode_return()
    def value_nick(self):
        enum_value = self.__get_enum_value()
        return enum_value.value_nick

    @cached_property
    @decode_return()
    def value_name(self):
        enum_value = self.__get_enum_value()
        return enum_value.value_name


GEnumBase.__name__ = "GEnum"
GEnumBase.__module__ = "GObject"


class FlagsBase(int):
    """Base type for all flags types

    :param value:
    :type value: :obj:`int`
    """

    _flags = []

    def __init__(self, value):
        super(FlagsBase, self).__init__()

    def __new__(cls, value):
        if not isinstance(value, integer_types):
            raise TypeError("int expected, got %r instead" % type(value))
        if value > sys.maxsize:
            raise OverflowError
        return int.__new__(cls, value)

    def __repr__(self):
        names = []
        for (num, vname) in self._flags:
            if not self and not num:
                names.append(vname)
                break
            if self & num:
                names.append(vname)

        names = " | ".join(names) or "0"
        return "<flags %s of type %s>" % (names, self.__class__.__name__)

    __str__ = __repr__

    def __or__(self, other):
        return type(self)(int(self) | other)

    def __and__(self, other):
        return type(self)(int(self) & other)


FlagsBase.__name__ = "Flags"
FlagsBase.__module__ = "GLib"


class GFlagsBase(FlagsBase):
    """Base type for all flags types with a GType

    :param value:
    :type value: :obj:`int`
    """

    __gtype__ = PGType.from_name("GFlags")

    def __get_flags_value(self, value):
        gtype = self.__gtype__._type
        klass = ctypes.cast(gtype.class_ref(), GFlagsClassPtr)
        value_ptr = klass.get_first_value(value)
        if not value_ptr:
            return
        return value_ptr.contents

    def __get_flag_values(self):
        values = []
        for (num, vname) in self._flags:
            masked = self & num
            if not masked:
                continue
            value = self.__get_flags_value(masked)
            if value:
                values.append(value)
        return values

    @cached_property
    @decode_return_list()
    def value_nicks(self):
        return [v.value_nick for v in self.__get_flag_values()]

    @property
    def first_value_nick(self):
        return (self.value_nicks and self.value_nicks[0]) or None

    @cached_property
    @decode_return_list()
    def value_names(self):
        return [v.value_name for v in self.__get_flag_values()]

    @property
    def first_value_name(self):
        return (self.value_names and self.value_names[0]) or None

GFlagsBase.__name__ = "GFlags"
GFlagsBase.__module__ = "GObject"


def _get_values(enum):
    values = []

    for value in enum.get_values():
        num = gint(value.value_).value
        vname = value.name.upper()
        values.append((num, vname))

    return values


def FlagsAttribute(info):
    if info.g_type.value != GType.from_name(b"void").value:
        gtype = PGType(info.g_type)
        base = GFlagsBase
    else:
        gtype = None
        base = FlagsBase

    cls = type(info.name, (base,), dict())
    cls.__module__ = info.namespace
    if gtype is not None:
        cls.__gtype__ = gtype

    values = _get_values(info)
    cls._flags = values

    # create instances for all of them and add to the class
    for num, vname in values:
        escaped = escape_identifier(vname)
        obj = cls(num)
        if escaped != vname:
            setattr(cls, escaped, obj)
        setattr(cls, vname, obj)

    return cls


def EnumAttribute(info):

    if info.g_type.value != GType.from_name(b"void").value:
        gtype = PGType(info.g_type)
        base = GEnumBase
    else:
        gtype = None
        base = EnumBase

    cls = type(info.name, (base,), dict())
    cls.__module__ = info.namespace

    values = _get_values(info)
    cls._allowed = dict(values)
    if gtype is not None:
        cls.__gtype__ = gtype

    for method in info.get_methods():
        add_method(method, cls)

    # create instances for all of them and add to the class
    for num, vname in values:
        escaped = escape_identifier(vname)
        obj = cls(num)
        if escaped != vname:
            setattr(cls, escaped, obj)
        setattr(cls, vname, obj)

    return cls
