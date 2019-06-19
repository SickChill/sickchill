# -*- Mode: Python; py-indent-offset: 4 -*-
# vim: tabstop=4 shiftwidth=4 expandtab
#
# Copyright (C) 2010 Tomeu Vizoso <tomeu.vizoso@collabora.co.uk>
# Copyright (C) 2011, 2012 Canonical Ltd.
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

import signal
import warnings
import sys

from pgi.gerror import PGError as GError
from pgi.overrides import get_introspection_module, override, deprecated, \
    deprecated_attr
from pgi.util import PyGIDeprecationWarning
from pgi import version_info
from pgi.static import (source_new, Enum, Flags,
                        source_set_callback, io_channel_read)
from pgi import static as _gobject
from pgi import static as _glib


GLib = get_introspection_module('GLib')

__all__ = []

__all__ += ["Enum", "Flags"]

_glib._init_glib(GLib)
Error = GError
OptionContext = _glib.OptionContext
OptionGroup = _glib.OptionGroup
Pid = _glib.Pid


spawn_async = _glib.spawn_async
"""spawn_async(argv, envp=None, working_directory=None, flags=GLib.SpawnFlags.DEFAULT, child_setup=None, user_data=None, standard_input=False, standard_output=False, standard_error=False)

:param argv: child's argument vector
:type argv: [:obj:`str`]

:param envp: child's environment, or :obj:`None` to inherit parent's
:type envp: [:obj:`str`] or :obj:`None`

:param flags: flags from :obj:`GLib.SpawnFlags`
:type flags: :obj:`GLib.SpawnFlags`

:param child_setup: function to run in the child just before exec()
:type child_setup: :obj:`GLib.SpawnChildSetupFunc` or :obj:`None`

:param user_data: user data for `child_setup`
:type user_data: :obj:`object` or :obj:`None`

:param standard_input: pipe stdin if :obj:`True`
:type standard_input: :obj:`bool`

:param standard_output: pipe stdout if :obj:`True`
:type standard_output: :obj:`bool`

:param standard_error: pipe stderr if :obj:`True`
:type standard_error: :obj:`bool`

:raises: :class:`GLib.Error`

:returns:
    :pid: child process ID
    :stdin: file descriptor to child's stdin, or :obj:`None`
    :stdout: file descriptor to read child's stdout, or :obj:`None`
    :stderr: file descriptor to read child's stderr, or :obj:`None`

:rtype: (**pid**: :obj:`int`, **stdin**: :obj:`int` or :obj:`None`, **stdout**: :obj:`int` or :obj:`None`, **stderr**: :obj:`int` or :obj:`None`)

See :obj:`GLib.spawn_async_with_pipes`\() for a full description; this function
simply calls the :obj:`GLib.spawn_async_with_pipes`\()

You should call :obj:`GLib.spawn_close_pid`\() on the returned child process
reference when you don't need it any more.

In case `standard_input`/`standard_output`/`standard_error` are True a file
descriptor is returned which needs to be closed by the caller after it is no
longer needed.
"""


def variant_type_from_string(s):
    return GLib.VariantType.new(s)

def threads_init():
    warnings.warn('Since version 3.11, calling threads_init is no longer needed. '
                  'See: https://wiki.gnome.org/PyGObject/Threading',
                  PyGIDeprecationWarning, stacklevel=2)


def gerror_matches(self, domain, code):
    # Handle cases where self.domain was set to an integer for compatibility
    # with the introspected GLib.Error.
    if isinstance(self.domain, str):
        self_domain_quark = GLib.quark_from_string(self.domain)
    else:
        self_domain_quark = self.domain
    return (self_domain_quark, self.code) == (domain, code)


def gerror_new_literal(domain, message, code):
    domain_quark = GLib.quark_to_string(domain)
    return GError(message, domain_quark, code)


# Monkey patch methods that rely on GLib introspection to be loaded at runtime.
Error.__name__ = 'Error'
Error.__module__ = 'GLib'
Error.matches = gerror_matches
Error.new_literal = staticmethod(gerror_new_literal)


__all__ += ['GError', 'Error', 'OptionContext', 'OptionGroup', 'Pid',
            'spawn_async', 'threads_init']


class _VariantCreator(object):

    _LEAF_CONSTRUCTORS = {
        'b': GLib.Variant.new_boolean,
        'y': GLib.Variant.new_byte,
        'n': GLib.Variant.new_int16,
        'q': GLib.Variant.new_uint16,
        'i': GLib.Variant.new_int32,
        'u': GLib.Variant.new_uint32,
        'x': GLib.Variant.new_int64,
        't': GLib.Variant.new_uint64,
        'h': GLib.Variant.new_handle,
        'd': GLib.Variant.new_double,
        's': GLib.Variant.new_string,
        'o': GLib.Variant.new_object_path,
        'g': GLib.Variant.new_signature,
        'v': GLib.Variant.new_variant,
    }

    def _create(self, format, args):
        """Create a GVariant object from given format and argument list.

        This method recursively calls itself for complex structures (arrays,
        dictionaries, boxed).

        Return a tuple (variant, rest_format, rest_args) with the generated
        GVariant, the remainder of the format string, and the remainder of the
        arguments.

        If args is None, then this won't actually consume any arguments, and
        just parse the format string and generate empty GVariant structures.
        This is required for creating empty dictionaries or arrays.
        """
        # leaves (simple types)
        constructor = self._LEAF_CONSTRUCTORS.get(format[0])
        if constructor:
            if args is not None:
                if not args:
                    raise TypeError('not enough arguments for GVariant format string')
                v = constructor(args[0])
                return (v, format[1:], args[1:])
            else:
                return (None, format[1:], None)

        if format[0] == '(':
            return self._create_tuple(format, args)

        if format.startswith('a{'):
            return self._create_dict(format, args)

        if format[0] == 'a':
            return self._create_array(format, args)

        raise NotImplementedError('cannot handle GVariant type ' + format)

    def _create_tuple(self, format, args):
        """Handle the case where the outermost type of format is a tuple."""

        format = format[1:]  # eat the '('
        if args is None:
            # empty value: we need to call _create() to parse the subtype
            rest_format = format
            while rest_format:
                if rest_format.startswith(')'):
                    break
                rest_format = self._create(rest_format, None)[1]
            else:
                raise TypeError('tuple type string not closed with )')

            rest_format = rest_format[1:]  # eat the )
            return (None, rest_format, None)
        else:
            if not args or not isinstance(args[0], tuple):
                raise TypeError('expected tuple argument')

            builder = GLib.VariantBuilder.new(variant_type_from_string('r'))
            for i in range(len(args[0])):
                if format.startswith(')'):
                    raise TypeError('too many arguments for tuple signature')

                (v, format, _) = self._create(format, args[0][i:])
                builder.add_value(v)
            args = args[1:]
            if not format.startswith(')'):
                raise TypeError('tuple type string not closed with )')

            rest_format = format[1:]  # eat the )
            return (builder.end(), rest_format, args)

    def _create_dict(self, format, args):
        """Handle the case where the outermost type of format is a dict."""

        builder = None
        if args is None or not args[0]:
            # empty value: we need to call _create() to parse the subtype,
            # and specify the element type precisely
            rest_format = self._create(format[2:], None)[1]
            rest_format = self._create(rest_format, None)[1]
            if not rest_format.startswith('}'):
                raise TypeError('dictionary type string not closed with }')
            rest_format = rest_format[1:]  # eat the }
            element_type = format[:len(format) - len(rest_format)]
            builder = GLib.VariantBuilder.new(variant_type_from_string(element_type))
        else:
            builder = GLib.VariantBuilder.new(variant_type_from_string('a{?*}'))
            for k, v in args[0].items():
                (key_v, rest_format, _) = self._create(format[2:], [k])
                (val_v, rest_format, _) = self._create(rest_format, [v])

                if not rest_format.startswith('}'):
                    raise TypeError('dictionary type string not closed with }')
                rest_format = rest_format[1:]  # eat the }

                entry = GLib.VariantBuilder.new(variant_type_from_string('{?*}'))
                entry.add_value(key_v)
                entry.add_value(val_v)
                builder.add_value(entry.end())

        if args is not None:
            args = args[1:]
        return (builder.end(), rest_format, args)

    def _create_array(self, format, args):
        """Handle the case where the outermost type of format is an array."""

        builder = None
        if args is None or not args[0]:
            # empty value: we need to call _create() to parse the subtype,
            # and specify the element type precisely
            rest_format = self._create(format[1:], None)[1]
            element_type = format[:len(format) - len(rest_format)]
            builder = GLib.VariantBuilder.new(variant_type_from_string(element_type))
        else:
            builder = GLib.VariantBuilder.new(variant_type_from_string('a*'))
            for i in range(len(args[0])):
                (v, rest_format, _) = self._create(format[1:], args[0][i:])
                builder.add_value(v)
        if args is not None:
            args = args[1:]
        return (builder.end(), rest_format, args)


class Variant(GLib.Variant):
    def __new__(cls, format_string, value):
        """Create a GVariant from a native Python object.

        format_string is a standard GVariant type signature, value is a Python
        object whose structure has to match the signature.

        Examples:
          GLib.Variant('i', 1)
          GLib.Variant('(is)', (1, 'hello'))
          GLib.Variant('(asa{sv})', ([], {'foo': GLib.Variant('b', True),
                                          'bar': GLib.Variant('i', 2)}))
        """
        creator = _VariantCreator()
        (v, rest_format, _) = creator._create(format_string, [value])
        if rest_format:
            raise TypeError('invalid remaining format string: "%s"' % rest_format)
        v.format_string = format_string
        return v

    # Called by Python on the result of __new__, shall do nothing.
    def __init__(self, format_string, value):
        assert(self.format_string == format_string)

    @staticmethod
    def new_tuple(*elements):
        return GLib.Variant.new_tuple(elements)

    def __del__(self):
        self.unref()

    try:
        GLib.Variant.print_
    except AttributeError:
        # Python 3
        def print_(self, type_annotate):
            return getattr(self, "print")(type_annotate)

    def __str__(self):
        return self.print_(True)

    def __repr__(self):
        if hasattr(self, 'format_string'):
            f = self.format_string
        else:
            f = self.get_type_string()
        return "GLib.Variant('%s', %s)" % (f, self.print_(False))

    def __eq__(self, other):
        try:
            return self.equal(other)
        except TypeError:
            return False

    def __ne__(self, other):
        try:
            return not self.equal(other)
        except TypeError:
            return True

    def __hash__(self):
        # We're not using just hash(self.unpack()) because otherwise we'll have
        # hash collisions between the same content in different variant types,
        # which will cause a performance issue in set/dict/etc.
        return hash((self.get_type_string(), self.unpack()))

    def unpack(self):
        """Decompose a GVariant into a native Python object."""

        LEAF_ACCESSORS = {
            'b': self.get_boolean,
            'y': self.get_byte,
            'n': self.get_int16,
            'q': self.get_uint16,
            'i': self.get_int32,
            'u': self.get_uint32,
            'x': self.get_int64,
            't': self.get_uint64,
            'h': self.get_handle,
            'd': self.get_double,
            's': self.get_string,
            'o': self.get_string,  # object path
            'g': self.get_string,  # signature
        }

        # simple values
        la = LEAF_ACCESSORS.get(self.get_type_string())
        if la:
            return la()

        # tuple
        if self.get_type_string().startswith('('):
            res = [self.get_child_value(i).unpack()
                   for i in range(self.n_children())]
            return tuple(res)

        # dictionary
        if self.get_type_string().startswith('a{'):
            res = {}
            for i in range(self.n_children()):
                v = self.get_child_value(i)
                res[v.get_child_value(0).unpack()] = v.get_child_value(1).unpack()
            return res

        # array
        if self.get_type_string().startswith('a'):
            return [self.get_child_value(i).unpack()
                    for i in range(self.n_children())]

        # variant (just unbox transparently)
        if self.get_type_string().startswith('v'):
            return self.get_variant().unpack()

        # maybe
        if self.get_type_string().startswith('m'):
            m = self.get_maybe()
            return m.unpack() if m else None

        raise NotImplementedError('unsupported GVariant type ' + self.get_type_string())

    @classmethod
    def split_signature(klass, signature):
        """Return a list of the element signatures of the topmost signature tuple.

        If the signature is not a tuple, it returns one element with the entire
        signature. If the signature is an empty tuple, the result is [].

        This is useful for e. g. iterating over method parameters which are
        passed as a single Variant.
        """
        if signature == '()':
            return []

        if not signature.startswith('('):
            return [signature]

        result = []
        head = ''
        tail = signature[1:-1]  # eat the surrounding ()
        while tail:
            c = tail[0]
            head += c
            tail = tail[1:]

            if c in ('m', 'a'):
                # prefixes, keep collecting
                continue
            if c in ('(', '{'):
                # consume until corresponding )/}
                level = 1
                up = c
                if up == '(':
                    down = ')'
                else:
                    down = '}'
                while level > 0:
                    c = tail[0]
                    head += c
                    tail = tail[1:]
                    if c == up:
                        level += 1
                    elif c == down:
                        level -= 1

            # otherwise we have a simple type
            result.append(head)
            head = ''

        return result

    #
    # Pythonic iterators
    #

    def __len__(self):
        if self.get_type_string() in ['s', 'o', 'g']:
            return len(self.get_string())
        # Array, dict, tuple
        if self.get_type_string().startswith('a') or self.get_type_string().startswith('('):
            return self.n_children()
        raise TypeError('GVariant type %s does not have a length' % self.get_type_string())

    def __getitem__(self, key):
        # dict
        if self.get_type_string().startswith('a{'):
            try:
                val = self.lookup_value(key, variant_type_from_string('*'))
                if val is None:
                    raise KeyError(key)
                return val.unpack()
            except TypeError:
                # lookup_value() only works for string keys, which is certainly
                # the common case; we have to do painful iteration for other
                # key types
                for i in range(self.n_children()):
                    v = self.get_child_value(i)
                    if v.get_child_value(0).unpack() == key:
                        return v.get_child_value(1).unpack()
                raise KeyError(key)

        # array/tuple
        if self.get_type_string().startswith('a') or self.get_type_string().startswith('('):
            key = int(key)
            if key < 0:
                key = self.n_children() + key
            if key < 0 or key >= self.n_children():
                raise IndexError('list index out of range')
            return self.get_child_value(key).unpack()

        # string
        if self.get_type_string() in ['s', 'o', 'g']:
            return self.get_string().__getitem__(key)

        raise TypeError('GVariant type %s is not a container' % self.get_type_string())

    #
    # Pythonic bool operations
    #

    def __nonzero__(self):
        return self.__bool__()

    def __bool__(self):
        if self.get_type_string() in ['y', 'n', 'q', 'i', 'u', 'x', 't', 'h', 'd']:
            return self.unpack() != 0
        if self.get_type_string() in ['b']:
            return self.get_boolean()
        if self.get_type_string() in ['s', 'o', 'g']:
            return len(self.get_string()) != 0
        # Array, dict, tuple
        if self.get_type_string().startswith('a') or self.get_type_string().startswith('('):
            return self.n_children() != 0
        if self.get_type_string() in ['v']:
            # unpack works recursively, hence bool also works recursively
            return bool(self.unpack())
        # Everything else is True
        return True

    def keys(self):
        if not self.get_type_string().startswith('a{'):
            return TypeError, 'GVariant type %s is not a dictionary' % self.get_type_string()

        res = []
        for i in range(self.n_children()):
            v = self.get_child_value(i)
            res.append(v.get_child_value(0).unpack())
        return res


def get_string(self):
    value, length = GLib.Variant.get_string(self)
    return value

setattr(Variant, 'get_string', get_string)

__all__.append('Variant')


def markup_escape_text(text, length=-1):
    if isinstance(text, bytes):
        return GLib.markup_escape_text(text.decode('UTF-8'), length)
    else:
        return GLib.markup_escape_text(text, length)
__all__.append('markup_escape_text')


# backwards compatible names from old static bindings
for n in ['DESKTOP', 'DOCUMENTS', 'DOWNLOAD', 'MUSIC', 'PICTURES',
          'PUBLIC_SHARE', 'TEMPLATES', 'VIDEOS']:
    attr = 'USER_DIRECTORY_' + n
    deprecated_attr("GLib", attr, "GLib.UserDirectory.DIRECTORY_" + n)
    globals()[attr] = getattr(GLib.UserDirectory, 'DIRECTORY_' + n)
    __all__.append(attr)

for n in ['ERR', 'HUP', 'IN', 'NVAL', 'OUT', 'PRI']:
    globals()['IO_' + n] = getattr(GLib.IOCondition, n)
    __all__.append('IO_' + n)

for n in ['APPEND', 'GET_MASK', 'IS_READABLE', 'IS_SEEKABLE',
          'MASK', 'NONBLOCK', 'SET_MASK']:
    attr = 'IO_FLAG_' + n
    deprecated_attr("GLib", attr, "GLib.IOFlags." + n)
    globals()[attr] = getattr(GLib.IOFlags, n)
    __all__.append(attr)

# spelling for the win
IO_FLAG_IS_WRITEABLE = GLib.IOFlags.IS_WRITABLE
deprecated_attr("GLib", "IO_FLAG_IS_WRITEABLE", "GLib.IOFlags.IS_WRITABLE")
__all__.append('IO_FLAG_IS_WRITEABLE')

for n in ['AGAIN', 'EOF', 'ERROR', 'NORMAL']:
    attr = 'IO_STATUS_' + n
    globals()[attr] = getattr(GLib.IOStatus, n)
    deprecated_attr("GLib", attr, "GLib.IOStatus." + n)
    __all__.append(attr)

for n in ['CHILD_INHERITS_STDIN', 'DO_NOT_REAP_CHILD', 'FILE_AND_ARGV_ZERO',
          'LEAVE_DESCRIPTORS_OPEN', 'SEARCH_PATH', 'STDERR_TO_DEV_NULL',
          'STDOUT_TO_DEV_NULL']:
    attr = 'SPAWN_' + n
    globals()[attr] = getattr(GLib.SpawnFlags, n)
    deprecated_attr("GLib", attr, "GLib.SpawnFlags." + n)
    __all__.append(attr)

for n in ['HIDDEN', 'IN_MAIN', 'REVERSE', 'NO_ARG', 'FILENAME', 'OPTIONAL_ARG',
          'NOALIAS']:
    attr = 'OPTION_FLAG_' + n
    globals()[attr] = getattr(GLib.OptionFlags, n)
    deprecated_attr("GLib", attr, "GLib.OptionFlags." + n)
    __all__.append(attr)

for n in ['UNKNOWN_OPTION', 'BAD_VALUE', 'FAILED']:
    attr = 'OPTION_ERROR_' + n
    deprecated_attr("GLib", attr, "GLib.OptionError." + n)
    globals()[attr] = getattr(GLib.OptionError, n)
    __all__.append(attr)


# these are not currently exported in GLib gir, presumably because they are
# platform dependent; so get them from our static bindings
for name in ['G_MINFLOAT', 'G_MAXFLOAT', 'G_MINDOUBLE', 'G_MAXDOUBLE',
             'G_MINSHORT', 'G_MAXSHORT', 'G_MAXUSHORT', 'G_MININT', 'G_MAXINT',
             'G_MAXUINT', 'G_MINLONG', 'G_MAXLONG', 'G_MAXULONG', 'G_MAXSIZE',
             'G_MINSSIZE', 'G_MAXSSIZE', 'G_MINOFFSET', 'G_MAXOFFSET']:
    attr = name.split("_", 1)[-1]
    globals()[attr] = getattr(_gobject, name)
    __all__.append(attr)


class MainLoop(GLib.MainLoop):
    # Backwards compatible constructor API
    def __new__(cls, context=None):
        return GLib.MainLoop.new(context, False)

    # Retain classic pygobject behaviour of quitting main loops on SIGINT
    def __init__(self, context=None):
        def _handler(loop):
            loop.quit()
            loop._quit_by_sigint = True
            # We handle signal deletion in __del__, return True so GLib
            # doesn't do the deletion for us.
            return True

        if sys.platform != 'win32':
            # compatibility shim, keep around until we depend on glib 2.36
            if hasattr(GLib, 'unix_signal_add'):
                fn = GLib.unix_signal_add
            else:
                fn = GLib.unix_signal_add_full
            self._signal_source = fn(GLib.PRIORITY_DEFAULT, signal.SIGINT, _handler, self)

    def __del__(self):
        if hasattr(self, '_signal_source'):
            GLib.source_remove(self._signal_source)

    def run(self):
        super(MainLoop, self).run()
        if hasattr(self, '_quit_by_sigint'):
            # caught by _main_loop_sigint_handler()
            raise KeyboardInterrupt

MainLoop = override(MainLoop)
__all__.append('MainLoop')


class MainContext(GLib.MainContext):
    # Backwards compatible API with default value
    def iteration(self, may_block=True):
        return super(MainContext, self).iteration(may_block)

MainContext = override(MainContext)
__all__.append('MainContext')


class Source(GLib.Source):
    def __new__(cls, *args, **kwargs):
        # use our custom pyg_source_new() here as g_source_new() is not
        # bindable
        source = source_new()
        source.__class__ = cls
        setattr(source, '__pygi_custom_source', True)
        return source

    def __init__(self, *args, **kwargs):
        return super(Source, self).__init__()

    def set_callback(self, fn, user_data=None):
        if hasattr(self, '__pygi_custom_source'):
            # use our custom pyg_source_set_callback() if for a GSource object
            # with custom functions
            source_set_callback(self, fn, user_data)
        else:
            # otherwise, for Idle and Timeout, use the standard method
            super(Source, self).set_callback(fn, user_data)

    def get_current_time(self):
        return GLib.get_real_time() * 0.000001

    get_current_time = deprecated(get_current_time, 'GLib.Source.get_time() or GLib.get_real_time()')
    """get_current_time()

    :returns: Time in seconds since the Epoch
    :rtype: float

    {{ docs }}
    """

    # as get/set_priority are introspected, we can't use the static
    # property(get_priority, ..) here
    def __get_priority(self):
        return self.get_priority()

    def __set_priority(self, value):
        self.set_priority(value)

    priority = property(__get_priority, __set_priority)

    def __get_can_recurse(self):
        return self.get_can_recurse()

    def __set_can_recurse(self, value):
        self.set_can_recurse(value)

    can_recurse = property(__get_can_recurse, __set_can_recurse)

Source = override(Source)
__all__.append('Source')


class Idle(Source):
    def __new__(cls, priority=GLib.PRIORITY_DEFAULT):
        source = GLib.idle_source_new()
        source.__class__ = cls
        return source

    def __init__(self, priority=GLib.PRIORITY_DEFAULT):
        super(Source, self).__init__()
        if priority != GLib.PRIORITY_DEFAULT:
            self.set_priority(priority)

__all__.append('Idle')


class Timeout(Source):
    def __new__(cls, interval=0, priority=GLib.PRIORITY_DEFAULT):
        source = GLib.timeout_source_new(interval)
        source.__class__ = cls
        return source

    def __init__(self, interval=0, priority=GLib.PRIORITY_DEFAULT):
        if priority != GLib.PRIORITY_DEFAULT:
            self.set_priority(priority)

__all__.append('Timeout')


# backwards compatible API

# These functions will incorrectly be called with None as last argument, so
# work around that with wrappers.

def idle_add(function, *user_data, **kwargs):
    priority = kwargs.get('priority', GLib.PRIORITY_DEFAULT_IDLE)
    return GLib.idle_add(priority, lambda _: function(*user_data))

__all__.append('idle_add')


def timeout_add(interval, function, *user_data, **kwargs):
    priority = kwargs.get('priority', GLib.PRIORITY_DEFAULT)
    return GLib.timeout_add(priority, interval, lambda _: function(*user_data))

__all__.append('timeout_add')


def timeout_add_seconds(interval, function, *user_data, **kwargs):
    priority = kwargs.get('priority', GLib.PRIORITY_DEFAULT)
    return GLib.timeout_add_seconds(
        priority, interval, lambda _: function(*user_data))

__all__.append('timeout_add_seconds')


# The GI GLib API uses g_io_add_watch_full renamed to g_io_add_watch with
# a signature of (channel, priority, condition, func, user_data).
# Prior to PyGObject 3.8, this function was statically bound with an API closer to the
# non-full version with a signature of: (fd, condition, func, *user_data)
# We need to support this until we are okay with breaking API in a way which is
# not backwards compatible.
#
# This needs to take into account several historical APIs:
# - calling with an fd as first argument
# - calling with a Python file object as first argument (we keep this one as
#   it's really convenient and does not change the number of arguments)
# - calling without a priority as second argument
def _io_add_watch_get_args(channel, priority_, condition, *cb_and_user_data, **kwargs):
    if not isinstance(priority_, int) or isinstance(priority_, GLib.IOCondition):
        warnings.warn('Calling io_add_watch without priority as second argument is deprecated',
                      PyGIDeprecationWarning)
        # shift the arguments around
        user_data = cb_and_user_data
        callback = condition
        condition = priority_
        if not callable(callback):
            raise TypeError('third argument must be callable')

        # backwards compatibility: Call with priority kwarg
        if 'priority' in kwargs:
            warnings.warn('Calling io_add_watch with priority keyword argument is deprecated, put it as second positional argument',
                          PyGIDeprecationWarning)
            priority_ = kwargs['priority']
        else:
            priority_ = GLib.PRIORITY_DEFAULT
    else:
        if len(cb_and_user_data) < 1 or not callable(cb_and_user_data[0]):
            raise TypeError('expecting callback as fourth argument')
        callback = cb_and_user_data[0]
        user_data = cb_and_user_data[1:]

    # backwards compatibility: Allow calling with fd
    if isinstance(channel, int):
        func_fdtransform = lambda _, cond, *data: callback(channel, cond, *data)
        real_channel = GLib.IOChannel.unix_new(channel)
    elif hasattr(channel, 'fileno'):
        # backwards compatibility: Allow calling with Python file
        func_fdtransform = lambda _, cond, *data: callback(channel, cond, *data)
        real_channel = GLib.IOChannel.unix_new(channel.fileno())
    else:
        assert isinstance(channel, GLib.IOChannel)
        func_fdtransform = callback
        real_channel = channel

    return real_channel, priority_, condition, func_fdtransform, user_data

__all__.append('_io_add_watch_get_args')


def io_add_watch(*args, **kwargs):
    """io_add_watch(channel, priority, condition, func, *user_data) -> event_source_id"""
    channel, priority, condition, func, user_data = _io_add_watch_get_args(*args, **kwargs)
    return GLib.io_add_watch(channel, priority, condition, func, *user_data)

__all__.append('io_add_watch')


# backwards compatible API
class IOChannel(GLib.IOChannel):
    def __new__(cls, filedes=None, filename=None, mode=None, hwnd=None):
        if filedes is not None:
            return GLib.IOChannel.unix_new(filedes)
        if filename is not None:
            return GLib.IOChannel.new_file(filename, mode or 'r')
        if hwnd is not None:
            return GLib.IOChannel.win32_new_fd(hwnd)
        raise TypeError('either a valid file descriptor, file name, or window handle must be supplied')

    def __init__(self, *args, **kwargs):
        return super(IOChannel, self).__init__()

    def read(self, max_count=-1):
        return io_channel_read(self, max_count)

    def readline(self, size_hint=-1):
        # note, size_hint is just to maintain backwards compatible API; the
        # old static binding did not actually use it
        (status, buf, length, terminator_pos) = self.read_line()
        if buf is None:
            return ''
        return buf

    def readlines(self, size_hint=-1):
        # note, size_hint is just to maintain backwards compatible API;
        # the old static binding did not actually use it
        lines = []
        status = GLib.IOStatus.NORMAL
        while status == GLib.IOStatus.NORMAL:
            (status, buf, length, terminator_pos) = self.read_line()
            # note, this appends an empty line after EOF; this is
            # bug-compatible with the old static bindings
            if buf is None:
                buf = ''
            lines.append(buf)
        return lines

    def write(self, buf, buflen=-1):
        if not isinstance(buf, bytes):
            buf = buf.encode('UTF-8')
        if buflen == -1:
            buflen = len(buf)
        (status, written) = self.write_chars(buf, buflen)
        return written

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    _whence_map = {0: GLib.SeekType.SET, 1: GLib.SeekType.CUR, 2: GLib.SeekType.END}

    def seek(self, offset, whence=0):
        try:
            w = self._whence_map[whence]
        except KeyError:
            raise ValueError("invalid 'whence' value")
        return self.seek_position(offset, w)

    def add_watch(self, condition, callback, *user_data, **kwargs):
        priority = kwargs.get('priority', GLib.PRIORITY_DEFAULT)
        return io_add_watch(self, priority, condition, callback, *user_data)

    add_watch = deprecated(add_watch, 'GLib.io_add_watch()')

    def __iter__(self):
        return self

    def __next__(self):
        (status, buf, length, terminator_pos) = self.read_line()
        if status == GLib.IOStatus.NORMAL:
            return buf
        raise StopIteration

    # Python 2.x compatibility
    next = __next__

IOChannel = override(IOChannel)
__all__.append('IOChannel')


class PollFD(GLib.PollFD):
    def __new__(cls, fd, events):
        pollfd = GLib.PollFD()
        pollfd.__class__ = cls
        return pollfd

    def __init__(self, fd, events):
        self.fd = fd
        self.events = events

PollFD = override(PollFD)
__all__.append('PollFD')


# The GI GLib API uses g_child_watch_add_full renamed to g_child_watch_add with
# a signature of (priority, pid, callback, data).
# Prior to PyGObject 3.8, this function was statically bound with an API closer to the
# non-full version with a signature of: (pid, callback, data=None, priority=GLib.PRIORITY_DEFAULT)
# We need to support this until we are okay with breaking API in a way which is
# not backwards compatible.
def _child_watch_add_get_args(priority_or_pid, pid_or_callback, *args, **kwargs):
    user_data = []

    if callable(pid_or_callback):
        warnings.warn('Calling child_watch_add without priority as first argument is deprecated',
                      PyGIDeprecationWarning)
        pid = priority_or_pid
        callback = pid_or_callback
        if len(args) == 0:
            priority = kwargs.get('priority', GLib.PRIORITY_DEFAULT)
        elif len(args) == 1:
            user_data = args
            priority = kwargs.get('priority', GLib.PRIORITY_DEFAULT)
        elif len(args) == 2:
            user_data = [args[0]]
            priority = args[1]
        else:
            raise TypeError('expected at most 4 positional arguments')
    else:
        priority = priority_or_pid
        pid = pid_or_callback
        if 'function' in kwargs:
            callback = kwargs['function']
            user_data = args
        elif len(args) > 0 and callable(args[0]):
            callback = args[0]
            user_data = args[1:]
        else:
            raise TypeError('expected callback as third argument')

    if 'data' in kwargs:
        if user_data:
            raise TypeError('got multiple values for "data" argument')
        user_data = [kwargs['data']]

    return priority, pid, callback, user_data

# we need this to be accessible for unit testing
__all__.append('_child_watch_add_get_args')


def child_watch_add(*args, **kwargs):
    """child_watch_add(priority, pid, function, *data)"""
    priority, pid, function, data = _child_watch_add_get_args(*args, **kwargs)
    return GLib.child_watch_add(priority, pid, function, *data)

__all__.append('child_watch_add')


def get_current_time():
    return GLib.get_real_time() * 0.000001

get_current_time = deprecated(get_current_time, 'GLib.get_real_time()')
"""get_current_time()

:returns: Time in seconds since the Epoch
:rtype: float

{{ docs }}
"""

__all__.append('get_current_time')


# backwards compatible API with default argument, and ignoring bytes_read
# output argument
def filename_from_utf8(utf8string, len=-1):
    return GLib.filename_from_utf8(utf8string, len)[0]

__all__.append('filename_from_utf8')


# backwards compatible API for renamed function
if not hasattr(GLib, 'unix_signal_add_full'):
    def add_full_compat(*args):
        warnings.warn('GLib.unix_signal_add_full() was renamed to GLib.unix_signal_add()',
                      PyGIDeprecationWarning)
        return GLib.unix_signal_add(*args)

    GLib.unix_signal_add_full = add_full_compat


# obsolete constants for backwards compatibility
glib_version = (GLib.MAJOR_VERSION, GLib.MINOR_VERSION, GLib.MICRO_VERSION)
__all__.append('glib_version')
deprecated_attr("GLib", "glib_version",
                "(GLib.MAJOR_VERSION, GLib.MINOR_VERSION, GLib.MICRO_VERSION)")

pyglib_version = version_info
__all__.append('pyglib_version')
deprecated_attr("GLib", "pyglib_version", "gi.version_info")
