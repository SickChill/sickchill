# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys

PY2 = sys.version_info[0] == 2
PY3 = not PY2

if PY2:
    def implements_bool(cls):
        cls.__nonzero__ = cls.__bool__
        del cls.__bool__
        return cls
    integer_types = (int, long)
    long = long
    xrange = xrange
elif PY3:
    implements_bool = lambda x: x
    integer_types = (int,)
    long = int
    xrange = lambda *x: iter(range(*x))
