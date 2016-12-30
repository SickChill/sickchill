# Copyright 2012-2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from pgi.clib import glib
from pgi.clib.gir import GITypeTag
from pgi import _compat

from .utils import BaseType, register_type


class BasicType(BaseType):

    def pack_in(self, value):
        raise NotImplementedError

    def pack_out(self, value):
        raise NotImplementedError

    def unpack_out(self, value):
        raise NotImplementedError

    def unpack_return(self, value):
        raise NotImplementedError

    def new(self):
        raise NotImplementedError

    def pack_pointer(self, value):
        raise NotImplementedError


@register_type(GITypeTag.BOOLEAN)
class Boolean(BasicType):

    def pack_in(self, value):
        return self.parse("""
            $bool = $_.bool($value)
            """, value=value)["bool"]

    def pack_out(self, value):
        return self.parse("""
            $c_bool = $ctypes.c_int($value)
            """, value=value)["c_bool"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            $bool = $_.bool($value)
            """, ctypes_value=value)["bool"]

    def unpack_return(self, value):
        return self.parse("""
            $bool = $_.bool($value)
            """, value=value)["bool"]

    def new(self):
        return self.parse("""
            $value = $ctypes.c_int()
            """)["value"]

    def pack_pointer(self, value):
        return self.parse("""
            $ptr = $_.bool($value)
            """, value=value)["ptr"]


@register_type(GITypeTag.INT8)
class Int8(BasicType):

    def _check(self, name):
        return self.parse("""
            if not $_.isinstance($value, $basestring):
                $int = $_.int($value)
            else:
                raise TypeError("$DESC: %r not a number" % $value)

            # overflow check for int8
            if not -2**7 <= $int < 2**7:
                raise $_.OverflowError("$DESC: Value %r not in range" % $int)
            """, value=name, basestring=_compat.string_types)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $cvalue = $ctypes.c_int8($value)
            """, value=checked)["cvalue"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            $value = $ctypes.c_int8()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.UINT8)
class UInt8(BasicType):

    def _check(self, name):

        if _compat.PY3:
            int_text_types = (str, bytes)
        else:
            int_text_types = (unicode, str)

        return self.parse("""
            # uint8 type/value check
            if $_.isinstance($value, $text_types):
                if $_.isinstance($value, $_.bytes):
                    try:
                        $value = $_.ord($value)
                    except $_.TypeError:
                        raise $_.TypeError("$DESC: must be a single character")
                else:
                    raise $_.TypeError("$DESC: must be a str character")

            $uint = $_.int($value)

            # overflow check for uint8
            if not 0 <= $uint < 2**8:
                raise $_.OverflowError("$DESC: %r not in range" % $uint)
            """, value=name, text_types=int_text_types)["uint"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $cvalue = $ctypes.c_uint8($value)
            """, value=checked)["cvalue"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            $value = $ctypes.c_uint8()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.INT16)
class Int16(BasicType):

    def _check(self, name):
        return self.parse("""
            if not $_.isinstance($value, $basestring):
                $int = $_.int($value)
            else:
                raise $_.TypeError("$DESC: not a number")

            # overflow check for int16
            if not -2**15 <= $int < 2**15:
                raise $_.OverflowError("$DESC: %r not in range" % $int)
            """, value=name, basestring=_compat.string_types)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $cvalue = $ctypes.c_int16($value)
            """, value=checked)["cvalue"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            $value = $ctypes.c_int16()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.UINT16)
class UInt16(BasicType):

    def _check(self, name):
        return self.parse("""
            if not $_.isinstance($value, $basestring):
                $int = $_.int($value)
            else:
                raise $_.TypeError("$DESC: not a number")

            # overflow check for uint16
            if not 0 <= $int < 2**16:
                raise $_.OverflowError("$DESC: %r not in range" % $int)
            """, value=name, basestring=_compat.string_types)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $cvalue = $ctypes.c_uint16($value)
            """, value=checked)["cvalue"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            $value = $ctypes.c_uint16()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.INT32)
class Int32(BasicType):

    def _check(self, name):
        return self.parse("""
            # int32 type/value check
            if not $_.isinstance($value, $basestring):
                $int = $_.int($value)
            else:
                raise $_.TypeError("$DESC: not a number")

            if not -2**31 <= $int < 2**31:
                raise $_.OverflowError("$DESC: %r not in range" % $int)
            """, value=name, basestring=_compat.string_types)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $c_value = $ctypes.c_int32($value)
            """, value=checked)["c_value"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            $value = $ctypes.c_int32()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.UINT32)
class UInt32(BasicType):

    def _check(self, name):
        return self.parse("""
            # uint32 type/value check
            if not $_.isinstance($value, $basestring):
                $int = $_.int($value)
            else:
                raise $_.TypeError("$DESC: not a number")

            if not 0 <= $int < 2**32:
                raise $_.OverflowError("$DESC: %r not in range" % $int)
            """, value=name, basestring=_compat.string_types)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $c_value = $ctypes.c_uint32($value)
            """, value=checked)["c_value"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            $value = $ctypes.c_uint32()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.INT64)
class Int64(BasicType):

    def _check(self, name):
        return self.parse("""
            # int64 type/value check
            if not $_.isinstance($value, $basestring):
                $int = $_.int($value)
            else:
                raise $_.TypeError("$DESC: not a number")

            if not -2**63 <= $int < 2**63:
                raise $_.OverflowError("$DESC: %r not in range" % $int)
            """, value=name, basestring=_compat.string_types)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $c_value = $ctypes.c_int64($value)
            """, value=checked)["c_value"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            # new int64
            $value = $ctypes.c_int64()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.UINT64)
class UInt64(BasicType):

    def _check(self, name):
        return self.parse("""
            # uint64 type/value check
            if not $_.isinstance($value, $basestring):
                $int = $_.int($value)
            else:
                raise $_.TypeError("$DESC: not a number")

            if not 0 <= $int < 2**64:
                raise $_.OverflowError("$DESC: %r not in range" % $int)
            """, value=name, basestring=_compat.string_types)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(value)
        return self.parse("""
            $c_value = $ctypes.c_uint64($value)
            """, value=checked)["c_value"]

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            # new uint64
            $value = $ctypes.c_uint64()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.FLOAT)
class Float(BasicType):

    def _check(self, name):
        return self.parse("""
            # float type/value check
            if $_.isinstance($value, $basestring):
                raise $_.TypeError("$DESC: not a number")
            $float = $_.float($value)
            $c_float = $ctypes.c_float($float)
            $c_value = $c_float.value
            if $c_value != $float and \\
                    $c_value in ($_.float('inf'), $_.float('-inf'),
                                 $_.float('nan')):
                raise $_.OverflowError("$DESC: %r out of range" % $float)
            """, value=name, basestring=_compat.string_types)["c_float"]

    def pack_in(self, value):
        return self._check(value)

    pack_out = pack_in

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            # new float
            $value = $ctypes.c_float()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.DOUBLE)
class Double(BasicType):

    def _check(self, name):
        return self.parse("""
            # double type/value check
            if $_.isinstance($value, $basestring):
                raise $_.TypeError("$DESC: not a number")
            $double = $_.float($value)
            $c_double = $ctypes.c_double($double)
            $c_value = $c_double.value
            if $c_value != $double and \\
                    $c_value in ($_.float('inf'), $_.float('-inf'),
                                 $_.float('nan')):
                raise $_.OverflowError("$DESC: %f out of range" % $double)
            """, value=name, basestring=_compat.string_types)["c_double"]

    def pack_in(self, value):
        return self._check(value)

    pack_out = pack_in

    def unpack_out(self, value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=value)["value"]

    def unpack_return(self, value):
        return value

    def new(self):
        return self.parse("""
            # new float
            $value = $ctypes.c_double()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.UNICHAR)
class UniChar(BasicType):

    def _check_py2(self, name):
        return self.parse("""
            if $_.isinstance($value, $_.str):
                $value = $value.decode("utf-8")
            elif not isinstance($value, $_.unicode):
                raise $_.TypeError("$DESC")

            $int = $_.ord($value)

            if not 0 <= $int < 2**32:
                raise $_.OverflowError("$DESC: %r not in range" % $int)
            """, value=name)["int"]

    def _check_py3(self, name):
        return self.parse("""
            $int = $_.ord($value)

            if not 0 <= $int < 2**32:
                raise $_.OverflowError("$DESC: %r not in range" % $int)
            """, value=name)["int"]

    def pack_in(self, value):
        return self._check(value)

    def pack_out(self, value):
        checked = self._check(self, value)
        return self.parse("""
            $c_value = $ctypes.c_uint32($value)
            """, value=checked)["c_value"]

    def unpack_out_py2(self, name):
        return self.parse("""
            $out = $_.unichr($value.value).encode("utf-8")
            """, value=name)["out"]

    def unpack_out_py3(self, name):
        return self.parse("""
            $out = $_.chr($value.value)
            """, value=name)["out"]

    def unpack_return_py2(self, name):
        return self.parse("""
            $out = $_.unichr($value).encode("utf-8")
            """, value=name)["out"]

    def unpack_return_py3(self, name):
        return self.parse("""
            $out = $_.chr($value)
            """, value=name)["out"]

    def new(self):
        return self.parse("""
            $value = $ctypes.c_uint32()
            """)["value"]

    pack_pointer = pack_in


@register_type(GITypeTag.VOID)
class Void(BaseType):

    def _check(self, name):
        if self.may_be_null:
            return name

        return self.parse("""
            if $ptr is None:
                raise $_.TypeError("$DESC: No None allowed")
            """, ptr=name)["ptr"]

    def pack_in(self, value):
        checked = self._check(value)
        return self.parse("""
            $c_ptr = $ctypes.c_void_p($ptr)
            """, ptr=checked)["c_ptr"]

    pack_out = pack_in

    def unpack_out(self, name):
        if self.type.is_pointer:
            return "None"

        return self.parse("""
            $value = $ptr.value
            """, ptr=name)["value"]

    unpack_return = unpack_out

    def new(self):
        assert self.type.is_pointer

        return self.parse("""
            $c_ptr = $ctypes.c_void_p()
            """)["c_ptr"]

    pack_pointer = pack_in


@register_type(GITypeTag.UTF8)
class Utf8(BaseType):

    def _check_py3(self, name):
        if self.may_be_null:
            return self.parse("""
                if $value is not None:
                    if not $_.isinstance($value, $_.str):
                        raise $_.TypeError(
                            "$DESC: %r not a string or None" % $value)
                    else:
                        $string = $value
                else:
                    $string = None
                """, value=name)["string"]

        return self.parse("""
            if not isinstance($value, $_.str):
                raise $_.TypeError("$DESC: %r not a string" % $value)
            else:
                $string = $value
            """, value=name)["string"]

    def _check_py2(self, name):
        if self.may_be_null:
            return self.parse("""
                if $value is not None:
                    if $_.isinstance($value, $_.unicode):
                        $string = $value.encode("utf-8")
                    elif not $_.isinstance($value, $_.str):
                        raise $_.TypeError(
                            "$DESC: %r not a string or None" % $value)
                    else:
                        $string = $value
                else:
                    $string = None
                """, value=name)["string"]

        return self.parse("""
            if $_.isinstance($value, $_.unicode):
                $string = $value.encode("utf-8")
            elif not isinstance($value, $_.str):
                raise $_.TypeError("$DESC: %r not a string" % $value)
            else:
                $string = $value
            """, value=name)["string"]

    def pack_in_py2(self, name):
        return self._check(name)

    def pack_in_py3(self, name):
        checked = self._check(name)
        return self.parse("""
            $encoded = $value
            if $value is not None:
                $encoded = $value.encode("utf-8")
            """, value=checked)["encoded"]

    def pack_out_py2(self, name):
        checked = self._check(name)
        return self.parse("""
            $c_value = $ctypes.c_char_p($value)
            """, value=checked)["c_value"]

    def pack_out_py3(self, name):
        checked = self._check(name)
        return self.parse("""
            if $value is not None:
                $value = $value.encode("utf-8")
            $c_value = $ctypes.c_char_p($value)
            """, value=checked)["c_value"]

    def dup(self, name):
        var = self.parse("""
            if $ptr:
                $ptr_cpy = $ctypes.c_char_p($glib.g_strdup($ptr))
            else:
                $ptr_cpy = $none
            """, ptr=name, glib=glib, none=None)

        return var["ptr_cpy"]

    def unpack_out_py2(self, c_value):
        return self.parse("""
            $value = $ctypes_value.value
            """, ctypes_value=c_value)["value"]

    def unpack_out_py3(self, name):
        return self.parse("""
            $value = $ctypes_value.value
            if $value is not None:
                $value = $value.decode("utf-8")
            """, ctypes_value=name)["value"]

    def unpack_return_py2(self, name):
        return self.parse("""
            $str_value = $ctypes.c_char_p($value).value
            """, value=name)["str_value"]

    def unpack_return_py3(self, name):
        return self.parse("""
            $str_value = $ctypes.c_char_p($value).value
            if $str_value is not None:
                $str_value = $str_value.decode("utf-8")
            """, value=name)["str_value"]

    def new(self):
        return self.parse("""
            $value = $ctypes.c_char_p()
            """)["value"]

    def pack_pointer(self, value):
        checked = self._check(value)
        return self.parse("""
            $ptr = ord($value)
            """, value=checked)["ptr"]


@register_type(GITypeTag.FILENAME)
class Filename(Utf8):
    pass
