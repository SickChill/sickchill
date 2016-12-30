# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from pgi.clib.gir import GITypeTag, GIDirection, GITransfer, GIInfoType


class CallbackArgument(object):
    TAG = None

    is_aux = False
    py_type = None

    def __init__(self, backend, info, type_, name):
        self.info = info
        self.name = name
        self.backend = backend
        self.type = type_

    @classmethod
    def get_class(cls, type_):
        return cls

    def setup(self):
        pass

    def process(self):
        return None, self.name

    def is_direction_in(self):
        return self.direction in (GIDirection.INOUT, GIDirection.IN)

    def is_direction_out(self):
        return self.direction in (GIDirection.INOUT, GIDirection.OUT)

    def is_direction_inout(self):
        return self.direction == GIDirection.INOUT

    def transfer_nothing(self):
        return self.info.ownership_transfer.value == GITransfer.NOTHING

    def transfer_container(self):
        return self.info.ownership_transfer.value == GITransfer.CONTAINER

    def transfer_everything(self):
        return self.info.ownership_transfer.value == GITransfer.EVERYTHING


class BaseInterfaceArgument(CallbackArgument):
    TAG = GITypeTag.INTERFACE
    py_type = object

    @classmethod
    def get_class(cls, type_):
        iface = type_.get_interface()
        iface_type = iface.type.value

        if iface_type == GIInfoType.STRUCT:
            return StructArgument
        elif iface_type == GIInfoType.OBJECT:
            return ObjectArgument
        elif iface_type == GIInfoType.UNION:
            return UnionArgument
        elif iface_type == GIInfoType.FLAGS:
            return FlagsArgument
        elif iface_type == GIInfoType.ENUM:
            return EnumArgument

        raise NotImplementedError("Unsupported interface type %r" % iface.type)

    def process(self):
        var = self.backend.get_type(self.type)
        out = var.unpack_return(self.name)
        return var.block, out


class FlagsArgument(BaseInterfaceArgument):
    pass


class EnumArgument(BaseInterfaceArgument):
    pass


class ObjectArgument(BaseInterfaceArgument):
    pass


class StructArgument(BaseInterfaceArgument):
    pass


class UnionArgument(BaseInterfaceArgument):
    pass


class Utf8Argument(CallbackArgument):
    TAG = GITypeTag.UTF8
    py_type = str


class BooleanArgument(CallbackArgument):
    TAG = GITypeTag.BOOLEAN
    py_type = bool


class Int64Argument(CallbackArgument):
    TAG = GITypeTag.INT64
    py_type = int


class Int32Argument(CallbackArgument):
    TAG = GITypeTag.INT32
    py_type = int


class UInt64Argument(CallbackArgument):
    TAG = GITypeTag.UINT64
    py_type = int


class VoidArgument(CallbackArgument):
    TAG = GITypeTag.VOID
    py_type = int


_classes = {}


def _find_cbargs():
    global _classes
    for var in globals().values():
        if not isinstance(var, type):
            continue
        if issubclass(var, CallbackArgument) and var is not CallbackArgument:
            _classes[var.TAG] = var
_find_cbargs()


def get_cbarg_class(arg_type):
    global _classes
    tag_value = arg_type.tag.value
    try:
        cls = _classes[tag_value]
    except KeyError:
        raise NotImplementedError(
            "%r signal argument not implemented" % arg_type.tag)
    else:
        return cls.get_class(arg_type)
