# Copyright 2012-2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from pgi.clib.gir import GITypeTag
from pgi.clib.glib import GErrorPtr
from pgi.clib.gobject import GType
from pgi.gerror import PGError
from pgi.gtype import PGType

from .utils import BaseType, registry


@registry.register(GITypeTag.GTYPE)
class GType_(BaseType):

    def _check(self, name):
        gtype_map = {
            str: "gchararray",
            int: "gint",
            float: "gdouble",
            bool: "gboolean",
        }

        items = gtype_map.items()
        gtype_map = dict((k, PGType.from_name(v)) for (k, v) in items)

        var = self.parse("""
if not $_.isinstance($obj, $PGType):
    if hasattr($obj, "__gtype__"):
        $obj = $obj.__gtype__
    elif $obj in $gtype_map:
        $obj = $gtype_map[$obj]

if not $_.isinstance($obj, $PGType):
    raise TypeError("%r not a GType" % $obj)
""", gtype_map=gtype_map, obj=name, PGType=PGType)

        return var["obj"]

    def pack_in(self, name):
        checked = self._check(name)
        var = self.parse("""
$gtype = $GType($obj._type.value)
""", obj=checked, GType=GType)

        return var["gtype"]

    pack_out = pack_in

    def unpack_out(self, name):
        var = self.parse("""
$pgtype = $PGType($gtype)
""", gtype=name, PGType=PGType)

        return var["pgtype"]

    unpack_return = unpack_out

    def new(self):
        var = self.parse("""
$gtype = $GType()
""", GType=GType)

        return var["gtype"]


@registry.register(GITypeTag.ERROR)
class Error(BaseType):

    def unpack(self, name, own=False):
        var = self.parse("""
if $gerror_ptr:
    $out = $PGError._from_gerror($gerror_ptr, $own)
else:
    $out = $none
""", gerror_ptr=name, PGError=PGError, none=None, own=own)

        return var["out"]

    def check_raise(self, name):
        self.parse("""
if $error:
    raise $error
""", error=name)

    def new(self):
        return self.parse("""
$ptr = $gerror_ptr()
""", gerror_ptr=GErrorPtr)["ptr"]
