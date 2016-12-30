# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from ._compat import PY3
from .util import cached_property


class PGError(RuntimeError):

    _error = None

    @classmethod
    def _from_gerror(cls, error, own=True):
        """Creates a GError exception and takes ownership if own is True"""

        if not own:
            error = error.copy()

        self = cls()
        self._error = error
        return self

    @cached_property
    def message(self):
        if self._error:
            message = self._error.contents.message
            if PY3 and message is not None:
                message = message.decode("utf-8")
            return message

    @cached_property
    def domain(self):
        if self._error:
            return self._error.contents.domain.string

    @cached_property
    def code(self):
        if self._error:
            return self._error.contents.code

    def __str__(self):
        message = self.message
        if message is None:
            # base case without error set
            return super(PGError, self).__str__()
        return message

    def __del__(self):
        if self._error:
            self._error.free()


PGError.__module__ = "GLib"
PGError.__name__ = "Error"
