# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import sys
import cffi

from .. import glib
from ._cdef import GOBJECT_CDEF


ffi = cffi.FFI()
ffi.include(glib.ffi)
ffi.cdef(GOBJECT_CDEF)

if sys.platform == 'win32':
    lib = ffi.dlopen("libgobject-2.0-0.dll")
else:
    lib = ffi.dlopen("libgobject-2.0.so.0")


__all__ = ["ffi", "lib"]
