# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

# File based on work done by Medariox

import inspect
import re

import rtorrent
from rtorrent.common import (bool_to_int, convert_version_tuple_to_str,
                             safe_repr)
from rtorrent.compat import xmlrpclib
from rtorrent.err import MethodError


def get_varname(rpc_call):
    """Transform rpc method into variable name.

    @newfield example: Example
    @example: if the name of the rpc method is 'p.down_rate', the variable
    name will be 'down_rate'
    """
    # extract variable name from xmlrpc func name
    r = re.match(r'(?:[ptdf]\.)?(.+?)(?:\.set)?$', rpc_call)
    if r:
        return(r.group(1))

    return(None)


def _handle_unavailable_rpc_method(method, rt_obj):
    msg = "Method isn't available."
    if rt_obj._get_client_version_tuple() < method.min_version:
        msg = 'This method is only available in ' \
            'RTorrent version v{0} or later'.format(
                convert_version_tuple_to_str(method.min_version))

    raise MethodError(msg)


class DummyClass:
    def __init__(self):
        pass


class Method:
    """Represents an individual RPC method."""

    def __init__(self, _class, method_name,
                 rpc_call, docstring=None, varname=None, **kwargs):
        self._class = _class  # : Class this method is associated with
        self.class_name = _class.__name__
        self.method_name = method_name  # : name of public-facing method
        self.rpc_call = rpc_call  # : name of rpc method
        self.docstring = docstring  # : docstring for rpc method (optional)
        self.varname = varname  # : variable for the result of the method call, usually set to self.varname
        self.min_version = kwargs.get('min_version', (
            0, 0, 0))  # : Minimum version of rTorrent required
        self.boolean = kwargs.get('boolean', False)  # : returns boolean value?
        self.post_process_func = kwargs.get(
            'post_process_func', None)  # : custom post process function
        self.aliases = kwargs.get(
            'aliases', [])  # : aliases for method (optional)
        self.required_args = []  #: Arguments required when calling the method (not utilized)

        self.method_type = self._get_method_type()

        if self.varname is None:
            self.varname = get_varname(self.rpc_call)
        assert self.varname is not None, "Couldn't get variable name."

    def __repr__(self):
        return safe_repr("Method(method_name='{0}', rpc_call='{1}')",
                         self.method_name, self.rpc_call)

    def _get_method_type(self):
        """Determine whether method is a modifier or a retriever."""
        if self.method_name[:4] == 'set_':
            return('m')  # modifier
        else:
            return('r')  # retriever

    def is_modifier(self):
        if self.method_type == 'm':
            return(True)
        else:
            return(False)

    def is_retriever(self):
        if self.method_type == 'r':
            return(True)
        else:
            return(False)

    def is_available(self, rt_obj):
        if rt_obj._get_client_version_tuple() < self.min_version or \
                self.rpc_call not in rt_obj._get_rpc_methods():
            return(False)
        else:
            return(True)


class Multicall:
    def __init__(self, class_obj, **kwargs):
        self.class_obj = class_obj
        if class_obj.__class__.__name__ == 'RTorrent':
            self.rt_obj = class_obj
        else:
            self.rt_obj = class_obj._rt_obj
        self.calls = []

    def add(self, method, *args):
        """Add call to multicall.

        @param method: L{Method} instance or name of raw RPC method
        @type method: Method or str

        @param args: call arguments
        """
        # if a raw rpc method was given instead of a Method instance,
        # try and find the instance for it. And if all else fails, create a
        # dummy Method instance
        if isinstance(method, str):
            result = find_method(method)
            # if result not found
            if result == -1:
                method = Method(DummyClass, method, method)
            else:
                method = result

        # ensure method is available before adding
        if not method.is_available(self.rt_obj):
            _handle_unavailable_rpc_method(method, self.rt_obj)

        self.calls.append((method, args))

    def list_calls(self):
        for c in self.calls:
            print(c)

    def call(self):
        """Execute added multicall calls.

        @return: the results (post-processed), in the order they were added
        @rtype: tuple
        """
        m = xmlrpclib.MultiCall(self.rt_obj._get_conn())
        for call in self.calls:
            method, args = call
            rpc_call = getattr(method, 'rpc_call')
            getattr(m, rpc_call)(*args)

        results = m()
        results = tuple(results)
        results_processed = []

        for r, c in zip(results, self.calls):
            method = c[0]  # Method instance
            result = process_result(method, r)
            results_processed.append(result)
            # assign result to class_obj
            exists = hasattr(self.class_obj, method.varname)
            if not exists or not inspect.ismethod(getattr(self.class_obj, method.varname)):
                setattr(self.class_obj, method.varname, result)

        return(tuple(results_processed))


def call_method(class_obj, method, *args):
    """Handle single RPC calls.

    @param class_obj: Peer/File/Torrent/Tracker/RTorrent instance
    @type class_obj: object

    @param method: L{Method} instance or name of raw RPC method
    @type method: Method or str
    """
    if method.is_retriever():
        args = args[:-1]
    else:
        assert args[-1] is not None, 'No argument given.'

    if class_obj.__class__.__name__ == 'RTorrent':
        rt_obj = class_obj
    else:
        rt_obj = class_obj._rt_obj

    # check if rpc method is even available
    if not method.is_available(rt_obj):
        _handle_unavailable_rpc_method(method, rt_obj)

    m = Multicall(class_obj)
    m.add(method, *args)
    # only added one method, only getting one result back
    ret_value = m.call()[0]

    return(ret_value)


def find_method(rpc_call):
    """Return L{Method} instance associated with given RPC call."""
    method_lists = [
        rtorrent.methods,
        rtorrent.file.methods,
        rtorrent.tracker.methods,
        rtorrent.peer.methods,
        rtorrent.torrent.methods,
    ]

    for l in method_lists:
        for m in l:
            if m.rpc_call.lower() == rpc_call.lower():
                return(m)

    return(-1)


def process_result(method, result):
    """Process given C{B{result}} based on flags set in C{B{method}}.

    @param method: L{Method} instance
    @type method: Method

    @param result: result to be processed (the result of given L{Method} instance)

    @note: Supported Processing:
        - boolean - convert ones and zeros returned by rTorrent and
        convert to python boolean values
    """
    # handle custom post processing function
    if method.post_process_func is not None:
        result = method.post_process_func(result)

    # is boolean?
    if method.boolean:
        if result in [1, '1']:
            result = True
        elif result in [0, '0']:
            result = False

    return(result)


def _build_rpc_methods(class_, method_list):
    """Build glorified aliases to raw RPC methods."""
    instance = None
    if not inspect.isclass(class_):
        instance = class_
        class_ = instance.__class__

    for m in method_list:
        class_name = m.class_name
        if class_name != class_.__name__:
            continue

        if class_name == 'RTorrent':
            caller = lambda self, arg = None, method = m:\
                call_method(self, method, bool_to_int(arg))
        elif class_name == 'Torrent':
            caller = lambda self, arg = None, method = m:\
                call_method(self, method, self.rpc_id,
                            bool_to_int(arg))
        elif class_name in ['Tracker', 'File']:
            caller = lambda self, arg = None, method = m:\
                call_method(self, method, self.rpc_id,
                            bool_to_int(arg))

        elif class_name == 'Peer':
            caller = lambda self, arg = None, method = m:\
                call_method(self, method, self.rpc_id,
                            bool_to_int(arg))

        elif class_name == 'Group':
            caller = lambda arg = None, method = m: \
                call_method(instance, method, bool_to_int(arg))

        if m.docstring is None:
            m.docstring = ''

        # print(m)
        docstring = """{0}

        @note: Variable where the result for this method is stored: {1}.{2}""".format(
            m.docstring,
            class_name,
            m.varname)

        caller.__doc__ = docstring

        for method_name in [m.method_name] + list(m.aliases):
            if instance is None:
                setattr(class_, method_name, caller)
            else:
                setattr(instance, method_name, caller)
