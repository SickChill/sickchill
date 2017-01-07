# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ._ffi import ffi, lib
from .._utils import string_decode
from .gibaseinfo import GIBaseInfo


class GIRegisteredTypeInfo(GIBaseInfo):

    @property
    def type_name(self):
        res = lib.g_registered_type_info_get_type_name(self._ptr)
        return string_decode(ffi, res)

    @property
    def type_init(self):
        res = lib.g_registered_type_info_get_type_init(self._ptr)
        return string_decode(ffi, res)

    def get_g_type(self):
        # FIXME
        return lib.g_registered_type_info_get_g_type(self._ptr)
