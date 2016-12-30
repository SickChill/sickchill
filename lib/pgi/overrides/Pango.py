# -*- Mode: Python; py-indent-offset: 4 -*-
# vim: tabstop=4 shiftwidth=4 expandtab
#
# Copyright (C) 2010 Paolo Borelli <pborelli@gnome.org>
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
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA

from pgi.overrides import override, get_introspection_module


Pango = get_introspection_module('Pango')

__all__ = []


class FontDescription(Pango.FontDescription):

    def __new__(cls, string=None):
        if string is not None:
            return Pango.font_description_from_string(string)
        else:
            return Pango.FontDescription.__new__(cls)

    def __init__(self, *args, **kwargs):
        return super(FontDescription, self).__init__()

FontDescription = override(FontDescription)
__all__.append('FontDescription')


class Layout(Pango.Layout):

    def __new__(cls, context):
        return Pango.Layout.new(context)

    def set_markup(self, text, length=-1):
        super(Layout, self).set_markup(text, length)

Layout = override(Layout)
__all__.append('Layout')
