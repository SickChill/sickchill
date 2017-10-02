# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ..glib import Enum, gboolean, gint
from .gitypeinfo import GITypeInfo
from .gibaseinfo import GIBaseInfo, GIInfoType
from .._utils import find_library, wrap_class

_gir = find_library("girepository-1.0")


class GITransfer(Enum):
    NOTHING, CONTAINER, EVERYTHING = range(3)


class GIDirection(Enum):
    IN, OUT, INOUT = range(3)


class GIScopeType(Enum):
    INVALID, CALL, ASYNC, NOTIFIED = range(4)


@GIBaseInfo._register(GIInfoType.ARG)
class GIArgInfo(GIBaseInfo):

    def _get_repr(self):
        values = super(GIArgInfo, self)._get_repr()
        values["direction"] = repr(self.direction)
        values["is_caller_allocates"] = repr(self.is_caller_allocates)
        values["is_return_value"] = repr(self.is_return_value)
        values["is_optional"] = repr(self.is_optional)
        values["may_be_null"] = repr(self.may_be_null)
        values["ownership_transfer"] = repr(self.ownership_transfer)
        values["scope"] = repr(self.scope)
        if self.closure != -1:
            values["closure"] = repr(self.closure)
        if self.destroy != -1:
            values["destroy"] = repr(self.destroy)
        values["arg_type"] = repr(self.get_type())

        return values

_methods = [
    ("get_direction", GIDirection, [GIArgInfo]),
    ("is_caller_allocates", gboolean, [GIArgInfo]),
    ("is_return_value", gboolean, [GIArgInfo]),
    ("is_optional", gboolean, [GIArgInfo]),
    ("may_be_null", gboolean, [GIArgInfo]),
    ("get_ownership_transfer", GITransfer, [GIArgInfo]),
    ("get_scope", GIScopeType, [GIArgInfo]),
    ("get_closure", gint, [GIArgInfo]),
    ("get_destroy", gint, [GIArgInfo]),
    ("get_type", GITypeInfo, [GIArgInfo], True),
    ("load_type", None, [GIArgInfo, GITypeInfo]),
    ("is_skip", gboolean, [GIArgInfo]),
]

wrap_class(_gir, GIArgInfo, GIArgInfo, "g_arg_info_", _methods)

__all__ = ["GITransfer", "GIDirection", "GIScopeType", "GIArgInfo"]
