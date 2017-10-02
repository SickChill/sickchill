# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ._ffi import ffi, lib
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gitypeinfo import GITypeInfo


@GIBaseInfo._register(GIInfoType.CONSTANT)
class GIConstantInfo(GIBaseInfo):

    def get_type(self):
        return GITypeInfo(lib.g_constant_info_get_type(self._ptr))

    def get_value(self):
        arg = ffi.new("GIArgument*")
        size = lib.g_constant_info_get_value(self._ptr, arg)
        return (size, arg[0])
