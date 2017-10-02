# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import byref

from .clib.gir import GIArgument


_union_access = [None, "v_boolean", "v_int8", "v_uint8", "v_int16",
                 "v_uint16", "v_int32", "v_uint32", "v_int64", "v_uint64",
                 "v_float", "v_double", None, "v_string", "v_string",
                 None, None, None, None, None, None, None]


def ConstantAttribute(info):
    arg = GIArgument()
    info.get_value(byref(arg))

    const_type = info.get_type()
    tag_type = const_type.tag.value

    value_member = _union_access[tag_type]
    if not value_member:
        raise NotImplementedError("Not supported const type: %r", tag_type)
    else:
        value = getattr(arg, value_member)

    return value
