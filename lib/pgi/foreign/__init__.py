# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""Foreign structs make it possible for gi to interact with other python
libraries. For example it allows functions to take cairo structs created
with cairocffi.
"""

import importlib

from ._base import ForeignStruct, ForeignError


_MODULES = {}


def get_foreign_module(namespace):
    """Returns the module or raises ForeignError"""

    if namespace not in _MODULES:
        try:
            module = importlib.import_module("." + namespace, __package__)
        except ImportError:
            module = None
        _MODULES[namespace] = module

    module = _MODULES.get(namespace)
    if module is None:
        raise ForeignError("Foreign %r structs not supported" % namespace)
    return module


def get_foreign_struct(namespace, name):
    """Returns a ForeignStruct implementation or raises ForeignError"""

    get_foreign_module(namespace)

    try:
        return ForeignStruct.get(namespace, name)
    except KeyError:
        raise ForeignError("Foreign %s.%s not supported" % (namespace, name))


def require_foreign(namespace, symbol=None):
    """Raises ImportError if the specified foreign module isn't supported or
    the needed dependencies aren't installed.

    e.g.: check_foreign('cairo', 'Context')
    """

    
    try:
        if symbol is None:
            get_foreign_module(namespace)
        else:
            get_foreign_struct(namespace, symbol)
    except ForeignError as e:
        raise ImportError(e)


def get_foreign(namespace, name):
    """Returns a ForeignStruct instance or None"""

    try:
        return get_foreign_struct(namespace, name)
    except ForeignError:
        return None
