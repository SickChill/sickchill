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

import collections
import sys
import warnings

from pgi.repository import GObject
from pgi.overrides import override, get_introspection_module, \
    strip_boolean_result, deprecated_init
from pgi import PyGIDeprecationWarning

if sys.version_info >= (3, 0):
    _basestring = str
    _callable = lambda c: hasattr(c, '__call__')
else:
    _basestring = basestring
    _callable = callable

Gtk = get_introspection_module('Gtk')

__all__ = []

if Gtk._version == '2.0':
    warn_msg = "You have imported the Gtk 2.0 module.  Because Gtk 2.0 \
was not designed for use with introspection some of the \
interfaces and API will fail.  As such this is not supported \
by the pygobject development team and we encourage you to \
port your app to Gtk 3 or greater. PyGTK is the recomended \
python module to use with Gtk 2.0"

    warnings.warn(warn_msg, RuntimeWarning)


class PyGTKDeprecationWarning(PyGIDeprecationWarning):
    pass

__all__.append('PyGTKDeprecationWarning')


def _construct_target_list(targets):
    """Create a list of TargetEntry items from a list of tuples in the form (target, flags, info)

    The list can also contain existing TargetEntry items in which case the existing entry
    is re-used in the return list.
    """
    target_entries = []
    for entry in targets:
        if not isinstance(entry, Gtk.TargetEntry):
            entry = Gtk.TargetEntry.new(*entry)
        target_entries.append(entry)
    return target_entries

__all__.append('_construct_target_list')


def _extract_handler_and_args(obj_or_map, handler_name):
    handler = None
    if isinstance(obj_or_map, collections.Mapping):
        handler = obj_or_map.get(handler_name, None)
    else:
        handler = getattr(obj_or_map, handler_name, None)

    if handler is None:
        raise AttributeError('Handler %s not found' % handler_name)

    args = ()
    if isinstance(handler, collections.Sequence):
        if len(handler) == 0:
            raise TypeError("Handler %s tuple can not be empty" % handler)
        args = handler[1:]
        handler = handler[0]

    elif not _callable(handler):
        raise TypeError('Handler %s is not a method, function or tuple' % handler)

    return handler, args


# Exposed for unit-testing.
__all__.append('_extract_handler_and_args')


def _builder_connect_callback(builder, gobj, signal_name, handler_name, connect_obj, flags, obj_or_map):
    handler, args = _extract_handler_and_args(obj_or_map, handler_name)

    after = flags & GObject.ConnectFlags.AFTER
    if connect_obj is not None:
        if after:
            gobj.connect_object_after(signal_name, handler, connect_obj, *args)
        else:
            gobj.connect_object(signal_name, handler, connect_obj, *args)
    else:
        if after:
            gobj.connect_after(signal_name, handler, *args)
        else:
            gobj.connect(signal_name, handler, *args)


class Widget(Gtk.Widget):

    translate_coordinates = strip_boolean_result(Gtk.Widget.translate_coordinates)
    """
    :param dest_widget: a :obj:`Gtk.Widget`
    :type dest_widget: :obj:`Gtk.Widget`
    :param src_x: X position relative to `self`
    :type src_x: :obj:`int`
    :param src_y: Y position relative to `self`
    :type src_y: :obj:`int`
    :returns:
        :obj:`None` if either widget was not realized, or there
        was no common ancestor. Otherwise a ``(dest_x, dest_y)`` tuple
        containing the X and Y position relative to `dest_widget`.
    :rtype: (**dest_x**: :obj:`int`, **dest_y**: :obj:`int`) or :obj:`None`

    {{ docs }}
    """

    def drag_dest_set_target_list(self, target_list):
        if (target_list is not None) and (not isinstance(target_list, Gtk.TargetList)):
            target_list = Gtk.TargetList.new(_construct_target_list(target_list))
        super(Widget, self).drag_dest_set_target_list(target_list)

    def drag_source_set_target_list(self, target_list):
        if (target_list is not None) and (not isinstance(target_list, Gtk.TargetList)):
            target_list = Gtk.TargetList.new(_construct_target_list(target_list))
        super(Widget, self).drag_source_set_target_list(target_list)

    def style_get_property(self, property_name, value=None):
        """style_get_property(property_name, value=None)

        :param property_name:
            the name of a style property
        :type property_name: :obj:`str`

        :param value:
            Either :obj:`None` or a correctly initialized :obj:`GObject.Value`
        :type value: :obj:`GObject.Value` or :obj:`None`

        :returns: The Python value of the style property

        {{ docs }}
        """

        if value is None:
            prop = self.find_style_property(property_name)
            if prop is None:
                raise ValueError('Class "%s" does not contain style property "%s"' %
                                 (self, property_name))
            value = GObject.Value(prop.value_type)

        Gtk.Widget.style_get_property(self, property_name, value)
        return value.get_value()


Widget = override(Widget)
__all__.append('Widget')


class Container(Gtk.Container, Widget):
    def __len__(self):
        return len(self.get_children())

    def __contains__(self, child):
        return child in self.get_children()

    def __iter__(self):
        return iter(self.get_children())

    def __bool__(self):
        return True

    # alias for Python 2.x object protocol
    __nonzero__ = __bool__

    get_focus_chain = strip_boolean_result(Gtk.Container.get_focus_chain)
    """
    :returns:
        A list of focusable widgets or :obj:`None` if no focus chain has
        been explicitly set.

    :rtype: [:obj:`Gtk.Widget`] or :obj:`None`

    Retrieves the focus chain of the container, if one has been
    set explicitly. If no focus chain has been explicitly
    set, GTK+ computes the focus chain based on the positions
    of the children. In that case returns :obj:`None`.
    """

    def child_get_property(self, child, property_name, value=None):
        """child_get_property(child, property_name, value=None)

        :param child:
            a widget which is a child of `self`
        :type child: :obj:`Gtk.Widget`

        :param property_name:
            the name of the property to get
        :type property_name: :obj:`str`

        :param value:
            Either :obj:`None` or a correctly initialized :obj:`GObject.Value`
        :type value: :obj:`GObject.Value` or :obj:`None`

        :returns: The Python value of the child property

        {{ docs }}
        """

        if value is None:
            prop = self.find_child_property(property_name)
            if prop is None:
                raise ValueError('Class "%s" does not contain child property "%s"' %
                                 (self, property_name))
            value = GObject.Value(prop.value_type)

        Gtk.Container.child_get_property(self, child, property_name, value)
        return value.get_value()

    def child_get(self, child, *prop_names):
        """Returns a list of child property values for the given names."""

        return [self.child_get_property(child, name) for name in prop_names]

    def child_set(self, child, **kwargs):
        """Set a child properties on the given child to key/value pairs."""

        for name, value in kwargs.items():
            name = name.replace('_', '-')
            self.child_set_property(child, name, value)


Container = override(Container)
__all__.append('Container')


class Editable(Gtk.Editable):

    def insert_text(self, text, position):
        """insert_text(self, text, position)

        :param new_text:
            the text to append
        :type new_text: :obj:`str`

        :param position:
            location of the position text will be inserted at
        :type position: :obj:`int`

        :returns:
            location of the position text will be inserted at
        :rtype: :obj:`int`

        Inserts `new_text` into the contents of the
        widget, at position `position`.

        Note that the position is in characters, not in bytes.
        """

        return super(Editable, self).insert_text(text, -1, position)

    get_selection_bounds = strip_boolean_result(Gtk.Editable.get_selection_bounds, fail_ret=())
    """
    :returns:
        An empty tuple if no area is selected or a tuple containing:

        :start_pos: the starting position
        :end_pos: the end position

    :rtype: (**start_pos**: :obj:`int`, **end_pos**: :obj:`int`) or ``()``

    Retrieves the selection bound of the editable. start_pos will be filled
    with the start of the selection and `end_pos` with end. If no text was
    selected an empty tuple will be returned.

    Note that positions are specified in characters, not bytes.
    """


Editable = override(Editable)
__all__.append("Editable")


class Action(Gtk.Action):
    __init__ = deprecated_init(Gtk.Action.__init__,
                               arg_names=('name', 'label', 'tooltip', 'stock_id'),
                               category=PyGTKDeprecationWarning)

Action = override(Action)
__all__.append("Action")


class RadioAction(Gtk.RadioAction):
    __init__ = deprecated_init(Gtk.RadioAction.__init__,
                               arg_names=('name', 'label', 'tooltip', 'stock_id', 'value'),
                               category=PyGTKDeprecationWarning)

RadioAction = override(RadioAction)
__all__.append("RadioAction")


class ActionGroup(Gtk.ActionGroup):
    __init__ = deprecated_init(Gtk.ActionGroup.__init__,
                               arg_names=('name',),
                               category=PyGTKDeprecationWarning)

    def add_actions(self, entries, user_data=None):
        """
        The add_actions() method is a convenience method that creates a number
        of gtk.Action  objects based on the information in the list of action
        entry tuples contained in entries and adds them to the action group.
        The entry tuples can vary in size from one to six items with the
        following information:

            * The name of the action. Must be specified.
            * The stock id for the action. Optional with a default value of None
              if a label is specified.
            * The label for the action. This field should typically be marked
              for translation, see the set_translation_domain() method. Optional
              with a default value of None if a stock id is specified.
            * The accelerator for the action, in the format understood by the
              gtk.accelerator_parse() function. Optional with a default value of
              None.
            * The tooltip for the action. This field should typically be marked
              for translation, see the set_translation_domain() method. Optional
              with a default value of None.
            * The callback function invoked when the action is activated.
              Optional with a default value of None.

        The "activate" signals of the actions are connected to the callbacks and
        their accel paths are set to <Actions>/group-name/action-name.
        """
        try:
            iter(entries)
        except (TypeError):
            raise TypeError('entries must be iterable')

        def _process_action(name, stock_id=None, label=None, accelerator=None, tooltip=None, callback=None):
            action = Action(name=name, label=label, tooltip=tooltip, stock_id=stock_id)
            if callback is not None:
                if user_data is None:
                    action.connect('activate', callback)
                else:
                    action.connect('activate', callback, user_data)

            self.add_action_with_accel(action, accelerator)

        for e in entries:
            # using inner function above since entries can leave out optional arguments
            _process_action(*e)

    def add_toggle_actions(self, entries, user_data=None):
        """
        The add_toggle_actions() method is a convenience method that creates a
        number of gtk.ToggleAction objects based on the information in the list
        of action entry tuples contained in entries and adds them to the action
        group. The toggle action entry tuples can vary in size from one to seven
        items with the following information:

            * The name of the action. Must be specified.
            * The stock id for the action. Optional with a default value of None
              if a label is specified.
            * The label for the action. This field should typically be marked
              for translation, see the set_translation_domain() method. Optional
              with a default value of None if a stock id is specified.
            * The accelerator for the action, in the format understood by the
              gtk.accelerator_parse() function. Optional with a default value of
              None.
            * The tooltip for the action. This field should typically be marked
              for translation, see the set_translation_domain() method. Optional
              with a default value of None.
            * The callback function invoked when the action is activated.
              Optional with a default value of None.
            * A flag indicating whether the toggle action is active. Optional
              with a default value of False.

        The "activate" signals of the actions are connected to the callbacks and
        their accel paths are set to <Actions>/group-name/action-name.
        """

        try:
            iter(entries)
        except (TypeError):
            raise TypeError('entries must be iterable')

        def _process_action(name, stock_id=None, label=None, accelerator=None, tooltip=None, callback=None, is_active=False):
            action = Gtk.ToggleAction(name=name, label=label, tooltip=tooltip, stock_id=stock_id)
            action.set_active(is_active)
            if callback is not None:
                if user_data is None:
                    action.connect('activate', callback)
                else:
                    action.connect('activate', callback, user_data)

            self.add_action_with_accel(action, accelerator)

        for e in entries:
            # using inner function above since entries can leave out optional arguments
            _process_action(*e)

    def add_radio_actions(self, entries, value=None, on_change=None, user_data=None):
        """
        The add_radio_actions() method is a convenience method that creates a
        number of gtk.RadioAction objects based on the information in the list
        of action entry tuples contained in entries and adds them to the action
        group. The entry tuples can vary in size from one to six items with the
        following information:

            * The name of the action. Must be specified.
            * The stock id for the action. Optional with a default value of None
              if a label is specified.
            * The label for the action. This field should typically be marked
              for translation, see the set_translation_domain() method. Optional
              with a default value of None if a stock id is specified.
            * The accelerator for the action, in the format understood by the
              gtk.accelerator_parse() function. Optional with a default value of
              None.
            * The tooltip for the action. This field should typically be marked
              for translation, see the set_translation_domain() method. Optional
              with a default value of None.
            * The value to set on the radio action. Optional with a default
              value of 0. Should be specified in applications.

        The value parameter specifies the radio action that should be set
        active. The "changed" signal of the first radio action is connected to
        the on_change callback (if specified and not None) and the accel paths
        of the actions are set to <Actions>/group-name/action-name.
        """
        try:
            iter(entries)
        except (TypeError):
            raise TypeError('entries must be iterable')

        first_action = None

        def _process_action(group_source, name, stock_id=None, label=None, accelerator=None, tooltip=None, entry_value=0):
            action = RadioAction(name=name, label=label, tooltip=tooltip, stock_id=stock_id, value=entry_value)

            # FIXME: join_group is a patch to Gtk+ 3.0
            #        otherwise we can't effectively add radio actions to a
            #        group.  Should we depend on 3.0 and error out here
            #        or should we offer the functionality via a compat
            #        C module?
            if hasattr(action, 'join_group'):
                action.join_group(group_source)

            if value == entry_value:
                action.set_active(True)

            self.add_action_with_accel(action, accelerator)
            return action

        for e in entries:
            # using inner function above since entries can leave out optional arguments
            action = _process_action(first_action, *e)
            if first_action is None:
                first_action = action

        if first_action is not None and on_change is not None:
            if user_data is None:
                first_action.connect('changed', on_change)
            else:
                first_action.connect('changed', on_change, user_data)

ActionGroup = override(ActionGroup)
__all__.append('ActionGroup')


class UIManager(Gtk.UIManager):
    def add_ui_from_string(self, buffer, length=-1):
        """add_ui_from_string(buffer, length=-1)

        {{ all }}
        """

        return Gtk.UIManager.add_ui_from_string(self, buffer, length)

    def insert_action_group(self, action_group, pos=-1):
        return Gtk.UIManager.insert_action_group(self, action_group, pos)

UIManager = override(UIManager)
__all__.append('UIManager')


class ComboBox(Gtk.ComboBox, Container):
    get_active_iter = strip_boolean_result(Gtk.ComboBox.get_active_iter)
    """
    :returns: a :obj:`Gtk.TreeIter` or :obj:`None` if there is no active item
    :rtype: :obj:`Gtk.TreeIter` or :obj:`None`

    Returns the `iter` for the current active item, if it exists.
    """

ComboBox = override(ComboBox)
__all__.append('ComboBox')


class Box(Gtk.Box):
    __init__ = deprecated_init(Gtk.Box.__init__,
                               arg_names=('homogeneous', 'spacing'),
                               category=PyGTKDeprecationWarning)

Box = override(Box)
__all__.append('Box')


class SizeGroup(Gtk.SizeGroup):
    __init__ = deprecated_init(Gtk.SizeGroup.__init__,
                               arg_names=('mode',),
                               deprecated_defaults={'mode': Gtk.SizeGroupMode.VERTICAL},
                               category=PyGTKDeprecationWarning)

SizeGroup = override(SizeGroup)
__all__.append('SizeGroup')


class MenuItem(Gtk.MenuItem):
    __init__ = deprecated_init(Gtk.MenuItem.__init__,
                               arg_names=('label',),
                               category=PyGTKDeprecationWarning)

MenuItem = override(MenuItem)
__all__.append('MenuItem')


class Builder(Gtk.Builder):
    def connect_signals(self, obj_or_map):
        """connect_signals(self, obj_or_map)

        Connect signals specified by this builder to a name, handler mapping.

        Connect signal, name, and handler sets specified in the builder with
        the given mapping "obj_or_map". The handler/value aspect of the mapping
        can also contain a tuple in the form of (handler [,arg1 [,argN]])
        allowing for extra arguments to be passed to the handler. For example:

        .. code-block:: python

            builder.connect_signals({'on_clicked': (on_clicked, arg1, arg2)})
        """
        self.connect_signals_full(_builder_connect_callback, obj_or_map)

    def add_from_string(self, buffer, length=-1):
        """add_from_string(buffer, length=-1)

        {{ all }}
        """

        return Gtk.Builder.add_from_string(self, buffer, length)

    def add_objects_from_string(self, buffer, object_ids):
        """add_objects_from_string(buffer, object_ids)

        :param buffer: the string to parse
        :type buffer: :obj:`str`
        :param object_ids: array of objects to build
        :type object_ids: [:obj:`str`]

        :raises: :class:`GLib.Error`

        :returns: A positive value on success, 0 if an error occurred
        :rtype: :obj:`int`

        {{ docs }}
        """

        length = -1
        return Gtk.Builder.add_objects_from_string(self, buffer, length, object_ids)

Builder = override(Builder)
__all__.append('Builder')


# NOTE: This must come before any other Window/Dialog subclassing, to ensure
# that we have a correct inheritance hierarchy.


class Window(Gtk.Window):
    __init__ = deprecated_init(Gtk.Window.__init__,
                               arg_names=('type',),
                               category=PyGTKDeprecationWarning)

Window = override(Window)
__all__.append('Window')


class Dialog(Gtk.Dialog, Container):
    _old_arg_names = ('title', 'parent', 'flags', 'buttons', '_buttons_property')
    _init = deprecated_init(Gtk.Dialog.__init__,
                            arg_names=('title', 'transient_for', 'flags',
                                       'add_buttons', 'buttons'),
                            ignore=('flags', 'add_buttons'),
                            deprecated_aliases={'transient_for': 'parent',
                                                'buttons': '_buttons_property'},
                            category=PyGTKDeprecationWarning)

    def __init__(self, *args, **kwargs):

        new_kwargs = kwargs.copy()
        old_kwargs = dict(zip(self._old_arg_names, args))
        old_kwargs.update(kwargs)

        # Increment the warning stacklevel for sub-classes which implement their own __init__.
        stacklevel = 2
        if self.__class__ != Dialog and self.__class__.__init__ != Dialog.__init__:
            stacklevel += 1

        # buttons was overloaded by PyGtk but is needed for Gtk.MessageDialog
        # as a pass through, so type check the argument and give a deprecation
        # when it is not of type Gtk.ButtonsType
        add_buttons = old_kwargs.get('buttons', None)
        if add_buttons is not None and not isinstance(add_buttons, Gtk.ButtonsType):
            warnings.warn('The "buttons" argument must be a Gtk.ButtonsType enum value. '
                          'Please use the "add_buttons" method for adding buttons. '
                          'See: https://wiki.gnome.org/PyGObject/InitializerDeprecations',
                          PyGTKDeprecationWarning, stacklevel=stacklevel)
            if 'buttons' in new_kwargs:
                del new_kwargs['buttons']
        else:
            add_buttons = None

        flags = old_kwargs.get('flags', 0)
        if flags:
            warnings.warn('The "flags" argument for dialog construction is deprecated. '
                          'Please use initializer keywords: modal=True and/or destroy_with_parent=True. '
                          'See: https://wiki.gnome.org/PyGObject/InitializerDeprecations',
                          PyGTKDeprecationWarning, stacklevel=stacklevel)

            if flags & Gtk.DialogFlags.MODAL:
                new_kwargs['modal'] = True

            if flags & Gtk.DialogFlags.DESTROY_WITH_PARENT:
                new_kwargs['destroy_with_parent'] = True

        self._init(*args, **new_kwargs)

        if add_buttons:
            self.add_buttons(*add_buttons)

    action_area = property(lambda dialog: dialog.get_action_area())
    vbox = property(lambda dialog: dialog.get_content_area())

    def add_buttons(self, *args):
        """add_buttons(*args)

        The add_buttons() method adds several buttons to the Gtk.Dialog using
        the button data passed as arguments to the method. This method is the
        same as calling the Gtk.Dialog.add_button() repeatedly. The button data
        pairs - button text (or stock ID) and a response ID integer are passed
        individually. For example:

        .. code-block:: python

            dialog.add_buttons(Gtk.STOCK_OPEN, 42, "Close", Gtk.ResponseType.CLOSE)

        will add "Open" and "Close" buttons to dialog.
        """
        def _button(b):
            while b:
                t, r = b[0:2]
                b = b[2:]
                yield t, r

        try:
            for text, response in _button(args):
                self.add_button(text, response)
        except (IndexError):
            raise TypeError('Must pass an even number of arguments')

Dialog = override(Dialog)
__all__.append('Dialog')


class MessageDialog(Gtk.MessageDialog, Dialog):
    __init__ = deprecated_init(Gtk.MessageDialog.__init__,
                               arg_names=('parent', 'flags', 'message_type',
                                          'buttons', 'message_format'),
                               deprecated_aliases={'text': 'message_format',
                                                   'message_type': 'type'},
                               category=PyGTKDeprecationWarning)

    def format_secondary_text(self, message_format):
        self.set_property('secondary-use-markup', False)
        self.set_property('secondary-text', message_format)

    def format_secondary_markup(self, message_format):
        self.set_property('secondary-use-markup', True)
        self.set_property('secondary-text', message_format)

MessageDialog = override(MessageDialog)
__all__.append('MessageDialog')


class ColorSelectionDialog(Gtk.ColorSelectionDialog):
    __init__ = deprecated_init(Gtk.ColorSelectionDialog.__init__,
                               arg_names=('title',),
                               category=PyGTKDeprecationWarning)

ColorSelectionDialog = override(ColorSelectionDialog)
__all__.append('ColorSelectionDialog')


class FileChooserDialog(Gtk.FileChooserDialog):
    __init__ = deprecated_init(Gtk.FileChooserDialog.__init__,
                               arg_names=('title', 'parent', 'action', 'buttons'),
                               category=PyGTKDeprecationWarning)

FileChooserDialog = override(FileChooserDialog)
__all__.append('FileChooserDialog')


class FontSelectionDialog(Gtk.FontSelectionDialog):
    __init__ = deprecated_init(Gtk.FontSelectionDialog.__init__,
                               arg_names=('title',),
                               category=PyGTKDeprecationWarning)

FontSelectionDialog = override(FontSelectionDialog)
__all__.append('FontSelectionDialog')


class RecentChooserDialog(Gtk.RecentChooserDialog):
    # Note, the "manager" keyword must work across the entire 3.x series because
    # "recent_manager" is not backwards compatible with PyGObject versions prior to 3.10.
    __init__ = deprecated_init(Gtk.RecentChooserDialog.__init__,
                               arg_names=('title', 'parent', 'recent_manager', 'buttons'),
                               deprecated_aliases={'recent_manager': 'manager'},
                               category=PyGTKDeprecationWarning)

RecentChooserDialog = override(RecentChooserDialog)
__all__.append('RecentChooserDialog')


class IconView(Gtk.IconView):
    __init__ = deprecated_init(Gtk.IconView.__init__,
                               arg_names=('model',),
                               category=PyGTKDeprecationWarning)

    get_item_at_pos = strip_boolean_result(Gtk.IconView.get_item_at_pos)
    """
    :param x: The x position to be identified
    :type x: :obj:`int`

    :param y: The y position to be identified
    :type y: :obj:`int`

    :returns:
        If not item exists at the specified position returns :obj:`None`,
        otherwise a tuple containing:

        :path: The path
        :cell: The renderer responsible for the cell at (`x`, `y`)

    :rtype: (**path**: :obj:`Gtk.TreePath`, **cell**: :obj:`Gtk.CellRenderer`) or :obj:`None`

    {{ docs }}
    """

    get_visible_range = strip_boolean_result(Gtk.IconView.get_visible_range)
    """
    :returns:
        Returns :obj:`None` if there is no visible range or a tuple
        containing:

        :start_path: Start of region
        :end_path: End of region

    :rtype: (**start_path**: :obj:`Gtk.TreePath`, **end_path**: :obj:`Gtk.TreePath`) or :obj:`None`

    {{ docs }}
    """

    get_dest_item_at_pos = strip_boolean_result(Gtk.IconView.get_dest_item_at_pos)
    """
    :param drag_x:
        the position to determine the destination item for
    :type drag_x: :obj:`int`

    :param drag_y:
        the position to determine the destination item for
    :type drag_y: :obj:`int`

    :returns:
        If there is no item at the given position return :obj:`None` otherwise
        a tuple containing:

        :path: The path of the item
        :pos: The drop position

    :rtype: (**path**: :obj:`Gtk.TreePath`, **pos**: :obj:`Gtk.IconViewDropPosition`) or :obj:`None`

    {{ docs }}
    """

IconView = override(IconView)
__all__.append('IconView')


class ToolButton(Gtk.ToolButton):
    __init__ = deprecated_init(Gtk.ToolButton.__init__,
                               arg_names=('stock_id',),
                               category=PyGTKDeprecationWarning)

ToolButton = override(ToolButton)
__all__.append('ToolButton')


class IMContext(Gtk.IMContext):
    get_surrounding = strip_boolean_result(Gtk.IMContext.get_surrounding)
    """
    :returns:
        :obj:`None` if no surrounding text was provided; otherwise a tuple
        containing:

        :text: text holding context around the insertion point.
        :cursor_index: byte index of the insertion cursor within `text`

    :rtype: (**text**: :obj:`str`, **cursor_index**: :obj:`int`) or :obj:`None`

    {{ docs }}
    """

IMContext = override(IMContext)
__all__.append('IMContext')


class RecentInfo(Gtk.RecentInfo):
    get_application_info = strip_boolean_result(Gtk.RecentInfo.get_application_info)
    """
    :param app_name: the name of the application that has registered this item
    :type app_name: :obj:`str`

    :returns:
        :obj:`None` if no application with `app_name` has registered this
        resource inside the recently used list otherwise a tuple containing:

        :app_exec: string containing the command line
        :count: the number of times this item was registered
        :time_: the timestamp this item was last registered for this application

    :rtype: (**app_exec**: :obj:`str`, **count**: :obj:`int`, **time_**: :obj:`int`) or :obj:`None`

    {{ docs }}
    """

RecentInfo = override(RecentInfo)
__all__.append('RecentInfo')


class TextBuffer(Gtk.TextBuffer):
    def _get_or_create_tag_table(self):
        table = self.get_tag_table()
        if table is None:
            table = Gtk.TextTagTable()
            self.set_tag_table(table)

        return table

    def create_tag(self, tag_name=None, **properties):
        """Creates a tag and adds it to the tag table of the TextBuffer.

        :param str tag_name:
            Name of the new tag, or None
        :param **properties:
            Keyword list of properties and their values
        :returns:
            A new tag.

        This is equivalent to creating a Gtk.TextTag and then adding the
        tag to the buffer's tag table. The returned tag is owned by
        the buffer's tag table.

        If ``tag_name`` is None, the tag is anonymous.

        If ``tag_name`` is not None, a tag called ``tag_name`` must not already
        exist in the tag table for this buffer.

        Properties are passed as a keyword list of names and values (e.g.
        foreground='DodgerBlue', weight=Pango.Weight.BOLD)
        """

        tag = Gtk.TextTag(name=tag_name, **properties)
        self._get_or_create_tag_table().add(tag)
        return tag

    def create_mark(self, mark_name, where, left_gravity=False):
        return Gtk.TextBuffer.create_mark(self, mark_name, where, left_gravity)

    def set_text(self, text, length=-1):
        """set_text(text, length=-1)

        {{ all }}
        """

        Gtk.TextBuffer.set_text(self, text, length)

    def insert(self, iter, text, length=-1):
        """insert(iter, text, length=-1)

        {{ all }}
        """

        Gtk.TextBuffer.insert(self, iter, text, length)

    def insert_with_tags(self, iter, text, *tags):
        start_offset = iter.get_offset()
        self.insert(iter, text)

        if not tags:
            return

        start = self.get_iter_at_offset(start_offset)

        for tag in tags:
            self.apply_tag(tag, start, iter)

    def insert_with_tags_by_name(self, iter, text, *tags):
        if not tags:
            return

        tag_objs = []

        for tag in tags:
            tag_obj = self.get_tag_table().lookup(tag)
            if not tag_obj:
                raise ValueError('unknown text tag: %s' % tag)
            tag_objs.append(tag_obj)

        self.insert_with_tags(iter, text, *tag_objs)

    def insert_at_cursor(self, text, length=-1):
        if not isinstance(text, _basestring):
            raise TypeError('text must be a string, not %s' % type(text))

        Gtk.TextBuffer.insert_at_cursor(self, text, length)

    get_selection_bounds = strip_boolean_result(Gtk.TextBuffer.get_selection_bounds, fail_ret=())
    """
    :returns:
        If there is no selection returns an empty tuple otherwise a tuple
        containing:

        :start: selection start
        :end: selection end

    :rtype: (**start**: :obj:`Gtk.TextIter`, **end**: :obj:`Gtk.TextIter`) or :obj:`None`

    {{ docs }}
    """

TextBuffer = override(TextBuffer)
__all__.append('TextBuffer')


class TextIter(Gtk.TextIter):
    forward_search = strip_boolean_result(Gtk.TextIter.forward_search)
    """
    :param str: a search string
    :type str: :obj:`str`

    :param flags: flags affecting how the search is done
    :type flags: :obj:`Gtk.TextSearchFlags`

    :param limit: location of last possible `match_end`, or :obj:`None` for the end of the buffer
    :type limit: :obj:`Gtk.TextIter` or :obj:`None`

    :returns:
        If no match was found returns :obj:`None` otherwise a tuple containing:

        :match_start: start of match
        :match_end: end of match

    :rtype: (**match\_start**: :obj:`Gtk.TextIter`, **match\_end**: :obj:`Gtk.TextIter`) or :obj:`None`

    {{ docs }}
    """

    backward_search = strip_boolean_result(Gtk.TextIter.backward_search)
    """
    :param str: search string
    :type str: :obj:`str`

    :param flags: bitmask of flags affecting the search
    :type flags: :obj:`Gtk.TextSearchFlags`

    :param limit: location of last possible `match_start`, or :obj:`None` for start of buffer
    :type limit: :obj:`Gtk.TextIter` or :obj:`None`

    :returns:
        :obj:`None` if not match was found otherwise a tuple containing:

        :match_start: start of match
        :match_end: end of match

    :rtype: (**match_start**: :obj:`Gtk.TextIter`, **match_end**: :obj:`Gtk.TextIter`) or :obj:`None`

    {{ docs }}
    """

TextIter = override(TextIter)
__all__.append('TextIter')


class TreeModel(Gtk.TreeModel):
    """
    .. note::

        Implements ``__len__``, ``__bool__``, ``__nonzero__``, ``__iter__``,
        ``__getitem__``, ``__setitem__`` and ``__delitem__``.

        Iterating over a :obj:`Gtk.TreeModel` yields
        :obj:`Gtk.TreeModelRow` instances.

        ``__getitem__`` returns a :obj:`Gtk.TreeModelRow`.

    {{ all }}
    """

    def __len__(self):
        return self.iter_n_children(None)

    def __bool__(self):
        return True

    # alias for Python 2.x object protocol
    __nonzero__ = __bool__

    def _getiter(self, key):
        if isinstance(key, Gtk.TreeIter):
            return key
        elif isinstance(key, int) and key < 0:
            index = len(self) + key
            if index < 0:
                raise IndexError("row index is out of bounds: %d" % key)
            try:
                aiter = self.get_iter(index)
            except ValueError:
                raise IndexError("could not find tree path '%s'" % key)
            return aiter
        else:
            try:
                aiter = self.get_iter(key)
            except ValueError:
                raise IndexError("could not find tree path '%s'" % key)
            return aiter

    def _coerce_path(self, path):
        if isinstance(path, Gtk.TreePath):
            return path
        else:
            return TreePath(path)

    def __getitem__(self, key):
        aiter = self._getiter(key)
        return TreeModelRow(self, aiter)

    def __setitem__(self, key, value):
        row = self[key]
        self.set_row(row.iter, value)

    def __delitem__(self, key):
        aiter = self._getiter(key)
        self.remove(aiter)

    def __iter__(self):
        return TreeModelRowIter(self, self.get_iter_first())

    get_iter_first = strip_boolean_result(Gtk.TreeModel.get_iter_first)
    """
    :returns: :obj:`Gtk.TreeIter` or :obj:`None` if the tree is empty.
    :rtype: :obj:`Gtk.TreeIter` or :obj:`None`

    {{ docs }}
    """

    iter_children = strip_boolean_result(Gtk.TreeModel.iter_children)
    """
    :param parent: the :obj:`Gtk.TreeIter`-struct, or :obj:`None`
    :type parent: :obj:`Gtk.TreeIter` or :obj:`None`

    :returns: :obj:`Gtk.TreeIter` or :obj:`None`
    :rtype: :obj:`Gtk.TreeIter` or :obj:`None`

    Sets `iter` to point to the first child of `parent`.
    If `parent` has no children, :obj:`None` is returned.
    If `parent` is :obj:`None` returns the first node, equivalent to
    ``Gtk.TreeModel.iter_first()``.
    """

    iter_nth_child = strip_boolean_result(Gtk.TreeModel.iter_nth_child)
    """
    :param parent: the :obj:`Gtk.TreeIter`-struct to get the child from, or :obj:`None`.
    :type parent: :obj:`Gtk.TreeIter` or :obj:`None`

    :param n: the index of the desired child
    :type n: :obj:`int`

    :returns: :obj:`Gtk.TreeIter` if `parent` has an `n`-th child otherwise :obj:`None`
    :rtype: :obj:`Gtk.TreeIter` or :obj:`None`

    Returns child `iter` of `parent`, using the given index.

    The first index is 0. If `n` is too big, or `parent` has no children,
    :obj:`None` is returned. `parent` will remain a valid node after this
    function has been called. As a special case, if `parent` is :obj:`None`,
    then the `n`-th root node is set.
    """

    iter_parent = strip_boolean_result(Gtk.TreeModel.iter_parent)
    """
    :param child: the :obj:`Gtk.TreeIter`-struct
    :type child: :obj:`Gtk.TreeIter`

    :returns: :obj:`Gtk.TreeIter` or :obj:`None` if `child` has a parent.
    :rtype:  :obj:`Gtk.TreeIter` or :obj`None`

    Returns iter of the parent of `child`.

    If `child` is at the toplevel, and doesn't have a parent, then :obj:`None`
    is returned. `child` will remain a valid node after this function has been
    called.
    """

    get_iter_from_string = strip_boolean_result(Gtk.TreeModel.get_iter_from_string,
                                                ValueError, 'invalid tree path')
    """
    :param path_string: a string representation of a :obj:`Gtk.TreePath`-struct
    :type path_string: :obj:`str`

    :raises: :class:`ValueError` if an iterator pointing to `path_string` does not exist.
    :returns: a :obj:`Gtk.TreeIter`
    :rtype: :obj:`Gtk.TreeIter`

    Returns a valid iterator pointing to `path_string`, if it
    exists. Otherwise raises :class:`ValueError`
    """

    def get_iter(self, path):
        """
        :param path: the :obj:`Gtk.TreePath`-struct
        :type path: :obj:`Gtk.TreePath`

        :raises: :class:`ValueError` if `path` doesn't exist
        :returns: a :obj:`Gtk.TreeIter`
        :rtype: :obj:`Gtk.TreeIter`

        Returns an iterator pointing to `path`. If `path` does not exist
        :class:`ValueError` is raised.
        """

        path = self._coerce_path(path)
        success, aiter = super(TreeModel, self).get_iter(path)
        if not success:
            raise ValueError("invalid tree path '%s'" % path)
        return aiter

    def iter_next(self, iter):
        """
        :param iter: the :obj:`Gtk.TreeIter`-struct
        :type iter: :obj:`Gtk.TreeIter`

        :returns: a :obj:`Gtk.TreeIter` or :obj:`None`
        :rtype: :obj:`Gtk.TreeIter` or :obj:`None`

        Returns an iterator pointing to the node following `iter` at the
        current level.

        If there is no next `iter`, :obj:`None` is returned.
        """

        next_iter = iter.copy()
        success = super(TreeModel, self).iter_next(next_iter)
        if success:
            return next_iter

    def iter_previous(self, iter):
        """
        :param iter: the :obj:`Gtk.TreeIter`-struct
        :type iter: :obj:`Gtk.TreeIter`

        :returns: a :obj:`Gtk.TreeIter` or :obj:`None`
        :rtype: :obj:`Gtk.TreeIter` or :obj:`None`

        Returns an iterator pointing to the previous node at the current level.

        If there is no previous `iter`, :obj:`None` is returned.
        """

        prev_iter = iter.copy()
        success = super(TreeModel, self).iter_previous(prev_iter)
        if success:
            return prev_iter

    def _convert_row(self, row):
        # TODO: Accept a dictionary for row
        # model.append(None,{COLUMN_ICON: icon, COLUMN_NAME: name})
        if isinstance(row, str):
            raise TypeError('Expected a list or tuple, but got str')

        n_columns = self.get_n_columns()
        if len(row) != n_columns:
            raise ValueError('row sequence has the incorrect number of elements')

        result = []
        columns = []
        for cur_col, value in enumerate(row):
            # do not try to set None values, they are causing warnings
            if value is None:
                continue
            result.append(self._convert_value(cur_col, value))
            columns.append(cur_col)
        return (result, columns)

    def set_row(self, treeiter, row):
        """
        :param treeiter: the :obj:`Gtk.TreeIter`
        :type treeiter: :obj:`Gtk.TreeIter`

        :param row: a list of values for each column
        :type row: [:obj:`object`]

        Sets all values of a row pointed to by `treeiter` from a list of
        values passes as `row`. The length of the row has to match the number
        of columns of the model. :obj:`None` in `row` means the value will be
        skipped and not set.

        Also see :obj:`Gtk.ListStore.set_value`\() and
        :obj:`Gtk.TreeStore.set_value`\()
        """

        converted_row, columns = self._convert_row(row)
        for column in columns:
            value = row[column]
            if value is None:
                continue  # None means skip this row

            self.set_value(treeiter, column, value)

    def _convert_value(self, column, value):
        '''Convert value to a GObject.Value of the expected type'''

        if isinstance(value, GObject.Value):
            return value
        return GObject.Value(self.get_column_type(column), value)

    def get(self, treeiter, *columns):
        """
        :param treeiter: the :obj:`Gtk.TreeIter`
        :type treeiter: :obj:`Gtk.TreeIter`

        :param \\*columns: a list of column indices to fetch
        :type columns: (:obj:`int`)

        Returns a tuple of all values specified by their indices in `columns`
        in the order the indices are contained in `columns`

        Also see :obj:`Gtk.TreeStore.get_value`\()
        """

        n_columns = self.get_n_columns()

        values = []
        for col in columns:
            if not isinstance(col, int):
                raise TypeError("column numbers must be ints")

            if col < 0 or col >= n_columns:
                raise ValueError("column number is out of range")

            values.append(self.get_value(treeiter, col))

        return tuple(values)

    #
    # Signals supporting python iterables as tree paths
    #
    def row_changed(self, path, iter):
        return super(TreeModel, self).row_changed(self._coerce_path(path), iter)

    def row_inserted(self, path, iter):
        return super(TreeModel, self).row_inserted(self._coerce_path(path), iter)

    def row_has_child_toggled(self, path, iter):
        return super(TreeModel, self).row_has_child_toggled(self._coerce_path(path),
                                                            iter)

    def row_deleted(self, path):
        return super(TreeModel, self).row_deleted(self._coerce_path(path))

    def rows_reordered(self, path, iter, new_order):
        return super(TreeModel, self).rows_reordered(self._coerce_path(path),
                                                     iter, new_order)


TreeModel = override(TreeModel)
__all__.append('TreeModel')


class TreeSortable(Gtk.TreeSortable, ):

    get_sort_column_id = strip_boolean_result(Gtk.TreeSortable.get_sort_column_id, fail_ret=(None, None))
    """
    :returns:
        `(None, None)` if the sort column is one of the special sort
        column ids. Otherwise a tuple containing:

        :sort_column_id: The sort column id
        :order: The :obj:`Gtk.SortType`

    :rtype: (**sort_column_id**: :obj:`int`, **order**: :obj:`Gtk.SortType`) or (:obj:`None`, :obj:`None`)

    Returns `sort_column_id` and `order` with the current sort column and the
    order. It returns (:obj:`None`, :obj:`None`) if the `sort_column_id` is
    :obj:`Gtk.TREE_SORTABLE_DEFAULT_SORT_COLUMN_ID` or
    :obj:`Gtk.TREE_SORTABLE_UNSORTED_SORT_COLUMN_ID`.
    """

    def set_sort_func(self, sort_column_id, sort_func, user_data=None):
        super(TreeSortable, self).set_sort_func(sort_column_id, sort_func, user_data)

    def set_default_sort_func(self, sort_func, user_data=None):
        super(TreeSortable, self).set_default_sort_func(sort_func, user_data)

TreeSortable = override(TreeSortable)
__all__.append('TreeSortable')


class TreeModelSort(Gtk.TreeModelSort):
    __init__ = deprecated_init(Gtk.TreeModelSort.__init__,
                               arg_names=('model',),
                               category=PyGTKDeprecationWarning)

TreeModelSort = override(TreeModelSort)
__all__.append('TreeModelSort')


class ListStore(Gtk.ListStore, TreeModel, TreeSortable):
    def __init__(self, *column_types):
        Gtk.ListStore.__init__(self)
        self.set_column_types(column_types)

    def _do_insert(self, position, row):
        if row is not None:
            row, columns = self._convert_row(row)
            treeiter = self.insert_with_valuesv(position, columns, row)
        else:
            treeiter = Gtk.ListStore.insert(self, position)

        return treeiter

    def append(self, row=None):
        """append(row=None)

        :param row: a list of values to apply to the newly append row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: :obj:`Gtk.TreeIter` of the appended row
        :rtype: :obj:`Gtk.TreeIter`

        If `row` is :obj:`None` the appended row will be empty and to fill in
        values you need to call :obj:`Gtk.ListStore.set`\() or
        :obj:`Gtk.ListStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row .
        """

        if row:
            return self._do_insert(-1, row)
        # gtk_list_store_insert() does not know about the "position == -1"
        # case, so use append() here
        else:
            return Gtk.ListStore.append(self)

    def prepend(self, row=None):
        """prepend(row=None)

        :param row: a list of values to apply to the newly prepend row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: :obj:`Gtk.TreeIter` of the prepended row
        :rtype: :obj:`Gtk.TreeIter`

        If `row` is :obj:`None` the prepended row will be empty and to fill in
        values you need to call :obj:`Gtk.ListStore.set`\() or
        :obj:`Gtk.ListStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.
        """

        return self._do_insert(0, row)

    def insert(self, position, row=None):
        """insert(position, row=None)

        :param position: the position the new row will be inserted at
        :type position: :obj:`int`

        :param row: a list of values to apply to the newly inserted row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: :obj:`Gtk.TreeIter` of the inserted row
        :rtype: :obj:`Gtk.TreeIter`

        If `row` is :obj:`None` the inserted row will be empty and to fill in
        values you need to call :obj:`Gtk.ListStore.set`\() or
        :obj:`Gtk.ListStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.

        If `position` is -1 or is larger than the number of rows on the list,
        then the new row will be appended to the list.
        """

        return self._do_insert(position, row)

    # FIXME: sends two signals; check if this can use an atomic
    # insert_with_valuesv()

    def insert_before(self, sibling, row=None):
        """insert_before(sibling, row=None)

        :param sibling: A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type sibling: :obj:`Gtk.TreeIter` or :obj:`None`

        :param row: a list of values to apply to the newly inserted row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: :obj:`Gtk.TreeIter` pointing to the new row
        :rtype: :obj:`Gtk.TreeIter`

        Inserts a new row before `sibling`. If `sibling` is :obj:`None`, then
        the row will be appended to the end of the list.

        The row will be empty if `row` is :obj:`None. To fill in values, you
        need to call :obj:`Gtk.ListStore.set`\() or
        :obj:`Gtk.ListStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.
        """

        treeiter = Gtk.ListStore.insert_before(self, sibling)

        if row is not None:
            self.set_row(treeiter, row)

        return treeiter

    # FIXME: sends two signals; check if this can use an atomic
    # insert_with_valuesv()

    def insert_after(self, sibling, row=None):
        """insert_after(sibling, row=None)

        :param sibling: A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type sibling: :obj:`Gtk.TreeIter` or :obj:`None`

        :param row: a list of values to apply to the newly inserted row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: :obj:`Gtk.TreeIter` pointing to the new row
        :rtype: :obj:`Gtk.TreeIter`

        Inserts a new row after `sibling`. If `sibling` is :obj:`None`, then
        the row will be prepended to the beginning of the list.

        The row will be empty if `row` is :obj:`None. To fill in values, you
        need to call :obj:`Gtk.ListStore.set`\() or
        :obj:`Gtk.ListStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.
        """

        treeiter = Gtk.ListStore.insert_after(self, sibling)

        if row is not None:
            self.set_row(treeiter, row)

        return treeiter

    def set_value(self, treeiter, column, value):
        """
        {{ all }}

        `value` can also be a Python value and will be converted to a
        :obj:`GObject.Value` using the corresponding column type (See
        :obj:`Gtk.ListStore.set_column_types`\()).
        """

        value = self._convert_value(column, value)
        Gtk.ListStore.set_value(self, treeiter, column, value)

    def set(self, treeiter, *args):
        def _set_lists(columns, values):
            if len(columns) != len(values):
                raise TypeError('The number of columns do not match the number of values')
            for col_num, val in zip(columns, values):
                if not isinstance(col_num, int):
                    raise TypeError('TypeError: Expected integer argument for column.')
                self.set_value(treeiter, col_num, val)

        if args:
            if isinstance(args[0], int):
                columns = args[::2]
                values = args[1::2]
                _set_lists(columns, values)
            elif isinstance(args[0], (tuple, list)):
                if len(args) != 2:
                    raise TypeError('Too many arguments')
                _set_lists(args[0], args[1])
            elif isinstance(args[0], dict):
                columns = args[0].keys()
                values = args[0].values()
                _set_lists(columns, values)
            else:
                raise TypeError('Argument list must be in the form of (column, value, ...), ((columns,...), (values, ...)) or {column: value}.  No -1 termination is needed.')

ListStore = override(ListStore)
__all__.append('ListStore')


class TreeModelRow(object):
    """A :obj:`Gtk.TreeModelRow` object represents a row in a
    :obj:`Gtk.TreeModel`. A :obj:`Gtk.TreeModelRow` is created by taking the
    mapping of a :obj:`Gtk.TreeModel`. For example::

        treemodelrow = liststore[0]
        treemodelrow = liststore[(0,)]
        treemodelrow = liststore['0']

    all create a :obj:`Gtk.TreeModelRow` for the first row in liststore. The
    :obj:`Gtk.TreeModelRow` implements some of the Python sequence protocol
    that makes the row behave like a sequence of objects. Specifically a tree
    model row has the capability of:

    * getting and setting column values,
    * returning a tuple or list containing the column values, and
    * getting the number of values in the row i.e. the number of columns

    For example to get and set the value in the second column of a row, you
    could do the following::

        value = treemodelrow[1]
        treemodelrow[1] = value

    You can use the Python len() function to get the number of columns in the
    row and you can retrieve all the column values as a list (tuple) using the
    Python list() (tuple()) function.

    The :obj:`Gtk.TreeModelRow` supports one method: the iterchildren() method
    that returns a :obj:`Gtk.TreeModelRowIter` for iterating over the children
    of the row.
    """

    def __init__(self, model, iter_or_path):
        if not isinstance(model, Gtk.TreeModel):
            raise TypeError("expected Gtk.TreeModel, %s found" % type(model).__name__)
        self.model = model
        if isinstance(iter_or_path, Gtk.TreePath):
            self.iter = model.get_iter(iter_or_path)
        elif isinstance(iter_or_path, Gtk.TreeIter):
            self.iter = iter_or_path
        else:
            raise TypeError("expected Gtk.TreeIter or Gtk.TreePath, \
                %s found" % type(iter_or_path).__name__)

    iter = None
    """A :obj:`Gtk.TreeIter` pointing at the row"""

    model = None
    """	The :obj:`Gtk.TreeModel` that the row is part of"""

    @property
    def path(self):
        """The tree path of the row"""

        return self.model.get_path(self.iter)

    @property
    def next(self):
        """	The next :obj:`Gtk.TreeModelRow` or None"""

        return self.get_next()

    @property
    def previous(self):
        """	The previous :obj:`Gtk.TreeModelRow` or None"""

        return self.get_previous()

    @property
    def parent(self):
        """The parent :obj:`Gtk.TreeModelRow` or htis row or None"""

        return self.get_parent()

    def get_next(self):
        """Returns the next :obj:`Gtk.TreeModelRow` or None"""

        next_iter = self.model.iter_next(self.iter)
        if next_iter:
            return TreeModelRow(self.model, next_iter)

    def get_previous(self):
        """Returns the previous :obj:`Gtk.TreeModelRow` or None"""

        prev_iter = self.model.iter_previous(self.iter)
        if prev_iter:
            return TreeModelRow(self.model, prev_iter)

    def get_parent(self):
        """Returns the parent :obj:`Gtk.TreeModelRow` or htis row or None"""

        parent_iter = self.model.iter_parent(self.iter)
        if parent_iter:
            return TreeModelRow(self.model, parent_iter)

    def __getitem__(self, key):
        if isinstance(key, int):
            if key >= self.model.get_n_columns():
                raise IndexError("column index is out of bounds: %d" % key)
            elif key < 0:
                key = self._convert_negative_index(key)
            return self.model.get_value(self.iter, key)
        elif isinstance(key, slice):
            start, stop, step = key.indices(self.model.get_n_columns())
            alist = []
            for i in range(start, stop, step):
                alist.append(self.model.get_value(self.iter, i))
            return alist
        else:
            raise TypeError("indices must be integers, not %s" % type(key).__name__)

    def __setitem__(self, key, value):
        if isinstance(key, int):
            if key >= self.model.get_n_columns():
                raise IndexError("column index is out of bounds: %d" % key)
            elif key < 0:
                key = self._convert_negative_index(key)
            self.model.set_value(self.iter, key, value)
        elif isinstance(key, slice):
            start, stop, step = key.indices(self.model.get_n_columns())
            indexList = range(start, stop, step)
            if len(indexList) != len(value):
                raise ValueError(
                    "attempt to assign sequence of size %d to slice of size %d"
                    % (len(value), len(indexList)))

            for i, v in enumerate(indexList):
                self.model.set_value(self.iter, v, value[i])
        else:
            raise TypeError("index must be an integer or slice, not %s" % type(key).__name__)

    def _convert_negative_index(self, index):
        new_index = self.model.get_n_columns() + index
        if new_index < 0:
            raise IndexError("column index is out of bounds: %d" % index)
        return new_index

    def iterchildren(self):
        """Returns a :obj:`Gtk.TreeModelRowIter` for the row's children"""

        child_iter = self.model.iter_children(self.iter)
        return TreeModelRowIter(self.model, child_iter)

__all__.append('TreeModelRow')


class TreeModelRowIter(object):
    """A :obj:`Gtk.TreeModelRowIter` is an object that implements the Python
    Iterator protocol. It provides the means to iterate over a set of
    :obj:`Gtk.TreeModelRow` objects in a :obj:`Gtk.TreeModel`. A
    :obj:`Gtk.TreeModelRowIter` is created by calling the Python iter()
    function on a :obj:`Gtk.TreeModel` object::

        treemodelrowiter = iter(treestore)

    or, calling the :obj:`Gtk.TreeModelRow.iterchildren`\() method to iterate
    over its child rows.

    Each time you call the next() method it returns the next sibling
    :obj:`Gtk.TreeModelRow`. When there are no rows left the StopIteration
    exception is raised. Note that a :obj:`Gtk.TreeModelRowIter` does not
    iterate over the child rows of the rows it is iterating over. You'll have
    to use the :obj:`Gtk.TreeModelRow.iterchildren`\() method to retrieve an
    iterator for the child rows.
    """

    def __init__(self, model, aiter):
        self.model = model
        self.iter = aiter

    def __next__(self):
        if not self.iter:
            raise StopIteration
        row = TreeModelRow(self.model, self.iter)
        self.iter = self.model.iter_next(self.iter)
        return row

    # alias for Python 2.x object protocol
    next = __next__
    """Returns the next :obj:`Gtk.TreeModelRow`"""

    def __iter__(self):
        return self

__all__.append('TreeModelRowIter')


class TreePath(Gtk.TreePath):

    def __new__(cls, path=0):
        if isinstance(path, int):
            path = str(path)
        elif not isinstance(path, _basestring):
            path = ":".join(str(val) for val in path)

        if len(path) == 0:
            raise TypeError("could not parse subscript '%s' as a tree path" % path)
        try:
            return TreePath.new_from_string(path)
        except TypeError:
            raise TypeError("could not parse subscript '%s' as a tree path" % path)

    def __init__(self, *args, **kwargs):
        super(TreePath, self).__init__()

    def __str__(self):
        return self.to_string()

    def __lt__(self, other):
        return other is not None and self.compare(other) < 0

    def __le__(self, other):
        return other is not None and self.compare(other) <= 0

    def __eq__(self, other):
        return other is not None and self.compare(other) == 0

    def __ne__(self, other):
        return other is None or self.compare(other) != 0

    def __gt__(self, other):
        return other is None or self.compare(other) > 0

    def __ge__(self, other):
        return other is None or self.compare(other) >= 0

    def __iter__(self):
        return iter(self.get_indices())

    def __len__(self):
        return self.get_depth()

    def __getitem__(self, index):
        return self.get_indices()[index]

TreePath = override(TreePath)
__all__.append('TreePath')


class TreeStore(Gtk.TreeStore, TreeModel, TreeSortable):
    def __init__(self, *column_types):
        Gtk.TreeStore.__init__(self)
        self.set_column_types(column_types)

    def _do_insert(self, parent, position, row):
        if row is not None:
            row, columns = self._convert_row(row)
            treeiter = self.insert_with_values(parent, position, columns, row)
        else:
            treeiter = Gtk.TreeStore.insert(self, parent, position)

        return treeiter

    def append(self, parent, row=None):
        """append(parent, row=None)

        :param parent: A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type parent: :obj:`Gtk.TreeIter` or :obj:`None`

        :param row: a list of values to apply to the newly inserted row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: obj:`Gtk.TreeIter` pointing to the inserted row
        :rtype: :obj:`Gtk.TreeIter`

        Appends a new row to `self`. If `parent` is not :obj:`None`, then it
        will append the new row after the last child of `parent`, otherwise it
        will append a row to the top level.

        The returned `iterator will point to the new row. The row will be
        empty after this function is called  if `row` is :obj:`None`. To fill
        in values, you need to call :obj:`Gtk.TreeStore.set`\() or
        :obj:`Gtk.TreeStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.
        """

        return self._do_insert(parent, -1, row)

    def prepend(self, parent, row=None):
        """prepend(parent, row=None)

        :param parent: A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type parent: :obj:`Gtk.TreeIter` or :obj:`None`

        :param row: a list of values to apply to the newly inserted row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: obj:`Gtk.TreeIter` pointing to the inserted row
        :rtype: :obj:`Gtk.TreeIter`

        Prepends a new row to `self`. If `parent` is not :obj:`None`, then it
        will prepend the new row before the first child of `parent`, otherwise
        it will prepend a row to the top level.

        The returned `iterator will point to the new row. The row will be
        empty after this function is called if `row` is :obj:`None`. To fill
        in values, you need to call :obj:`Gtk.TreeStore.set`\() or
        :obj:`Gtk.TreeStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.
        """

        return self._do_insert(parent, 0, row)

    def insert(self, parent, position, row=None):
        """insert(parent, position, row=None)

        :param parent:
            A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type parent: :obj:`Gtk.TreeIter` or :obj:`None`

        :param position:
            position to insert the new row, or -1 for last
        :type position: :obj:`int`

        :param row: a list of values to apply to the newly inserted row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: a :obj:`Gtk.TreeIter` pointing to the new row
        :rtype: :obj:`Gtk.TreeIter`

        Creates a new row at `position`.  If parent is not :obj:`None`, then
        the row will be made a child of `parent`.  Otherwise, the row will be
        created at the toplevel. If `position` is -1 or is larger than the
        number of rows at that level, then the new row will be inserted to the
        end of the list.

        The returned iterator will point to the newly inserted row. The row
        will be empty after this function is called if `row` is :obj:`None`.
        To fill in values, you need to call :obj:`Gtk.TreeStore.set`\() or
        :obj:`Gtk.TreeStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.
        """

        return self._do_insert(parent, position, row)

    # FIXME: sends two signals; check if this can use an atomic
    # insert_with_valuesv()

    def insert_before(self, parent, sibling, row=None):
        """insert_before(parent, sibling, row=None)

        :param parent: A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type parent: :obj:`Gtk.TreeIter` or :obj:`None`

        :param sibling: A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type sibling: :obj:`Gtk.TreeIter` or :obj:`None`

        :param row: a list of values to apply to the newly inserted row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: a :obj:`Gtk.TreeIter` pointing to the new row
        :rtype: :obj:`Gtk.TreeIter`

        Inserts a new row before `sibling`. If `sibling` is :obj:`None`, then
        the row will be appended to `parent` 's children. If `parent` and
        `sibling` are :obj:`None`, then the row will be appended to the
        toplevel.  If both `sibling` and `parent` are set, then `parent` must
        be the parent of `sibling`.  When `sibling` is set, `parent` is
        optional.

        The returned iterator will point to this new row. The row will be
        empty after this function is called if `row` is :obj:`None`.  To fill
        in values, you need to call :obj:`Gtk.TreeStore.set`\() or
        :obj:`Gtk.TreeStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.
        """

        treeiter = Gtk.TreeStore.insert_before(self, parent, sibling)

        if row is not None:
            self.set_row(treeiter, row)

        return treeiter

    # FIXME: sends two signals; check if this can use an atomic
    # insert_with_valuesv()

    def insert_after(self, parent, sibling, row=None):
        """
        :param parent: A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type parent: :obj:`Gtk.TreeIter` or :obj:`None`

        :param sibling: A valid :obj:`Gtk.TreeIter`, or :obj:`None`
        :type sibling: :obj:`Gtk.TreeIter` or :obj:`None`

        :param row: a list of values to apply to the newly inserted row or :obj:`None`
        :type row: [:obj:`object`] or :obj:`None`

        :returns: a :obj:`Gtk.TreeIter` pointing to the new row
        :rtype: :obj:`Gtk.TreeIter`

        Inserts a new row after `sibling`.  If `sibling` is :obj:`None`, then
        the row will be prepended to `parent` 's children.  If `parent` and
        `sibling` are :obj:`None`, then the row will be prepended to the
        toplevel.  If both `sibling` and `parent` are set, then `parent` must
        be the parent of `sibling`.  When `sibling` is set, `parent` is
        optional.

        The returned iterator will point to this new row.  The row will be
        empty after this function is called if `row` is :obj:`None`.  To fill
        in values, you need to call :obj:`Gtk.TreeStore.set`\() or
        :obj:`Gtk.TreeStore.set_value`\().

        If `row` isn't :obj:`None` it has to be a list of values which will be
        used to fill the row.
        """

        treeiter = Gtk.TreeStore.insert_after(self, parent, sibling)

        if row is not None:
            self.set_row(treeiter, row)

        return treeiter

    def set_value(self, treeiter, column, value):
        """
        {{ all }}

        `value` can also be a Python value and will be converted to a
        :obj:`GObject.Value` using the corresponding column type (See
        :obj:`Gtk.ListStore.set_column_types`\()).
        """

        value = self._convert_value(column, value)
        Gtk.TreeStore.set_value(self, treeiter, column, value)

    def set(self, treeiter, *args):

        def _set_lists(columns, values):
            if len(columns) != len(values):
                raise TypeError('The number of columns do not match the number of values')
            for col_num, val in zip(columns, values):
                if not isinstance(col_num, int):
                    raise TypeError('TypeError: Expected integer argument for column.')
                self.set_value(treeiter, col_num, val)

        if args:
            if isinstance(args[0], int):
                columns = args[::2]
                values = args[1::2]
                _set_lists(columns, values)
            elif isinstance(args[0], (tuple, list)):
                if len(args) != 2:
                    raise TypeError('Too many arguments')
                _set_lists(args[0], args[1])
            elif isinstance(args[0], dict):
                columns = args[0].keys()
                values = args[0].values()
                _set_lists(columns, values)
            else:
                raise TypeError('Argument list must be in the form of (column, value, ...), ((columns,...), (values, ...)) or {column: value}.  No -1 termination is needed.')

TreeStore = override(TreeStore)
__all__.append('TreeStore')


class TreeView(Gtk.TreeView, Container):
    __init__ = deprecated_init(Gtk.TreeView.__init__,
                               arg_names=('model',),
                               category=PyGTKDeprecationWarning)

    get_path_at_pos = strip_boolean_result(Gtk.TreeView.get_path_at_pos)
    """
    :param x: The x position to be identified (relative to bin\_window).
    :type x: :obj:`int`

    :param y: The y position to be identified (relative to bin\_window).
    :type y: :obj:`int`

    :returns:
        :obj:`None` if the row doesn't exist at that coordinates or
        a tuple containing:

        :path: a :obj:`Gtk.TreePath`
        :column: a :obj:`Gtk.TreeViewColumn`
        :cell_x: the X coordinate relative to the cell
        :cell_y: the Y coordinate relative to the cell

    :rtype: (**path**: :obj:`Gtk.TreePath` or :obj:`None`, **column**: :obj:`Gtk.TreeViewColumn` or :obj:`None`, **cell_x**: :obj:`int`, **cell_y**: :obj:`int`) or :obj:`None`

    {{ docs }}
    """

    get_visible_range = strip_boolean_result(Gtk.TreeView.get_visible_range)
    """
    :returns:
        Either :obj:`None` if there is no visible range or a tuple containing:

        :start_path: start of region
        :end_path: end of region

    :rtype: (**start_path**: :obj:`Gtk.TreePath`, **end_path**: :obj:`Gtk.TreePath`) or :obj:`None`

    Returns the first and last visible path. Note that there may be invisible
    paths in between.
    """

    get_dest_row_at_pos = strip_boolean_result(Gtk.TreeView.get_dest_row_at_pos)
    """
    :param drag_x: the position to determine the destination row for
    :type drag_x: :obj:`int`

    :param drag_y: the position to determine the destination row for
    :type drag_y: :obj:`int`

    :returns:
        :obj:`None` if there is no row at the given position or a tuple
        containing:

        :path: the path of the highlighted row
        :pos: the drop position

    :rtype: (**path**: :obj:`Gtk.TreePath` or :obj:`None`, **pos**: :obj:`Gtk.TreeViewDropPosition`) or :obj:`None`

    Determines the destination row for a given position.  `drag_x` and
    `drag_y` are expected to be in widget coordinates.  This function is only
    meaningful if `self` is realized.  Therefore this function will always
    return :obj:`None` if `self` is not realized or does not have a model.
    """

    def enable_model_drag_source(self, start_button_mask, targets, actions):
        target_entries = _construct_target_list(targets)
        super(TreeView, self).enable_model_drag_source(start_button_mask,
                                                       target_entries,
                                                       actions)

    def enable_model_drag_dest(self, targets, actions):
        target_entries = _construct_target_list(targets)
        super(TreeView, self).enable_model_drag_dest(target_entries,
                                                     actions)

    def scroll_to_cell(self, path, column=None, use_align=False, row_align=0.0, col_align=0.0):
        if not isinstance(path, Gtk.TreePath):
            path = TreePath(path)
        super(TreeView, self).scroll_to_cell(path, column, use_align, row_align, col_align)

    def set_cursor(self, path, column=None, start_editing=False):
        if not isinstance(path, Gtk.TreePath):
            path = TreePath(path)
        super(TreeView, self).set_cursor(path, column, start_editing)

    def get_cell_area(self, path, column=None):
        if not isinstance(path, Gtk.TreePath):
            path = TreePath(path)
        return super(TreeView, self).get_cell_area(path, column)

    def insert_column_with_attributes(self, position, title, cell, **kwargs):
        """
        :param position: The position to insert the new column in
        :type position: :obj:`int`

        :param title: The title to set the header to
        :type title: :obj:`str`

        :param cell: The :obj:`Gtk.CellRenderer`
        :type cell: :obj:`Gtk.CellRenderer`

        {{ docs }}
        """

        column = TreeViewColumn()
        column.set_title(title)
        column.pack_start(cell, False)
        self.insert_column(column, position)
        column.set_attributes(cell, **kwargs)

TreeView = override(TreeView)
__all__.append('TreeView')


class TreeViewColumn(Gtk.TreeViewColumn):
    def __init__(self, title='',
                 cell_renderer=None,
                 **attributes):
        Gtk.TreeViewColumn.__init__(self, title=title)
        if cell_renderer:
            self.pack_start(cell_renderer, True)

        for (name, value) in attributes.items():
            self.add_attribute(cell_renderer, name, value)

    cell_get_position = strip_boolean_result(Gtk.TreeViewColumn.cell_get_position)
    """
    :param cell_renderer: a :obj:`Gtk.CellRenderer`
    :type cell_renderer: :obj:`Gtk.CellRenderer`

    :returns:
        :obj:`None` if `cell` does not belong to `self` or a tuple containing:

        :x_offset: the horizontal position of `cell` within `self`
        :width: the width of `cell`

    :rtype: (**x_offset**: :obj:`int`, **width**: :obj:`int`) or :obj:`None`

    Obtains the horizontal position and size of a cell in a column. If the
    cell is not found in the column :obj:`None` is returned.
    """

    def set_cell_data_func(self, cell_renderer, func, func_data=None):
        super(TreeViewColumn, self).set_cell_data_func(cell_renderer, func, func_data)

    def set_attributes(self, cell_renderer, **attributes):
        """
        :param cell_renderer: the :obj:`Gtk.CellRenderer` we're setting the attributes of
        :type cell_renderer: :obj:`Gtk.CellRenderer`

        {{ docs }}
        """

        Gtk.CellLayout.clear_attributes(self, cell_renderer)

        for (name, value) in attributes.items():
            Gtk.CellLayout.add_attribute(self, cell_renderer, name, value)


TreeViewColumn = override(TreeViewColumn)
__all__.append('TreeViewColumn')


class TreeSelection(Gtk.TreeSelection):

    def select_path(self, path):
        if not isinstance(path, Gtk.TreePath):
            path = TreePath(path)
        super(TreeSelection, self).select_path(path)

    def get_selected(self):
        """
        :returns:
            :model: the :obj:`Gtk.TreeModel`
            :iter: The :obj:`Gtk.TreeIter` or :obj:`None`

        :rtype: (**model**: :obj:`Gtk.TreeModel`, **iter**: :obj:`Gtk.TreeIter` or :obj:`None`)

        {{ docs }}
        """

        success, model, aiter = super(TreeSelection, self).get_selected()
        if success:
            return (model, aiter)
        else:
            return (model, None)

    # for compatibility with PyGtk

    def get_selected_rows(self):
        """
        :returns:
            A list containing a :obj:`Gtk.TreePath` for each selected row
            and a :obj:`Gtk.TreeModel` or :obj:`None`.

        :rtype: (:obj:`Gtk.TreeModel`, [:obj:`Gtk.TreePath`])

        {{ docs }}
        """

        rows, model = super(TreeSelection, self).get_selected_rows()
        return (model, rows)


TreeSelection = override(TreeSelection)
__all__.append('TreeSelection')


class Button(Gtk.Button, Container):
    _init = deprecated_init(Gtk.Button.__init__,
                            arg_names=('label', 'stock', 'use_stock', 'use_underline'),
                            ignore=('stock',),
                            category=PyGTKDeprecationWarning,
                            stacklevel=3)

    def __init__(self, *args, **kwargs):
        # Doubly deprecated initializer, the stock keyword is non-standard.
        # Simply give a warning that stock items are deprecated even though
        # we want to deprecate the non-standard keyword as well here from
        # the overrides.
        if 'stock' in kwargs and kwargs['stock']:
            warnings.warn('Stock items are deprecated. '
                          'Please use: Gtk.Button.new_with_mnemonic(label)',
                          PyGTKDeprecationWarning, stacklevel=2)
            new_kwargs = kwargs.copy()
            new_kwargs['label'] = new_kwargs['stock']
            new_kwargs['use_stock'] = True
            new_kwargs['use_underline'] = True
            del new_kwargs['stock']
            Gtk.Button.__init__(self, **new_kwargs)
        else:
            self._init(*args, **kwargs)

Button = override(Button)
__all__.append('Button')


class LinkButton(Gtk.LinkButton):
    __init__ = deprecated_init(Gtk.LinkButton.__init__,
                               arg_names=('uri', 'label'),
                               category=PyGTKDeprecationWarning)

LinkButton = override(LinkButton)
__all__.append('LinkButton')


class Label(Gtk.Label):
    __init__ = deprecated_init(Gtk.Label.__init__,
                               arg_names=('label',),
                               category=PyGTKDeprecationWarning)

Label = override(Label)
__all__.append('Label')


class Adjustment(Gtk.Adjustment):
    _init = deprecated_init(Gtk.Adjustment.__init__,
                            arg_names=('value', 'lower', 'upper',
                                       'step_increment', 'page_increment', 'page_size'),
                            deprecated_aliases={'page_increment': 'page_incr',
                                                'step_increment': 'step_incr'},
                            category=PyGTKDeprecationWarning,
                            stacklevel=3)

    def __init__(self, *args, **kwargs):
        self._init(*args, **kwargs)

        # The value property is set between lower and (upper - page_size).
        # Just in case lower, upper or page_size was still 0 when value
        # was set, we set it again here.
        if 'value' in kwargs:
            self.set_value(kwargs['value'])

Adjustment = override(Adjustment)
__all__.append('Adjustment')


class Table(Gtk.Table, Container):
    __init__ = deprecated_init(Gtk.Table.__init__,
                               arg_names=('n_rows', 'n_columns', 'homogeneous'),
                               deprecated_aliases={'n_rows': 'rows', 'n_columns': 'columns'},
                               category=PyGTKDeprecationWarning)

    def attach(self, child, left_attach, right_attach, top_attach, bottom_attach, xoptions=Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, xpadding=0, ypadding=0):
        Gtk.Table.attach(self, child, left_attach, right_attach, top_attach, bottom_attach, xoptions, yoptions, xpadding, ypadding)

Table = override(Table)
__all__.append('Table')


class ScrolledWindow(Gtk.ScrolledWindow):
    __init__ = deprecated_init(Gtk.ScrolledWindow.__init__,
                               arg_names=('hadjustment', 'vadjustment'),
                               category=PyGTKDeprecationWarning)

ScrolledWindow = override(ScrolledWindow)
__all__.append('ScrolledWindow')


class HScrollbar(Gtk.HScrollbar):
    __init__ = deprecated_init(Gtk.HScrollbar.__init__,
                               arg_names=('adjustment',),
                               category=PyGTKDeprecationWarning)

HScrollbar = override(HScrollbar)
__all__.append('HScrollbar')


class VScrollbar(Gtk.VScrollbar):
    __init__ = deprecated_init(Gtk.VScrollbar.__init__,
                               arg_names=('adjustment',),
                               category=PyGTKDeprecationWarning)

VScrollbar = override(VScrollbar)
__all__.append('VScrollbar')


class Paned(Gtk.Paned):
    def pack1(self, child, resize=False, shrink=True):
        super(Paned, self).pack1(child, resize, shrink)

    def pack2(self, child, resize=True, shrink=True):
        super(Paned, self).pack2(child, resize, shrink)

Paned = override(Paned)
__all__.append('Paned')


class Arrow(Gtk.Arrow):
    __init__ = deprecated_init(Gtk.Arrow.__init__,
                               arg_names=('arrow_type', 'shadow_type'),
                               category=PyGTKDeprecationWarning)

Arrow = override(Arrow)
__all__.append('Arrow')


class IconSet(Gtk.IconSet):
    def __new__(cls, pixbuf=None):
        if pixbuf is not None:
            warnings.warn('Gtk.IconSet(pixbuf) has been deprecated. Please use: '
                          'Gtk.IconSet.new_from_pixbuf(pixbuf)',
                          PyGTKDeprecationWarning, stacklevel=2)
            iconset = Gtk.IconSet.new_from_pixbuf(pixbuf)
        else:
            iconset = Gtk.IconSet.__new__(cls)
        return iconset

    def __init__(self, *args, **kwargs):
        return super(IconSet, self).__init__()

IconSet = override(IconSet)
__all__.append('IconSet')


class Viewport(Gtk.Viewport):
    __init__ = deprecated_init(Gtk.Viewport.__init__,
                               arg_names=('hadjustment', 'vadjustment'),
                               category=PyGTKDeprecationWarning)

Viewport = override(Viewport)
__all__.append('Viewport')


class TreeModelFilter(Gtk.TreeModelFilter):
    def set_visible_func(self, func, data=None):
        super(TreeModelFilter, self).set_visible_func(func, data)

    def set_value(self, iter, column, value):
        """Set the value of the child model"""

        # Delegate to child model
        iter = self.convert_iter_to_child_iter(iter)
        self.get_model().set_value(iter, column, value)

TreeModelFilter = override(TreeModelFilter)
__all__.append('TreeModelFilter')

if Gtk._version != '2.0':
    class Menu(Gtk.Menu):
        def popup(self, parent_menu_shell, parent_menu_item, func, data, button, activate_time):
            self.popup_for_device(None, parent_menu_shell, parent_menu_item, func, data, button, activate_time)
    Menu = override(Menu)
    __all__.append('Menu')

_Gtk_main_quit = Gtk.main_quit


@override(Gtk.main_quit)
def main_quit(*args):
    _Gtk_main_quit()

stock_lookup = strip_boolean_result(Gtk.stock_lookup)
"""
:param stock_id: a stock item name
:type stock_id: :obj:`str`

:returns: a stock item or :obj:`None` if the stock icon isn't known.
:rtype: :obj:`Gtk.StockItem` or :obj:`None`
"""

__all__.append('stock_lookup')

initialized, argv = Gtk.init_check(sys.argv)
sys.argv = list(argv)
