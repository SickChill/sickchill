# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .codegen import generate_field_getter, generate_field_setter
from .codegen import get_field_type
from .clib.gir import GIFieldInfoFlags
from .util import cached_property


class FieldAttribute(object):
    _getter = None
    _setter = None

    def __init__(self, name, info):
        self._info = info
        self.name = name

    @cached_property
    def writeable(self):
        return self._info.flags.value & GIFieldInfoFlags.IS_WRITABLE

    @cached_property
    def readable(self):
        return self._info.flags.value & GIFieldInfoFlags.IS_READABLE

    @cached_property
    def py_type(self):
        return get_field_type(self._info)

    def __get__(self, instance, owner):
        # make sure we support the type, raises NotImplementedError otherwise
        self.py_type

        if not instance:
            return self

        if not self.readable:
            raise AttributeError("Field %r not readable" % self.name)

        if not self._getter:
            self._getter = generate_field_getter(self._info)

        if instance:
            return self._getter(instance)
        return self

    def __set__(self, instance, value):
        if not self.writeable:
            raise AttributeError("Field %r not writeable" % self.name)

        if not self._setter:
            self._setter = generate_field_setter(self._info)

        self._setter(instance, value)
