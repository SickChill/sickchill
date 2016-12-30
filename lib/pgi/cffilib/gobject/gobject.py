# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ._ffi import ffi, lib
from .._compat import long
from .. import _create_enum_class


GParamFlags = _create_enum_class(ffi, "GParamFlags", "G_PARAM_", flags=True)


GSignalFlags = _create_enum_class(ffi, "GSignalFlags", "G_SIGNAL_", flags=True)


class GType(long):

    @classmethod
    def from_name(cls, name):
        return cls(lib.g_type_from_name(name))


def g_type_init():
    lib.g_type_init()
