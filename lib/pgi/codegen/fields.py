# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from pgi.clib.gir import GIInfoType, GITypeTag
from pgi.gtype import PGType
from pgi.util import import_attribute
from pgi.gerror import PGError


class Field(object):
    TAG = None
    py_type = None

    def __init__(self, info, type, backend):
        self.backend = backend
        self.info = info
        self.type = type

    @classmethod
    def get_class(cls, type_):
        return cls

    def setup(self):
        pass

    def get(self, name):
        raise NotImplementedError("no getter implemented")

    def set(self, name, value_name):
        raise NotImplementedError("no setter implemented")

    def get_param_type(self, index):
        """Returns a ReturnValue instance for param type 'index'"""

        assert index in (0, 1)

        type_info = self.type.get_param_type(index)
        type_cls = get_field_class(type_info)
        instance = type_cls(self.backend, type_info, None)
        instance.setup()
        return instance


class InterfaceField(Field):
    TAG = GITypeTag.INTERFACE
    py_type = object

    def setup(self):
        iface = self.type.get_interface()
        try:
            self.py_type = import_attribute(iface.namespace, iface.name)
        except ImportError:
            # fall back to object
            pass

    def get(self, name):
        var = self.backend.get_type(self.type)
        iface = self.type.get_interface()
        iface_type = iface.type.value

        if iface_type == GIInfoType.ENUM:
            out = var.unpack_out(name)
            return var.block, out
        elif iface_type == GIInfoType.STRUCT:
            out = var.unpack_out(name)
            return var.block, out
        elif iface_type == GIInfoType.OBJECT:
            out = var.unpack_out(name)
            return var.block, out
        elif iface_type == GIInfoType.FLAGS:
            out = var.unpack_out(name)
            return var.block, out

        raise NotImplementedError(
            "interface type not supported: %r" % iface.type)


class ErrorField(Field):
    TAG = GITypeTag.ERROR
    py_type = PGError


class TypeField(Field):
    TAG = GITypeTag.GTYPE
    py_type = PGType

    def get(self, name):
        var = self.backend.get_type(self.type)
        out = var.unpack_out(name)
        return var.block, out


class GHashField(Field):
    TAG = GITypeTag.GHASH
    py_type = dict

    def setup(self):
        self.py_type = {
            self.get_param_type(0).py_type: self.get_param_type(1).py_type}


class BasicField(Field):

    def get(self, name):
        var = self.backend.get_type(self.type)
        out = var.unpack_out(name)
        return var.block, out

    def set(self, name, value_name):
        var = self.backend.get_type(self.type)
        out = var.pack_out(value_name)
        return var.block, out


class DoubleField(BasicField):
    TAG = GITypeTag.DOUBLE
    py_type = float


class UInt32Field(BasicField):
    TAG = GITypeTag.UINT32
    py_type = int


class UInt8Field(BasicField):
    TAG = GITypeTag.UINT8
    py_type = int


class Int32Field(BasicField):
    TAG = GITypeTag.INT32
    py_type = int


class Int64Field(BasicField):
    TAG = GITypeTag.INT64
    py_type = int


class UInt64Field(BasicField):
    TAG = GITypeTag.UINT64
    py_type = int


class UInt16Field(BasicField):
    TAG = GITypeTag.UINT16
    py_type = int


class Int8Field(BasicField):
    TAG = GITypeTag.INT8
    py_type = int


class Int16Field(BasicField):
    TAG = GITypeTag.INT16
    py_type = int


class FloatField(BasicField):
    TAG = GITypeTag.FLOAT
    py_type = float


class UniCharField(BasicField):
    TAG = GITypeTag.UNICHAR
    py_type = str


class BooleanField(BasicField):
    TAG = GITypeTag.BOOLEAN
    py_type = bool


class ArrayField(Field):
    TAG = GITypeTag.ARRAY
    py_type = list

    def setup(self):
        elm_type = self.get_param_type(0)
        if isinstance(elm_type, UInt8Field):
            self.py_type = "bytes"
        else:
            self.py_type = [elm_type.py_type]

    def get(self, name):
        var = self.backend.get_type(self.type)
        out = var.unpack(name, None)
        return var.block, out

    def set(self, name, value_name):
        raise NotImplementedError("Array setters are not implemented")


class Utf8Field(BasicField):
    TAG = GITypeTag.UTF8
    py_type = str


class VoidField(BasicField):
    TAG = GITypeTag.VOID
    py_type = object


class GSListField(Field):
    TAG = GITypeTag.GSLIST
    py_type = list

    def setup(self):
        self.py_type = [self.get_param_type(0).py_type]


class GListField(Field):
    TAG = GITypeTag.GLIST
    py_type = list

    def setup(self):
        self.py_type = [self.get_param_type(0).py_type]


_classes = {}


def _find_fields():
    global _classes
    cls = [a for a in globals().values() if isinstance(a, type)]
    args = [a for a in cls if issubclass(a, Field) and a is not Field]
    _classes = dict(((a.TAG, a) for a in args))
_find_fields()


def get_field_class(arg_type):
    global _classes
    tag_value = arg_type.tag.value
    try:
        cls = _classes[tag_value]
    except KeyError:
        raise NotImplementedError("%r not supported" % arg_type.tag)
    else:
        return cls.get_class(arg_type)
