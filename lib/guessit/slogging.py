#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
#
# GuessIt is free software; you can redistribute it and/or modify it under
# the terms of the Lesser GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# GuessIt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function, unicode_literals
from functools import wraps

import logging
import sys
import os

log = logging.getLogger(__name__)

GREEN_FONT = "\x1B[0;32m"
YELLOW_FONT = "\x1B[0;33m"
BLUE_FONT = "\x1B[0;34m"
RED_FONT = "\x1B[0;31m"
RESET_FONT = "\x1B[0m"


def setup_logging(colored=True, with_time=False, with_thread=False, filename=None, with_lineno=False):  # pragma: no cover
    """Set up a nice colored logger as the main application logger."""

    class SimpleFormatter(logging.Formatter):
        def __init__(self, with_time, with_thread):
            self.fmt = (('%(asctime)s ' if with_time else '') +
                        '%(levelname)-8s ' +
                        '[%(name)s:%(funcName)s' +
                        (':%(lineno)s' if with_lineno else '') + ']' +
                        ('[%(threadName)s]' if with_thread else '') +
                        ' -- %(message)s')
            logging.Formatter.__init__(self, self.fmt)

    class ColoredFormatter(logging.Formatter):
        def __init__(self, with_time, with_thread):
            self.fmt = (('%(asctime)s ' if with_time else '') +
                        '-CC-%(levelname)-8s ' +
                        BLUE_FONT + '[%(name)s:%(funcName)s' +
                        (':%(lineno)s' if with_lineno else '') + ']' +
                        RESET_FONT + ('[%(threadName)s]' if with_thread else '') +
                        ' -- %(message)s')

            logging.Formatter.__init__(self, self.fmt)

        def format(self, record):
            modpath = record.name.split('.')
            record.mname = modpath[0]
            record.mmodule = '.'.join(modpath[1:])
            result = logging.Formatter.format(self, record)
            if record.levelno == logging.DEBUG:
                color = BLUE_FONT
            elif record.levelno == logging.INFO:
                color = GREEN_FONT
            elif record.levelno == logging.WARNING:
                color = YELLOW_FONT
            else:
                color = RED_FONT

            result = result.replace('-CC-', color)
            return result

    if filename is not None:
        # make sure we can write to our log file
        logdir = os.path.dirname(filename)
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        ch = logging.FileHandler(filename, mode='w')
        ch.setFormatter(SimpleFormatter(with_time, with_thread))
    else:
        ch = logging.StreamHandler()
        if colored and sys.platform != 'win32':
            ch.setFormatter(ColoredFormatter(with_time, with_thread))
        else:
            ch.setFormatter(SimpleFormatter(with_time, with_thread))

    logging.getLogger().addHandler(ch)


def trace_func_call(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        is_method = (f.__name__ != f.__qualname__)  # method is still not bound, we need to get around it
        if is_method:
            no_self_args = args[1:]
        else:
            no_self_args = args

        args_str = ', '.join(repr(arg) for arg in no_self_args)
        kwargs_str = ', '.join('{}={}'.format(k, v) for k, v in kwargs.items())
        if not args_str:
            args_str = kwargs_str
        elif not kwargs_str:
            args_str = args_str
        else:
            args_str = '{}, {}'.format(args_str, kwargs_str)

        log.debug('Calling {}({})'.format(f.__name__, args_str))
        return f(*args, **kwargs)

    return wrapper
