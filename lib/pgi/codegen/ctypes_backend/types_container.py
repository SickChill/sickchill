# Copyright 2012-2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import ctypes

from pgi.clib.gir import GITypeTag, GIArrayType
from pgi.clib import glib
from .utils import BaseType, registry, typeinfo_to_ctypes


@registry.register(GITypeTag.ARRAY)
class BaseArray(BaseType):

    @classmethod
    def get_class(cls, type_):
        type_ = type_.array_type.value

        if type_ == GIArrayType.C:
            return CArray

        raise NotImplementedError("unsupported array type: %r" % type_)


class CArray(BaseArray):

    def check(self, name):
        if self.type.array_fixed_size != -1:
            length = self.type.array_fixed_size
            self.parse("""
                $array_len = $_.len($l)
                if $array_len != $length:
                    raise ValueError(
                        "$DESC: Expected list of length %d, got $length" %
                        $array_len)
                """, l=name, length=length)
        return name

    def pack(self, name, length_type):
        return self._pack(name, length_type, True)

    def pack_in(self, name, length_type):
        return self._pack(name, length_type, False)

    def _pack(self, name, length_type, out=True):
        # length
        if self.type.array_length != -1:
            l = self.get_type(
                length_type, desc="Return value of __len__() of %s" % self.desc)
            length = l.parse("$len = $_.len($inp)", inp=name)["len"]
            packed_length = l.pack_out(length)
            l.block.write_into(self.block)
        elif self.type.array_fixed_size != -1:
            length = self.type.array_fixed_size
            packed_length = ""
        else:
            length = self.parse("$len = $_.len($inp)",
                                inp=name)["len"]
            packed_length = ""

        # param
        param_type = self.type.get_param_type(0)
        p = self.get_type(param_type, desc="Element of %s" % self.desc)
        item_in = self.var()
        item_out = p.pack_in(item_in)
        ctypes_type = typeinfo_to_ctypes(param_type)

        if out:
            getref = ctypes.pointer
        else:
            getref = ctypes.byref

        # array zero term
        if self.type.is_zero_terminated:
            return self.parse("""
                $array = ($ctypes_type * ($length + 1))()
                for $i, $item_in in $_.enumerate($name):
                    $param_pack
                    $array[$i] = $item_out
                $array[-1] = $ctypes_type()
                $array_ptr = $getref($array)
                    """, name=name, item_in=item_in, item_out=item_out,
                param_pack=p.block, ctypes_type=ctypes_type, length=length,
                getref=getref)["array_ptr"], packed_length

        if self.type.array_fixed_size != -1:
            array_type = ctypes_type * length
            return self.parse("""
                $array = $array_type()
                for $i, $item_in in $_.enumerate($name):
                    $param_pack
                    $array[$i] = $item_out
                $array_ptr = $getref($array)
                """, name=name, item_in=item_in, item_out=item_out,
                param_pack=p.block, array_type=array_type,
                getref=getref)["array_ptr"], packed_length

        # non zero term
        return self.parse("""
            $array_type = ($ctypes_type * $length)
            $array = $array_type()
            for $i, $item_in in $_.enumerate($name):
                $param_pack
                $array[$i] = $item_out
            $array_ptr = $getref($array)
            """, name=name, item_in=item_in, item_out=item_out,
            param_pack=p.block, ctypes_type=ctypes_type, length=length,
            getref=getref)["array_ptr"], packed_length

    def unpack(self, name, length):
        param_type = self.type.get_param_type(0)
        ctypes_type = typeinfo_to_ctypes(param_type)

        data = self.parse("""
            $data = $ctypes.cast($value, $ctypes.POINTER($type))
            """, value=name, type=ctypes_type)["data"]

        p = self.get_type(param_type)
        item_in = self.var()
        item_out = p.unpack_return(item_in)

        if self.type.array_length != -1:
            return self.parse("""
                $out = []
                for $item_in in $array[:$length.value]:
                    $unpack_item
                    $out.append($item_out)
                #$out = $array[:$length.value]
                """, array=data, length=length, unpack_item=p.block,
                item_in=item_in, item_out=item_out)["out"]

        elif self.type.array_fixed_size != -1:
            return self.parse("""
                $out = []
                for $item_in in $array[:$length]:
                    $unpack_item
                    $out.append($item_out)
                """, array=data, length=self.type.array_fixed_size,
                unpack_item=p.block, item_in=item_in, item_out=item_out)["out"]
        else:
            return self.parse("""
                $list = []
                $i = 0
                $current = $array and $array[$i]
                while $current:
                    $item_in = $current
                    $unpack_item
                    $list.append($item_out)
                    $i += 1
                    $current = $array[$i]
                """, array=data, unpack_item=p.block,
                item_in=item_in, item_out=item_out)["list"]

    def new(self, length_type):
        if self.type.array_length != -1:
            l = self.get_type(length_type)
            packed_length = l.new()
            l.block.write_into(self.block)
        else:
            packed_length = ""

        if self.type.is_zero_terminated or self.type.array_length != -1:
            return self.parse("""
                $array = $ctypes.c_void_p()
                """)["array"], packed_length
        elif self.type.array_fixed_size != -1:
            param_type = self.type.get_param_type(0)
            ctypes_type = typeinfo_to_ctypes(param_type)
            length = self.type.array_fixed_size

            return self.parse("""
                $data = ($ctypes_type * $length)()
                $array = $ctypes.pointer($data)
                """, ctypes_type=ctypes_type,
                length=length)["array"], packed_length
        else:
            raise NotImplementedError

    def unpack_return(self, name):
        raise NotImplementedError


@registry.register(GITypeTag.GLIST)
class GList(BaseType):

    def check(self, name):
        pass

    def pack(self, name):
        param_type_info = self.type.get_param_type(0)
        param_type = self.get_type(param_type_info)

        param_in = self.var()
        param_out = param_type.pack_pointer(param_type.pack_in(param_in))

        return self.parse("""
            $new = $GListPtr()
            for $item in $seq:
                $param_check_pack
                $new = $new.prepend($item_out)
            $new = $new.reverse()
            """, seq=name, GListPtr=glib.GListPtr, item=param_in,
            param_check_pack=param_type.block, item_out=param_out)["new"]

    def unpack(self, name):
        param_type = self.type.get_param_type(0)
        ctypes_type = typeinfo_to_ctypes(param_type)

        p = self.get_type(param_type)
        item_in = self.var()
        item_out = p.unpack_return(item_in)

        return self.parse("""
            $out = []
            $elm = $in_
            while $elm:
                $entry = $elm.contents
                $item_in = $ctypes_type($entry.data or 0).value
                $item_unpack
                $out.append($item_out)
                $elm = $entry.next
            """, in_=name, ctypes_type=ctypes_type, item_in=item_in,
            item_out=item_out, item_unpack=p.block)["out"]

    def free(self, name):
        return self.parse("""
            $list_.free()
            """, list_=name)


@registry.register(GITypeTag.GSLIST)
class GSList(BaseType):
    pass
