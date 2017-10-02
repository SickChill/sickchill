# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys


def pprint(obj, file_=None):
    """Prints debug information for various public objects like methods,
    functions, constructors etc.
    """

    if file_ is None:
        file_ = sys.stdout

    # functions, methods
    if callable(obj) and hasattr(obj, "_code"):
        obj._code.pprint(file_)
        return

    # classes
    if isinstance(obj, type) and hasattr(obj, "_constructors"):
        constructors = obj._constructors
        for names, func in sorted(constructors.items()):
            func._code.pprint(file_)
        return

    raise TypeError("unkown type")
