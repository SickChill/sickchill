# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ._ffi import lib
from ..gobject import GParamFlags
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gitypeinfo import GITypeInfo
from .giarginfo import GITransfer


@GIBaseInfo._register(GIInfoType.PROPERTY)
class GIPropertyInfo(GIBaseInfo):

    @property
    def flags(self):
        return GParamFlags(lib.g_property_info_get_flags(self._ptr))

    def get_type(self):
        return GITypeInfo(lib.g_property_info_get_type(self._ptr))

    @property
    def ownership_transfer(self):
        return GITransfer(
            lib.g_property_info_get_ownership_transfer(self._ptr))
