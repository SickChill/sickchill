# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import cffi
import cairocffi

from ._base import ForeignStruct


ffi = cffi.FFI()

@ForeignStruct.register("cairo", "Context")
class Context(ForeignStruct):

    def from_pointer(self, pointer):
        pointer = ffi.cast("void*", pointer)
        return cairocffi.Context._from_pointer(pointer, True)

    def to_pointer(self, instance):
        return int(ffi.cast("intptr_t", instance._pointer))

    def get_type(self):
        return cairocffi.Context


@ForeignStruct.register("cairo", "Surface")
class Surface(ForeignStruct):

    def from_pointer(self, pointer):
        pointer = ffi.cast("void*", pointer)
        return cairocffi.Surface._from_pointer(pointer, True)

    def to_pointer(self, instance):
        return int(ffi.cast("intptr_t", instance._pointer))

    def get_type(self):
        return cairocffi.Surface
