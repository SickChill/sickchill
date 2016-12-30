# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .._compat import xrange
from ._ffi import lib
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gitypeinfo import GITypeInfo
from .giregisteredtypeinfo import GIRegisteredTypeInfo


@GIBaseInfo._register(GIInfoType.UNION)
class GIUnionInfo(GIRegisteredTypeInfo):

    @property
    def n_fields(self):
        return lib.g_union_info_get_n_fields(self._ptr)

    def get_field(self, n):
        return lib.g_union_info_get_field(self._ptr, n)

    def get_fields(self):
        for i in xrange(self.n_fields):
            yield self.get_field(i)

    @property
    def n_methods(self):
        return lib.g_union_info_get_n_methods(self._ptr)

    def get_method(self):
        return lib.g_union_info_get_method(self._ptr)

    def get_methods(self):
        for i in xrange(self.n_methods):
            yield self.get_method(i)

    @property
    def is_discriminated(self):
        return bool(lib.g_union_info_is_discriminated(self._ptr))

    @property
    def discriminator_offset(self):
        return lib.g_union_info_get_discriminator_offset(self._ptr)

    @property
    def discriminator_type(self):
        return GITypeInfo(lib.g_union_info_get_discriminator_type(self._ptr))

    def get_discriminator(self, n):
        # FIXME
        return lib.g_union_info_get_discriminator(self._ptr, n)

    def find_method(self, name):
        # FIXME
        return lib.g_union_info_find_method(self._ptr, name)

    @property
    def size(self):
        return lib.g_union_info_get_size(self._ptr)

    @property
    def alignment(self):
        return lib.g_union_info_get_alignment(self._ptr)
