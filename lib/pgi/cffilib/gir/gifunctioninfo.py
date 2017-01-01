# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .. import _create_enum_class, glib
from .._utils import string_decode
from ._ffi import ffi, lib
from .gibaseinfo import GIBaseInfo, GIInfoType
from .gicallableinfo import GICallableInfo
from .gipropertyinfo import GIPropertyInfo


GIFunctionInfoFlags = _create_enum_class(ffi, "GIFunctionInfoFlags",
                                         "GI_FUNCTION_", flags=True)


GInvokeError = _create_enum_class(ffi, "GInvokeError", "G_INVOKE_ERROR_")


@GIBaseInfo._register(GIInfoType.FUNCTION)
class GIFunctionInfo(GICallableInfo):

    @property
    def symbol(self):
        res = lib.g_function_info_get_symbol(self._ptr)
        return string_decode(ffi, res)

    @property
    def flags(self):
        return GIFunctionInfoFlags(lib.g_function_info_get_flags(self._ptr))

    def get_property(self):
        res = lib.g_function_info_get_property(self._ptr)
        if res:
            return GIPropertyInfo(res)

    def invoke(self, in_args, out_args, return_value):
        if return_value is None:
            return_value = ffi.NULL
        else:
            return_value = return_value._ptr

        if in_args is None:
            in_args = ffi.NULL
            n_in_args = 0
        else:
            n_in_args = len(in_args)
            in_args = ffi.new("GIArgument[]", [a._ptr[0] for a in in_args])

        if out_args is None:
            out_args = ffi.NULL
            n_out_args = 0
        else:
            n_out_args = len(out_args)
            out_args = ffi.new("GIArgument[]", [a._ptr[0] for a in out_args])

        with glib.gerror() as error:
            res = lib.g_function_info_invoke(
                self._ptr, in_args, n_in_args, out_args, n_out_args,
                return_value, error)
        return bool(res)
