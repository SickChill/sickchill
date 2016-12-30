# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re
import os
import sys
import ctypes

from ._compat import PY3


# decode a path from glib
if os.name == "nt":
    def fsdecode(ffi, cdata):
        if cdata:
            return ffi.string(cdata).decode("utf-8")
elif PY3:
    _FSENC = sys.getfilesystemencoding()

    def fsdecode(ffi, cdata):
        if cdata:
            return ffi.string(cdata).decode(_FSENC, "surrogateescape")
else:
    def fsdecode(ffi, cdata):
        if cdata:
            return ffi.string(cdata)


if PY3:
    def string_decode(ffi, cdata):
        if cdata:
            bytes_ = ffi.string(cdata)
            return bytes_.decode("ascii")

    def string_encode(ffi, string, null=False):
        if string is None:
            if not null:
                return
            return ffi.cast("gchar*", ffi.NULL)
        return string.encode("ascii")
else:
    def string_decode(ffi, cdata):
        if cdata:
            return ffi.string(cdata)

    def string_encode(ffi, string, null=False):
        if string is None:
            if not null:
                return
            return ffi.cast("gchar*", ffi.NULL)
        return string


def _create_enum_class(ffi, type_name, prefix, flags=False):
    """Returns a new shiny class for the given enum type"""

    class _template(int):
        _map = {}

        @property
        def value(self):
            return int(self)

        def __str__(self):
            return self._map.get(self, "Unknown")

        def __repr__(self):
            return "%s.%s" % (type(self).__name__, str(self))

    class _template_flags(int):
        _map = {}

        @property
        def value(self):
            return int(self)

        def __str__(self):
            names = []
            val = int(self)
            for flag, name in self._map.items():
                if val & flag:
                    names.append(name)
                    val &= ~flag
            if val:
                names.append(str(val))
            return " | ".join(sorted(names or ["Unknown"]))

        def __repr__(self):
            return "%s(%s)" % (type(self).__name__, str(self))

    if flags:
        template = _template_flags
    else:
        template = _template

    cls = type(type_name, template.__bases__, dict(template.__dict__))
    prefix_len = len(prefix)
    for value, name in ffi.typeof(type_name).elements.items():
        assert name[:prefix_len] == prefix
        name = name[prefix_len:]
        setattr(cls, name, cls(value))
        cls._map[value] = name

    return cls


def _fixup_cdef_enums(string, reg=re.compile(r"=\s*(\d+)\s*<<\s*(\d+)")):
    """Converts some common enum expressions to constants"""

    def repl_shift(match):
        shift_by = int(match.group(2))
        value = int(match.group(1))
        int_value = ctypes.c_int(value << shift_by).value
        return "= %s" % str(int_value)
    return reg.sub(repl_shift, string)
