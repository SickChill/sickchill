# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
import cffi

from .. import gobject
from ._cdef import GIR_CDEF


ffi = cffi.FFI()
ffi.include(gobject.ffi)
ffi.cdef(GIR_CDEF)

if sys.platform == 'win32':
    lib = ffi.dlopen("libgirepository-1.0-1.dll")
else:
    lib = ffi.dlopen("libgirepository-1.0.so.1")


__all__ = ["ffi", "lib"]
