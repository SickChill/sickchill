# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ._ffi import ffi, lib
from .. import _create_enum_class
from ..gobject import GSignalFlags
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gicallableinfo import GICallableInfo
from .gifunctioninfo import GIFunctionInfo


@GIBaseInfo._register(GIInfoType.SIGNAL)
class GISignalInfo(GICallableInfo):

    @property
    def flags(self):
        return GSignalFlags(lib.g_signal_info_get_flags(self._ptr))

    @property
    def true_stops_emit(self):
        return lib.g_signal_info_true_stops_emit(self._ptr)

    def get_class_closure(self):
        res = lib.g_signal_info_get_class_closure(self._ptr)
        if res:
            return GIVFuncInfo(res)


GIVFuncInfoFlags = _create_enum_class(ffi, "GIVFuncInfoFlags", "GI_VFUNC_")


@GIBaseInfo._register(GIInfoType.VFUNC)
class GIVFuncInfo(GICallableInfo):

    @property
    def flags(self):
        return GIVFuncInfoFlags(lib.g_vfunc_info_get_flags(self._ptr))

    @property
    def offset(self):
        return lib.g_vfunc_info_get_offset(self._ptr)

    def get_signal(self):
        res = lib.g_vfunc_info_get_signal(self._ptr)
        if res:
            return GISignalInfo(res)

    def get_invoker(self):
        res = lib.g_vfunc_info_get_invoker(self._ptr)
        if res:
            return GIFunctionInfo(res)
