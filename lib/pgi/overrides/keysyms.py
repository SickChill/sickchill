# -*- Mode: Python; py-indent-offset: 4 -*-
# pygtk - Python bindings for the GTK toolkit.
# Copyright (C) 1998-2003  James Henstridge
#
#   gtk/keysyms.py: list of keysyms.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see <http://www.gnu.org/licenses/>.

import sys
import warnings

from pgi.overrides import get_introspection_module


Gdk = get_introspection_module('Gdk')

warnings.warn('keysyms has been deprecated. Please use Gdk.KEY_<name> instead.',
              RuntimeWarning)

_modname = globals()['__name__']
_keysyms = sys.modules[_modname]

for name in dir(Gdk):
    if name.startswith('KEY_'):
        target = name[4:]
        if target[0] in '0123456789':
            target = '_' + target
        value = getattr(Gdk, name)
        setattr(_keysyms, target, value)


# Not found in Gdk but left for compatibility.
Armenian_eternity = 0x14a1
Armenian_section_sign = 0x14a2
Armenian_parenleft = 0x14a5
Armenian_guillemotright = 0x14a6
Armenian_guillemotleft = 0x14a7
Armenian_em_dash = 0x14a8
Armenian_dot = 0x14a9
Armenian_mijaket = 0x14a9
Armenian_comma = 0x14ab
Armenian_en_dash = 0x14ac
Armenian_ellipsis = 0x14ae
