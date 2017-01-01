# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys


PY2 = sys.version_info[0] == 2
PY3 = not PY2


if PY3:
    xrange = range
elif PY2:
    xrange = xrange
else:
    assert 0
