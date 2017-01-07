# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ctypes import byref

from .util import cached_property, escape_parameter, decode_return
from .clib.glib import guint
from .clib.gobject import signal_list_ids, signal_query, GSignalQuery
from .codegen import generate_dummy_callable
from .gtype import PGType


class GSignal(object):
    def __init__(self, info, signal_id):
        self._id = signal_id
        self._info = info

    @property
    def _func(self):
        try:
            sig_info = self._info.find_signal(self._query.signal_name)
        except AttributeError:
            # older libgirepository
            sig_info = None

        if sig_info:
            func_name = sig_info.name.replace("-", "_")
            return generate_dummy_callable(
                sig_info, func_name, signal_owner_type=self.instance_type)
        else:
            # FIXME: either too old libgirepository or signal
            # that is not in the typelib.
            f = lambda: None
            f.__doc__ = "%s()" % self.name.replace("-", "_")
            return f

    @property
    def __doc__(self):
        return self._func.__doc__

    def __call__(self, *args, **kwargs):
        assert self._func
        return self._func(*args, **kwargs)

    @cached_property
    def _query(self):
        query = GSignalQuery()
        signal_query(self._id, byref(query))
        return query

    @property
    def id(self):
        return self._query.signal_id

    @property
    @decode_return()
    def name(self):
        return self._query.signal_name

    @property
    def instance_type(self):
        return PGType(self._query.itype)

    @property
    def return_type(self):
        return PGType(self._query.return_type)

    @property
    def flags(self):
        return self._query.signal_flags.value

    @property
    def param_types(self):
        count = int(self._query.n_params)
        return [PGType(t) for t in self._query.param_types[:count]]


class _GSignalQuery(object):
    def __init__(self, info, pgtype):
        # FIXME: DBusGLib.Proxy ?
        if pgtype == PGType.from_name("void"):
            return

        gtype = pgtype._type
        is_interface = pgtype.is_interface()

        def get_sig_ids(gtype):
            length = guint()
            array = signal_list_ids(gtype, byref(length))
            return array[:length.value]

        if is_interface:
            iface = gtype.default_interface_ref()
            sig_ids = get_sig_ids(gtype)
            gtype.default_interface_unref(iface)
        else:
            klass = gtype.class_ref()
            sig_ids = get_sig_ids(gtype)
            gtype.class_unref(klass)

        for id_ in sig_ids:
            sig = GSignal(info, id_)
            setattr(self, escape_parameter(sig.name), sig)

_GSignalQuery.__name__ = "GSignalQuery"


class SignalsDescriptor(object):

    def __init__(self, info):
        self.info = info

    def __get__(self, instance, owner):
        return _GSignalQuery(self.info, owner.__gtype__)


def SignalsAttribute(info):
    return SignalsDescriptor(info)
