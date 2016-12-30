# -*- Mode: Python; py-indent-offset: 4 -*-
# vim: tabstop=4 shiftwidth=4 expandtab
#
# Copyright (C) 2009 Johan Dahlin <johan@gnome.org>
#               2010 Simon van der Linden <svdlinden@src.gnome.org>
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

import sys
import warnings

from pgi.overrides import override, get_introspection_module, \
    strip_boolean_result
from pgi.util import PyGIDeprecationWarning
from pgi import require_version

Gdk = get_introspection_module('Gdk')

__all__ = []


# https://bugzilla.gnome.org/show_bug.cgi?id=673396
try:
    require_version("GdkX11", Gdk._version)
    from pgi.repository import GdkX11
    GdkX11  # pyflakes
except (ValueError, ImportError):
    pass


class Color(Gdk.Color):
    MAX_VALUE = 65535

    def __init__(self, red, green, blue):
        Gdk.Color.__init__(self)
        self.red = red
        self.green = green
        self.blue = blue

    def __eq__(self, other):
        return self.equal(other)

    def __repr__(self):
        return 'Gdk.Color(red=%d, green=%d, blue=%d)' % (self.red, self.green, self.blue)

    red_float = property(fget=lambda self: self.red / float(self.MAX_VALUE),
                         fset=lambda self, v: setattr(self, 'red', int(v * self.MAX_VALUE)))

    green_float = property(fget=lambda self: self.green / float(self.MAX_VALUE),
                           fset=lambda self, v: setattr(self, 'green', int(v * self.MAX_VALUE)))

    blue_float = property(fget=lambda self: self.blue / float(self.MAX_VALUE),
                          fset=lambda self, v: setattr(self, 'blue', int(v * self.MAX_VALUE)))

    def to_floats(self):
        """Return (red_float, green_float, blue_float) triple."""

        return (self.red_float, self.green_float, self.blue_float)

    @staticmethod
    def from_floats(red, green, blue):
        """Return a new Color object from red/green/blue values from 0.0 to 1.0."""

        return Color(int(red * Color.MAX_VALUE),
                     int(green * Color.MAX_VALUE),
                     int(blue * Color.MAX_VALUE))

Color = override(Color)
__all__.append('Color')

if Gdk._version == '3.0':
    class RGBA(Gdk.RGBA):
        def __init__(self, red=1.0, green=1.0, blue=1.0, alpha=1.0):
            Gdk.RGBA.__init__(self)
            self.red = red
            self.green = green
            self.blue = blue
            self.alpha = alpha

        def __eq__(self, other):
            return self.equal(other)

        def __repr__(self):
            return 'Gdk.RGBA(red=%f, green=%f, blue=%f, alpha=%f)' % (self.red, self.green, self.blue, self.alpha)

        def __iter__(self):
            """Iterator which allows easy conversion to tuple and list types."""

            yield self.red
            yield self.green
            yield self.blue
            yield self.alpha

        def to_color(self):
            """Converts this RGBA into a Color instance which excludes alpha."""

            return Color(int(self.red * Color.MAX_VALUE),
                         int(self.green * Color.MAX_VALUE),
                         int(self.blue * Color.MAX_VALUE))

        @classmethod
        def from_color(cls, color):
            """Returns a new RGBA instance given a Color instance."""

            return cls(color.red_float, color.green_float, color.blue_float)

    RGBA = override(RGBA)
    __all__.append('RGBA')

if Gdk._version == '2.0':
    class Rectangle(Gdk.Rectangle):

        def __init__(self, x, y, width, height):
            Gdk.Rectangle.__init__(self)
            self.x = x
            self.y = y
            self.width = width
            self.height = height

        def __repr__(self):
            return 'Gdk.Rectangle(x=%d, y=%d, width=%d, height=%d)' % (self.x, self.y, self.height, self.width)

    Rectangle = override(Rectangle)
    __all__.append('Rectangle')
else:
    # Newer GTK+/gobject-introspection (3.17.x) include GdkRectangle in the
    # typelib. See https://bugzilla.gnome.org/show_bug.cgi?id=748832 and
    # https://bugzilla.gnome.org/show_bug.cgi?id=748833
    if not hasattr(Gdk, 'Rectangle'):
        from pgi.repository import cairo as _cairo
        Rectangle = _cairo.RectangleInt

        __all__.append('Rectangle')
    else:
        # https://bugzilla.gnome.org/show_bug.cgi?id=756364
        # These methods used to be functions, keep aliases for backwards compat
        rectangle_intersect = Gdk.Rectangle.intersect
        rectangle_union = Gdk.Rectangle.union

        __all__.append('rectangle_intersect')
        __all__.append('rectangle_union')

if Gdk._version == '2.0':
    class Drawable(Gdk.Drawable):
        def cairo_create(self):
            return Gdk.cairo_create(self)

    Drawable = override(Drawable)
    __all__.append('Drawable')
else:
    class Window(Gdk.Window):
        def __new__(cls, parent, attributes, attributes_mask):
            # Gdk.Window had to be made abstract,
            # this override allows using the standard constructor
            return Gdk.Window.new(parent, attributes, attributes_mask)

        def __init__(self, parent, attributes, attributes_mask):
            pass

        def cairo_create(self):
            return Gdk.cairo_create(self)

    Window = override(Window)
    __all__.append('Window')

Gdk.EventType._2BUTTON_PRESS = getattr(Gdk.EventType, "2BUTTON_PRESS")
Gdk.EventType._3BUTTON_PRESS = getattr(Gdk.EventType, "3BUTTON_PRESS")


class Event(Gdk.Event):
    _UNION_MEMBERS = {
        Gdk.EventType.DELETE: 'any',
        Gdk.EventType.DESTROY: 'any',
        Gdk.EventType.EXPOSE: 'expose',
        Gdk.EventType.MOTION_NOTIFY: 'motion',
        Gdk.EventType.BUTTON_PRESS: 'button',
        Gdk.EventType._2BUTTON_PRESS: 'button',
        Gdk.EventType._3BUTTON_PRESS: 'button',
        Gdk.EventType.BUTTON_RELEASE: 'button',
        Gdk.EventType.KEY_PRESS: 'key',
        Gdk.EventType.KEY_RELEASE: 'key',
        Gdk.EventType.ENTER_NOTIFY: 'crossing',
        Gdk.EventType.LEAVE_NOTIFY: 'crossing',
        Gdk.EventType.FOCUS_CHANGE: 'focus_change',
        Gdk.EventType.CONFIGURE: 'configure',
        Gdk.EventType.MAP: 'any',
        Gdk.EventType.UNMAP: 'any',
        Gdk.EventType.PROPERTY_NOTIFY: 'property',
        Gdk.EventType.SELECTION_CLEAR: 'selection',
        Gdk.EventType.SELECTION_REQUEST: 'selection',
        Gdk.EventType.SELECTION_NOTIFY: 'selection',
        Gdk.EventType.PROXIMITY_IN: 'proximity',
        Gdk.EventType.PROXIMITY_OUT: 'proximity',
        Gdk.EventType.DRAG_ENTER: 'dnd',
        Gdk.EventType.DRAG_LEAVE: 'dnd',
        Gdk.EventType.DRAG_MOTION: 'dnd',
        Gdk.EventType.DRAG_STATUS: 'dnd',
        Gdk.EventType.DROP_START: 'dnd',
        Gdk.EventType.DROP_FINISHED: 'dnd',
        Gdk.EventType.CLIENT_EVENT: 'client',
        Gdk.EventType.VISIBILITY_NOTIFY: 'visibility',
    }

    if Gdk._version == '2.0':
        _UNION_MEMBERS[Gdk.EventType.NO_EXPOSE] = 'no_expose'

    if hasattr(Gdk.EventType, 'TOUCH_BEGIN'):
        _UNION_MEMBERS.update(
            {
                Gdk.EventType.TOUCH_BEGIN: 'touch',
                Gdk.EventType.TOUCH_UPDATE: 'touch',
                Gdk.EventType.TOUCH_END: 'touch',
                Gdk.EventType.TOUCH_CANCEL: 'touch',
            })

    def __getattr__(self, name):
        real_event = getattr(self, '_UNION_MEMBERS').get(self.type)
        if real_event:
            return getattr(getattr(self, real_event), name)
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        # pgi fixme
        Gdk.Event.__setattr__(self, name, value)
        return

        real_event = getattr(self, '_UNION_MEMBERS').get(self.type)
        if real_event:
            setattr(getattr(self, real_event), name, value)
        else:
            Gdk.Event.__setattr__(self, name, value)

    def __repr__(self):
        base_repr = Gdk.Event.__repr__(self).strip("><")
        return "<%s type=%r>" % (base_repr, self.type)

Event = override(Event)
__all__.append('Event')

# manually bind GdkEvent members to GdkEvent

modname = globals()['__name__']
module = sys.modules[modname]

# right now we can't get the type_info from the
# field info so manually list the class names
event_member_classes = ['EventAny',
                        'EventExpose',
                        'EventVisibility',
                        'EventMotion',
                        'EventButton',
                        'EventScroll',
                        'EventKey',
                        'EventCrossing',
                        'EventFocus',
                        'EventConfigure',
                        'EventProperty',
                        'EventSelection',
                        'EventOwnerChange',
                        'EventProximity',
                        'EventDND',
                        'EventWindowState',
                        'EventSetting',
                        'EventGrabBroken']

if Gdk._version == '2.0':
    event_member_classes.append('EventNoExpose')

if hasattr(Gdk, 'EventTouch'):
    event_member_classes.append('EventTouch')


# whitelist all methods that have a success return we want to mask
gsuccess_mask_funcs = ['get_state',
                       'get_axis',
                       'get_coords',
                       'get_root_coords']


for event_class in event_member_classes:
    override_class = type(event_class, (getattr(Gdk, event_class),), {})
    # add the event methods
    for method_info in Gdk.Event.__info__.get_methods():
        name = method_info.get_name()
        event_method = getattr(Gdk.Event, name)
        # python2 we need to use the __func__ attr to avoid internal
        # instance checks
        event_method = getattr(event_method, '__func__', event_method)

        # use the _gsuccess_mask decorator if this method is whitelisted
        if name in gsuccess_mask_funcs:
            event_method = strip_boolean_result(event_method)
        setattr(override_class, name, event_method)

    setattr(module, event_class, override_class)
    __all__.append(event_class)

# end GdkEvent overrides


class DragContext(Gdk.DragContext):
    def finish(self, success, del_, time):
        Gtk = get_introspection_module('Gtk')
        Gtk.drag_finish(self, success, del_, time)

DragContext = override(DragContext)
__all__.append('DragContext')


class Cursor(Gdk.Cursor):
    def __new__(cls, *args, **kwds):
        arg_len = len(args)
        kwd_len = len(kwds)
        total_len = arg_len + kwd_len

        if total_len == 1:
            # Since g_object_newv (super.__new__) does not seem valid for
            # direct use with GdkCursor, we must assume usage of at least
            # one of the C constructors to be valid.
            return cls.new(*args, **kwds)

        elif total_len == 2:
            warnings.warn('Calling "Gdk.Cursor(display, cursor_type)" has been deprecated. '
                          'Please use Gdk.Cursor.new_for_display(display, cursor_type). '
                          'See: https://wiki.gnome.org/PyGObject/InitializerDeprecations',
                          PyGIDeprecationWarning)
            return cls.new_for_display(*args, **kwds)

        elif total_len == 4:
            warnings.warn('Calling "Gdk.Cursor(display, pixbuf, x, y)" has been deprecated. '
                          'Please use Gdk.Cursor.new_from_pixbuf(display, pixbuf, x, y). '
                          'See: https://wiki.gnome.org/PyGObject/InitializerDeprecations',
                          PyGIDeprecationWarning)
            return cls.new_from_pixbuf(*args, **kwds)

        elif total_len == 6:
            if Gdk._version != '2.0':
                # pixmaps don't exist in Gdk 3.0
                raise ValueError("Wrong number of parameters")

            warnings.warn('Calling "Gdk.Cursor(source, mask, fg, bg, x, y)" has been deprecated. '
                          'Please use Gdk.Cursor.new_from_pixmap(source, mask, fg, bg, x, y). '
                          'See: https://wiki.gnome.org/PyGObject/InitializerDeprecations',
                          PyGIDeprecationWarning)
            return cls.new_from_pixmap(*args, **kwds)

        else:
            raise ValueError("Wrong number of parameters")


Cursor = override(Cursor)
__all__.append('Cursor')

color_parse = strip_boolean_result(Gdk.color_parse)
"""
    :param spec: the string specifying the color
    :type spec: :obj:`str`

    :returns: :obj:`Gdk.Color` or :obj:`None` if the parsing didn't succeed
    :rtype: :obj:`Gdk.Color` or :obj:`None`
"""

__all__.append('color_parse')


# Note, we cannot override the entire class as Gdk.Atom has no gtype, so just
# hack some individual methods
def _gdk_atom_str(atom):
    n = atom.name()
    if n:
        return n
    # fall back to atom index
    return 'Gdk.Atom<%i>' % hash(atom)


def _gdk_atom_repr(atom):
    n = atom.name()
    if n:
        return 'Gdk.Atom.intern("%s", False)' % n
    # fall back to atom index
    return '<Gdk.Atom(%i)>' % hash(atom)


Gdk.Atom.__str__ = _gdk_atom_str
Gdk.Atom.__repr__ = _gdk_atom_repr


# constants
if Gdk._version >= '3.0':
    SELECTION_PRIMARY = Gdk.atom_intern('PRIMARY', True)
    __all__.append('SELECTION_PRIMARY')

    SELECTION_SECONDARY = Gdk.atom_intern('SECONDARY', True)
    __all__.append('SELECTION_SECONDARY')

    SELECTION_CLIPBOARD = Gdk.atom_intern('CLIPBOARD', True)
    __all__.append('SELECTION_CLIPBOARD')

    TARGET_BITMAP = Gdk.atom_intern('BITMAP', True)
    __all__.append('TARGET_BITMAP')

    TARGET_COLORMAP = Gdk.atom_intern('COLORMAP', True)
    __all__.append('TARGET_COLORMAP')

    TARGET_DRAWABLE = Gdk.atom_intern('DRAWABLE', True)
    __all__.append('TARGET_DRAWABLE')

    TARGET_PIXMAP = Gdk.atom_intern('PIXMAP', True)
    __all__.append('TARGET_PIXMAP')

    TARGET_STRING = Gdk.atom_intern('STRING', True)
    __all__.append('TARGET_STRING')

    SELECTION_TYPE_ATOM = Gdk.atom_intern('ATOM', True)
    __all__.append('SELECTION_TYPE_ATOM')

    SELECTION_TYPE_BITMAP = Gdk.atom_intern('BITMAP', True)
    __all__.append('SELECTION_TYPE_BITMAP')

    SELECTION_TYPE_COLORMAP = Gdk.atom_intern('COLORMAP', True)
    __all__.append('SELECTION_TYPE_COLORMAP')

    SELECTION_TYPE_DRAWABLE = Gdk.atom_intern('DRAWABLE', True)
    __all__.append('SELECTION_TYPE_DRAWABLE')

    SELECTION_TYPE_INTEGER = Gdk.atom_intern('INTEGER', True)
    __all__.append('SELECTION_TYPE_INTEGER')

    SELECTION_TYPE_PIXMAP = Gdk.atom_intern('PIXMAP', True)
    __all__.append('SELECTION_TYPE_PIXMAP')

    SELECTION_TYPE_WINDOW = Gdk.atom_intern('WINDOW', True)
    __all__.append('SELECTION_TYPE_WINDOW')

    SELECTION_TYPE_STRING = Gdk.atom_intern('STRING', True)
    __all__.append('SELECTION_TYPE_STRING')

import sys

initialized, argv = Gdk.init_check(sys.argv)
