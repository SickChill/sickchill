# Copyright 2012,2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from pgi.clib.gir import GIDirection, GIArrayType, GITypeTag, GIInfoType
from pgi.clib.gir import GITransfer
from pgi.clib.gobject import GCallback
from pgi.gtype import PGType
from pgi.gerror import PGError
from pgi.util import import_attribute
from pgi import _compat


class Argument(object):
    """Base class for argument types

    is_aux   -- if the arg is handled by another arg
    in_var   -- variable name in the function def
    out_var  -- variable name to return
    call_var -- variable name passed to the function
    py_type  -- a python type for docs / possibly annotation
    """

    is_aux = False
    in_var = ""
    call_var = ""
    out_var = ""
    py_type = None
    is_userdata = False
    desc = ""

    def __init__(self, arguments, backend):
        self.args = arguments
        self.backend = backend

    @classmethod
    def get_class(cls, type_):
        return cls

    def setup(self):
        pass

    def pre_call(self):
        pass

    def post_call(self):
        pass

    @property
    def can_unpack_none(self):
        """If we get None if the pointer type is NULL"""

        return False


class ErrorArgument(Argument):

    class FakeType(object):
        class Y(object):
            value = GITypeTag.ERROR
        tag = Y()

    def pre_call(self):
        var = self.backend.get_type(ErrorArgument.FakeType(), may_be_null=True)

        self._error = var.new()
        self.call_var = var.get_reference(self._error)
        return var.block

    def post_call(self):
        var = self.backend.get_type(ErrorArgument.FakeType(), may_be_null=True)

        out = var.unpack(self._error, own=True)
        var.check_raise(out)
        return var.block


class GIArgument(Argument):

    TAG = None
    py_type = None

    def __init__(self, name, arguments, backend, info, type_):
        Argument.__init__(self, arguments, backend)

        self.info = info
        self.name = name
        self.type = type_
        self.call_var = name

        # param type case
        if self.info is not None:
            self.direction = self.info.direction.value
        else:
            self.direction = None

        if self.is_direction_in():
            self.in_var = name

    @property
    def may_be_null(self):
        return self.info.may_be_null

    def get_type(self):
        return self.backend.get_type(
            self.type, desc=self.desc, may_be_null=self.may_be_null)

    def get_param_type(self, index):
        """Returns a ReturnValue instance for param type 'index'"""

        assert index in (0, 1)

        type_info = self.type.get_param_type(index)
        type_cls = get_argument_class(type_info)
        instance = type_cls(None, [], self.backend, None, type_info)
        instance.setup()
        return instance

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

    def is_caller_allocates(self):
        return self.info.is_caller_allocates

    def __repr__(self):
        return "<%s name=%r>" % (self.__class__.__name__, self.name)


class GIErrorArgument(GIArgument):
    TAG = GITypeTag.ERROR
    py_type = PGError

    def pre_call(self):
        var = self.get_type()
        if self.is_direction_out():
            self._error = var.new()
            self.call_var = var.get_reference(self._error)
            return var.block

        # FIXME: in case

    def post_call(self):
        if not self.is_direction_out():
            return

        var = self.get_type()
        get_ownership = self.transfer_everything()
        self.out_var = var.unpack(self._error, get_ownership)

        return var.block

    @property
    def can_unpack_none(self):
        return True


class ArrayArgument(GIArgument):
    TAG = GITypeTag.ARRAY
    py_type = list

    def setup(self):
        elm_type = self.get_param_type(0)
        if isinstance(elm_type, UInt8Argument):
            self.py_type = "bytes"
        else:
            self.py_type = [elm_type.py_type]

    @classmethod
    def get_class(cls, type_):
        array_type = type_.array_type
        typev = array_type.value

        if typev == GIArrayType.C:
            return CArrayArgument
        elif typev == GIArrayType.BYTE_ARRAY:
            return ByteArrayArgument
        elif typev == GIArrayType.ARRAY:
            return GArrayArgument
        elif typev == GIArrayType.PTR_ARRAY:
            return PtrArrayArgument

        raise NotImplementedError("unsupported array type: %r" % array_type)


class GArrayArgument(ArrayArgument):
    pass


class ByteArrayArgument(ArrayArgument):
    pass


class PtrArrayArgument(ArrayArgument):
    pass


class CArrayArgument(ArrayArgument):

    def setup(self):
        super(CArrayArgument, self).setup()

        # mark other arg as aux so we handle it alone
        if self.type.array_length != -1:
            aux = self.args[self.type.array_length]
            aux.is_aux = True
            self._aux = aux

    def pre_call(self):
        var = self.get_type()
        if self.is_direction_inout():
            checked = var.check(self.name)
            if self.type.array_length != -1:
                self._data, self._length = var.pack(checked, self._aux.type)
                self._aux.call_var = var.get_reference(self._length)
            else:
                self._data, length = var.pack(checked, None)
            self.call_var = var.get_reference(self._data)
            return var.block
        elif self.is_direction_in():
            checked = var.check(self.name)
            if self.type.array_length != -1:
                self.call_var, length = var.pack_in(checked, self._aux.type)
                self._aux.call_var = length
            else:
                self.call_var, dummy = var.pack_in(checked, None)
            return var.block
        else:
            if self.type.array_length != -1:
                self._data, self._length = var.new(self._aux.type)
                self._aux.call_var = var.get_reference(self._length)
            else:
                self._data, dummy = var.new(None)
            self.call_var = var.get_reference(self._data)
            return var.block

    def post_call(self):
        if not self.is_direction_out():
            return

        var = self.get_type()
        if self.type.array_length != -1:
            self.out_var = var.unpack(self._data, self._length)
        else:
            self.out_var = var.unpack(self._data, None)
        return var.block


class BaseInterfaceArgument(GIArgument):
    TAG = GITypeTag.INTERFACE
    py_type = object

    def setup(self):
        iface = self.type.get_interface()
        try:
            self.py_type = import_attribute(iface.namespace, iface.name)
        except ImportError:
            # fall back to object
            pass

    @classmethod
    def get_class(cls, type_):
        iface = type_.get_interface()
        iface_type = iface.type.value

        if iface_type == GIInfoType.OBJECT:
            return ObjectArgument
        elif iface_type == GIInfoType.INTERFACE:
            return ObjectArgument
        elif iface_type == GIInfoType.ENUM or iface_type == GIInfoType.FLAGS:
            return EnumFlagsArgument
        elif iface_type == GIInfoType.STRUCT:
            return StructArgument
        elif iface_type == GIInfoType.CALLBACK:
            return CallbackArgument
        elif iface_type == GIInfoType.UNION:
            return UnionArgument

        raise NotImplementedError("Unsupported interface type %r" % iface.type)


class CallbackArgument(BaseInterfaceArgument):
    py_type = type(lambda: None)

    def setup(self):
        super(CallbackArgument, self).setup()

        self._user_data = None
        if self.info.closure != -1:
            self._user_data = self.args[self.info.closure]
            self._user_data.is_userdata = True

        self._destroy = None
        if self.info.destroy != -1:
            self._destroy = self.args[self.info.destroy]
            self._destroy.is_aux = True

    def pre_call(self):
        var = self.get_type()
        self.call_var = var.pack(var.check(self.name))

        if self._destroy:
            var.block.add_dependency("GCallback", GCallback)
            self._destroy.call_var = "GCallback()"

        if self._user_data:
            self._user_data.call_var = "None"

        return var.block


class EnumFlagsArgument(BaseInterfaceArgument):

    def pre_call(self):
        var = self.get_type()

        if self.is_direction_inout():
            self._data = var.pack_out(self.name)
            self.call_var = var.get_reference(self._data)
        elif self.is_direction_in():
            self.call_var = var.pack_in(self.name)
        else:
            self._data = var.new()
            self.call_var = var.get_reference(self._data)

        return var.block

    def post_call(self):
        if not self.is_direction_out():
            return

        var = self.get_type()
        self.out_var = var.unpack_out(self._data)
        return var.block


class StructArgument(BaseInterfaceArgument):

    def pre_call(self):
        var = self.get_type()

        if self.is_direction_inout():
            self._data = var.pack_out(self.name)
            self.call_var = var.get_reference(self._data)
        elif self.is_direction_in():
            self.call_var = var.pack_in(self.name)
        else:
            if self.is_caller_allocates():
                self.call_var = self._data = var.alloc()
            else:
                self._data = var.new()
                self.call_var = var.get_reference(self._data)

        return var.block

    def post_call(self):
        if not self.is_direction_out():
            return

        var = self.get_type()
        self.out_var = var.unpack_out(self._data)
        return var.block

    @property
    def can_unpack_none(self):
        return True


class UnionArgument(BaseInterfaceArgument):

    def pre_call(self):
        var = self.get_type()
        return var.block

    def post_call(self):
        var = self.get_type()
        return var.block


class ObjectArgument(BaseInterfaceArgument):

    def pre_call(self):
        var = self.get_type()

        if self.is_direction_in():
            self._data = var.pack_in(self.name)

            if self.transfer_everything():
                var.ref(self.name)

            if self.is_direction_out():
                self.call_var = var.get_reference(self._data)
            else:
                self.call_var = self._data

            return var.block
        else:
            self._data = var.new()
            self.call_var = var.get_reference(self._data)

            return var.block

    def post_call(self):
        if self.is_direction_out():
            var = self.get_type()
            out = var.unpack_out(self._data)
            if self.transfer_nothing():
                var.ref(out)
            self.out_var = out
            return var.block

    @property
    def can_unpack_none(self):
        return True


class BasicTypeArgument(GIArgument):
    TYPE_NAME = ""

    def pre_call(self):
        var = self.get_type()

        if self.is_direction_inout():
            self._data = var.pack_out(self.name)
            self.call_var = var.get_reference(self._data)
            return var.block
        elif self.is_direction_in():
            self.call_var = var.pack_in(self.name)
            return var.block
        else:
            self._data = var.new()
            self.call_var = var.get_reference(self._data)
            return var.block

    def post_call(self):
        if self.is_direction_out():
            var = self.get_type()
            self.out_var = var.unpack_out(self._data)
            return var.block


class BoolArgument(BasicTypeArgument):
    TAG = GITypeTag.BOOLEAN
    py_type = bool


class Int8Argument(BasicTypeArgument):
    TAG = GITypeTag.INT8
    py_type = int


class UInt8Argument(BasicTypeArgument):
    TAG = GITypeTag.UINT8
    py_type = int


class Int16Argument(BasicTypeArgument):
    TAG = GITypeTag.INT16
    py_type = int


class UInt16Argument(BasicTypeArgument):
    TAG = GITypeTag.UINT16
    py_type = int


class Int32Argument(BasicTypeArgument):
    TAG = GITypeTag.INT32
    py_type = int


class Int64Argument(BasicTypeArgument):
    TAG = GITypeTag.INT64
    py_type = int


class UInt64Argument(BasicTypeArgument):
    TAG = GITypeTag.UINT64
    py_type = int


class UINT32Argument(BasicTypeArgument):
    TAG = GITypeTag.UINT32
    py_type = int


class FloatArgument(BasicTypeArgument):
    TAG = GITypeTag.FLOAT
    py_type = float


class DoubleArgument(BasicTypeArgument):
    TAG = GITypeTag.DOUBLE
    py_type = float


class GTypeArgument(BasicTypeArgument):
    TAG = GITypeTag.GTYPE
    py_type = PGType


class VoidArgument(GIArgument):
    TAG = GITypeTag.VOID
    py_type = object

    def setup(self):
        pass

    def pre_call(self):
        var = self.get_type()
        self.call_var = var.pack_out(self.name)
        return var.block


class GListArgument(GIArgument):
    TAG = GITypeTag.GLIST
    py_type = list

    def setup(self):
        self.py_type = [self.get_param_type(0).py_type]

    def pre_call(self):
        if self.is_direction_in():
            var = self.get_type()
            self.call_var = var.pack(self.name)
            return var.block
        else:
            # FIXME
            return

    def post_call(self):
        var = self.get_type()
        if self.transfer_nothing():
            var.free(self.call_var)
        return var.block


class GSListArgument(GIArgument):
    TAG = GITypeTag.GSLIST
    py_type = list

    def setup(self):
        self.py_type = [self.get_param_type(0).py_type]


class GHashArgument(GIArgument):
    TAG = GITypeTag.GHASH
    py_type = dict

    def setup(self):
        self.py_type = {
            self.get_param_type(0).py_type: self.get_param_type(1).py_type}


class Utf8Argument(GIArgument):
    TAG = GITypeTag.UTF8
    py_type = str

    def pre_call(self):
        var = self.get_type()

        if self.is_direction_inout():
            data = var.pack_out(self.name)

            if self.transfer_everything():
                data = var.dup(data)

            self.call_var = var.get_reference(data)
            self._data = data
        elif self.is_direction_in():
            self.call_var = var.pack_in(self.name)
        else:
            self._data = var.new()
            self.call_var = var.get_reference(self._data)

        return var.block

    def post_call(self):
        if not self.is_direction_out():
            return

        var = self.get_type()
        self.out_var = var.unpack_out(self._data)
        if self.transfer_everything():
            var.free(self._data)
        return var.block

    @property
    def can_unpack_none(self):
        return True


class FilenameArgument(Utf8Argument):
    TAG = GITypeTag.FILENAME


class UniCharArgument(BasicTypeArgument):
    TAG = GITypeTag.UNICHAR
    py_type = _compat.text_type


_classes = {}


def _find_arguments():
    global _classes
    for var in globals().values():
        if not isinstance(var, type):
            continue
        if issubclass(var, GIArgument) and var is not GIArgument:
            _classes[var.TAG] = var
_find_arguments()


def get_argument_class(arg_type):
    global _classes
    tag_value = arg_type.tag.value
    try:
        cls = _classes[tag_value]
    except KeyError:
        raise NotImplementedError("%r argument not implemented" % arg_type.tag)
    else:
        return cls.get_class(arg_type)
