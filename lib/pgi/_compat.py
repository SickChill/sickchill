# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from __future__ import print_function

import sys


PY2 = sys.version_info[0] == 2
PY3 = not PY2

print_ = print

if PY3:
    string_types = (str,)
    text_type = str
    integer_types = (int,)
    long_type = int

    import builtins
    exec_ = getattr(builtins, "exec")

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

    xrange = range

    from io import StringIO
    StringIO = StringIO

    import builtins
    builtins = builtins
elif PY2:
    string_types = (str, unicode)
    text_type = unicode
    integer_types = (int, long)
    long_type = long

    def exec_(_code_, _globs_=None, _locs_=None):
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

    xrange = xrange

    from StringIO import StringIO
    StringIO = StringIO

    import __builtin__ as builtins
    builtins = builtins
else:
    assert 0
