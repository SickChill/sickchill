# Copyright 2012,2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re
import traceback

from ..util import ResultTuple
from .backend import list_backends, get_backend
from .utils import CodeBlock
from pgi.util import escape_identifier, escape_parameter, cache_return
from .arguments import get_argument_class, ErrorArgument
from .returnvalues import get_return_class
from pgi._compat import string_types, PY3
from pgi.clib.gir import GICallableInfo, GIFunctionInfo, GIFunctionInfoFlags
from pgi.clib.gir import GIRepository


@cache_return
def may_be_null_is_nullable():
    """If may_be_null returns nullable or if NULL can be passed in.

    This can still be wrong if the specific typelib is older than the linked
    libgirepository.

    https://bugzilla.gnome.org/show_bug.cgi?id=660879#c47
    """

    repo = GIRepository()
    repo.require("GLib", "2.0", 0)
    info = repo.find_by_name("GLib", "spawn_sync")
    # this argument is (allow-none) and can never be (nullable)
    return not info.get_arg(8).may_be_null


def get_type_name(type_):
    """Gives a name for a type that is suitable for a docstring.

    int -> "int"
    Gtk.Window -> "Gtk.Window"
    [int] -> "[int]"
    {int: Gtk.Button} -> "{int: Gtk.Button}"
    """

    if type_ is None:
        return ""
    if isinstance(type_, string_types):
        return type_
    elif isinstance(type_, list):
        assert len(type_) == 1
        return "[%s]" % get_type_name(type_[0])
    elif isinstance(type_, dict):
        assert len(type_) == 1
        key, value = list(type_.items())[0]
        return "{%s: %s}" % (get_type_name(key), get_type_name(value))
    elif type_.__module__ in ("__builtin__", "builtins"):
        return type_.__name__
    else:
        return "%s.%s" % (type_.__module__, type_.__name__)


def get_signal_owner_var_name(type_):
    tname = get_type_name(type_.pytype)
    name = tname.rsplit(".", 1)[-1]
    return "_".join([p.lower() for p in re.findall('[A-Z][^A-Z]*', name)])


def build_docstring(func_name, args, ret, throws, signal_owner_type=None):
    """Create a docstring in the form:
        name(in_name: type) -> (ret_type, out_name: type)
    """

    out_args = []
    if ret and not ret.ignore:
        if ret.py_type is None:
            out_args.append("unknown")
        else:
            tname = get_type_name(ret.py_type)
            if ret.may_return_null:
                tname += " or None"
            out_args.append(tname)

    in_args = []

    if signal_owner_type is not None:
        name = get_signal_owner_var_name(signal_owner_type)
        in_args.append("%s: %s" % (
            name, get_type_name(signal_owner_type.pytype)))

    for arg in args:
        if arg.is_aux:
            continue

        if arg.is_direction_in():
            if arg.py_type is None:
                in_args.append(arg.in_var)
            else:
                tname = get_type_name(arg.py_type)
                if arg.may_be_null:
                    tname += " or None"
                in_args.append("%s: %s" % (arg.in_var, tname))

        if arg.is_direction_out():
            if arg.py_type is None:
                out_args.append(arg.name)
            else:
                tname = get_type_name(arg.py_type)
                # if may_be_null means the arg is nullable, it is nullable
                # and the marshalling returns None for a NULL pointer
                if may_be_null_is_nullable() and arg.may_be_null and \
                        arg.can_unpack_none:
                    tname += " or None"
                # When can we assume that out args return None?
                out_args.append("%s: %s" % (arg.name, tname))

    in_def = ", ".join(in_args)

    if not out_args:
        out_def = "None"
    elif len(out_args) == 1:
        out_def = out_args[0]
    else:
        out_def = "(%s)" % ", ".join(out_args)

    error = ""
    if throws:
        error = "raises "

    return "%s(%s) %s-> %s" % (func_name, in_def, error, out_def)


def _generate_function(backend, info, arg_infos, arg_types,
                       return_type, method):

    args = []
    for arg_info, arg_type in zip(arg_infos, arg_types):
        cls = get_argument_class(arg_type)
        name = escape_identifier(arg_info.name)
        args.append(cls(name, args, backend, arg_info, arg_type))

    cls = get_return_class(return_type)
    return_value = cls(info, return_type, args, backend)
    throws = info.flags.value & GIFunctionInfoFlags.THROWS

    if throws:
        args.append(ErrorArgument(args, backend))

    # setup
    for arg in args:
        arg.setup()

    return_value.setup()

    # in args
    in_args = [a for a in args if not a.is_aux and a.in_var]

    # set description used for exceptions
    for i, arg in enumerate(in_args):
        arg.desc = "%s() argument '%s'(%d)" % (info.name, arg.in_var, i + 1)

    # if the last in argument is a user data, make it a positional argument
    if in_args and in_args[-1].is_userdata:
        name = in_args[-1].in_var
        in_args[-1].in_var = "*" + name

    in_names = [a.in_var for a in in_args]

    var_fac = backend.var
    var_fac.add_blacklist([n.strip("*") for n in in_names])
    self_name = ""
    if method:
        self_name = var_fac.request_name("self")
        in_names.insert(0, self_name)
    in_names = ", ".join(in_names)

    # pre call
    body = CodeBlock()
    for arg in args:
        if arg.is_aux or arg.is_userdata:
            continue
        block = arg.pre_call()
        if block:
            block.write_into(body)

    block = return_value.pre_call()
    if block:
        block.write_into(body)

    # generate call
    lib = backend.get_library(info.namespace)
    symbol = info.symbol
    block, func = backend.get_function(lib, symbol, args,
                                       return_value, method,
                                       throws)
    if block:
        block.write_into(body)

    # do the call
    call_vars = [a.call_var for a in args if a.call_var]
    if method:
        # there are not unbound method in Python 3 and also no
        # type checking for the "self" object, but at least raise
        # TypeError if getting the pointer value fails which
        # should cover most cases

        if PY3:
            block, var = backend.parse("""
try:
    $ptr = %s._obj
except AttributeError:
    raise TypeError
""" % self_name)
        else:
            block, var = backend.parse("$ptr = %s._obj" % self_name)
        block.write_into(body)

        call_vars.insert(0, var["ptr"])
    call_block, var = backend.parse("$ret = $func($args)",
                                    func=func, args=", ".join(call_vars))
    call_block.write_into(body)
    ret = var["ret"]

    out = []

    # handle errors first
    if throws:
        error_arg = args.pop()
        block = error_arg.post_call()
        if block:
            block.write_into(body)

    # process return value
    if not return_value.ignore:
        block, return_var = return_value.post_call(ret)
        assert return_var
        if block:
            block.write_into(body)
        out.append((return_var, None))

    # process out args
    for arg in args:
        if arg.is_aux or arg.is_userdata:
            continue
        block = arg.post_call()
        if block:
            block.write_into(body)
        if arg.out_var:
            out.append((arg.out_var, arg.name))

    if len(out) == 1:
        body.write_line("return %s" % out[0][0])
    elif len(out) > 1:
        # for more than one value use a named tuple.
        out_vars, out_names = zip(*out)
        ntuple = ResultTuple._new_type(out_names)
        block, var = backend.parse("""
return $ntuple((%s))
""" % ", ".join(out_vars), ntuple=ntuple)
        block.write_into(body)

    # build final function block

    func_name = escape_identifier(info.name)

    docstring = build_docstring(func_name, args, return_value, throws)

    main, var = backend.parse("""
# backend: $backend_name
def $func_name($func_args):
    '''$docstring'''

    $func_body
""", backend_name=backend.NAME, func_args=in_names, docstring=docstring,
     func_body=body, func_name=func_name)

    func = main.compile()[func_name]
    func._code = main
    func.__doc__ = docstring
    func.__module__ = info.namespace

    return func


def generate_function(info, method=False):
    """Creates a Python callable for a GIFunctionInfo instance"""

    assert isinstance(info, GIFunctionInfo)

    arg_infos = list(info.get_args())
    arg_types = [a.get_type() for a in arg_infos]
    return_type = info.get_return_type()

    func = None
    messages = []
    for backend in list_backends():
        instance = backend()
        try:
            func = _generate_function(instance, info, arg_infos, arg_types,
                                      return_type, method)
        except NotImplementedError:
            messages.append("%s: %s" % (backend.NAME, traceback.format_exc()))
        else:
            break

    if func:
        return func

    raise NotImplementedError("\n".join(messages))


def generate_dummy_callable(info, func_name, method=False,
                            signal_owner_type=None):
    """Takes a GICallableInfo and generates a dummy callback function which
    just raises but has a correct docstring. They are mainly accessible for
    documentation, so the API reference can reference a real thing.

    func_name can be different than info.name because vfuncs, for example,
    get prefixed with 'do_' when exposed in Python.
    """

    assert isinstance(info, GICallableInfo)

    # FIXME: handle out args and trailing user_data ?

    arg_infos = list(info.get_args())
    arg_types = [a.get_type() for a in arg_infos]
    return_type = info.get_return_type()

    # the null backend is good enough here
    backend = get_backend("null")()

    args = []
    for arg_info, arg_type in zip(arg_infos, arg_types):
        cls = get_argument_class(arg_type)
        name = escape_identifier(arg_info.name)
        name = escape_parameter(name)
        args.append(cls(name, args, backend, arg_info, arg_type))

    cls = get_return_class(return_type)
    return_value = cls(info, return_type, args, backend)

    for arg in args:
        arg.setup()

    return_value.setup()

    func_name = escape_identifier(func_name)
    docstring = build_docstring(func_name, args, return_value,
                                False, signal_owner_type)

    in_args = [a for a in args if not a.is_aux and a.in_var]
    in_names = [a.in_var for a in in_args]

    var_fac = backend.var
    var_fac.add_blacklist(in_names)
    self_name = ""
    if method:
        self_name = var_fac.request_name("self")
        in_names.insert(0, self_name)

    main, var = backend.parse("""
def $func_name($func_args):
    '''$docstring'''

    raise NotImplementedError("This is just a dummy callback function")
""", func_args=", ".join(in_names), docstring=docstring, func_name=func_name)

    func = main.compile()[func_name]
    func._code = main
    func.__doc__ = docstring
    func.__module__ = info.namespace

    return func
