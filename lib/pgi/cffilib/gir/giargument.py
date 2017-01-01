# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ._ffi import ffi
from ..glib import strdup
from .._compat import PY3


class GIArgument(object):

    def __init__(self, **kwargs):
        self._ptr = ffi.new("GIArgument*")
        for key, value in kwargs.items():
            # FIXME: leaks..
            if key == "v_string":
                if PY3:
                    value = value.encode("utf-8")
                value = strdup(value)
            setattr(self._ptr, key, value)

    def __getattr__(self, key):
        res = getattr(self._ptr, key)
        if key == "v_string":
            if res:
                res = ffi.string(res)
                if PY3:
                    res = res.decode("utf-8")
                return res
        else:
            return res

__all__ = ["GIArgument"]
