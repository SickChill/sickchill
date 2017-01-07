# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .backend import get_backend
from .utils import CodeBlock
from .cbargs import get_cbarg_class
from .cbreturn import get_cbreturn_class
from pgi.util import escape_identifier, escape_parameter


def build_docstring(cb_name, args):
    parts = []
    for arg in args:
        if arg.py_type is None:
            parts.append(arg.name)
        else:
            parts.append("%s: %s" % (arg.name, arg.py_type.__name__))

    return "%s(%s) -> None" % (cb_name, ", ".join(parts))


def generate_callback_wrapper(info):
    backend = get_backend("ctypes")()

    args = list(info.get_args())
    arg_types = [a.get_type() for a in args]

    ret_type = info.get_return_type()
    cls = get_cbreturn_class(ret_type)
    return_value = cls(backend, info, ret_type)

    cb_args = []
    for arg, type_ in zip(args, arg_types):
        cls = get_cbarg_class(type_)
        excaped_name = escape_identifier(arg.name)
        cb_arg = cls(backend, arg, type_, excaped_name)
        cb_args.append(cb_arg)

    for arg in cb_args:
        arg.setup()

    body = CodeBlock()

    outs_vars = []
    for arg in cb_args:
        if arg.is_aux:
            continue
        block, out = arg.process()
        if block:
            block.write_into(body)
        outs_vars.append(out)

    arg_names = [a.name for a in cb_args]
    backend.var.add_blacklist(arg_names)

    argument_list = ", ".join(arg_names)
    forward_arguments = ", ".join(outs_vars)
    func_name = escape_parameter(info.name)
    cb_name = backend.var()

    return_var = backend.var()
    return_block, out_var = return_value.process(return_var)
    return_block = return_block or CodeBlock()

    docstring = build_docstring(func_name, cb_args)

    block, var = backend.parse("""
def $cb_wrapper($args):
    $body
    # $docstring
    $ret = $callback($out_args)
    $post
    return $out
""", args=argument_list, out_args=forward_arguments, cb_wrapper=func_name,
     callback=cb_name, body=body, docstring=docstring, ret=return_var,
     out=out_var, post=return_block)

    def create_cb_for_func(real_func):
        if real_func is not None:
            # binds the callback to the block and compiles it
            func = block.compile(**{cb_name: real_func})[func_name]
        else:
            func = None
        return backend.get_callback(func, cb_args, return_value)

    return create_cb_for_func, docstring


def _generate_signal_callback(backend, info, args, arg_types):
    sig_args = []

    ret_type = info.get_return_type()
    cls = get_cbreturn_class(ret_type)
    return_value = cls(backend, info, ret_type)

    for arg, type_ in zip(args, arg_types):
        cls = get_cbarg_class(type_)
        excaped_name = escape_identifier(arg.name)
        sig_arg = cls(backend, arg, type_, excaped_name)
        sig_args.append(sig_arg)

    for arg in sig_args:
        arg.setup()

    body = CodeBlock()

    outs_vars = []
    for arg in sig_args:
        if arg.is_aux:
            continue
        block, out = arg.process()
        if block:
            block.write_into(body)
        outs_vars.append(out)

    argument_list = ", ".join([a.name for a in sig_args])
    forward_arguments = ", ".join(outs_vars)
    func_name = escape_parameter(info.name)
    cb_name = backend.var()

    return_var = backend.var()
    return_block, out_var = return_value.process(return_var)
    return_block = return_block or CodeBlock()

    block, var = backend.parse("""
def $cb_wrapper($dummy, $args):
    $body
    $ret = $callback($out_args)
    $post
    return $out
""", args=argument_list, out_args=forward_arguments, cb_wrapper=func_name,
     callback=cb_name, body=body, post=return_block, out=out_var,
     ret=return_var)

    def create_sig_for_func(real_func):
        f = block.compile(**{cb_name: real_func})[func_name]
        return backend.get_callback(f, sig_args, return_value, is_signal=True)

    return create_sig_for_func


def generate_signal_callback(info):
    args = list(info.get_args())
    arg_types = [a.get_type() for a in args]
    backend = get_backend("ctypes")()

    cb_func = None
    try:
        cb_func = _generate_signal_callback(backend, info, args, arg_types)
    except NotImplementedError:
        raise

    return cb_func
