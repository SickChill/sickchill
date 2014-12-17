# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement
import os

import sys
import logging
import logging.handlers
import threading

import sickbeard
from sickbeard import classes

# log levels
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
DB = 5

reverseNames = {u'ERROR': ERROR,
                u'WARNING': WARNING,
                u'INFO': INFO,
                u'DEBUG': DEBUG,
                u'DB': DB}

censoredItems = {}

class NullHandler(logging.Handler):
    def emit(self, record):
        pass


class NullFilter(logging.Filter):
    def filter(self, record):
        pass


class CensorLoggingAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        for k, v in self.extra.items():
            if v and len(v) > 0 and v in msg:
                msg = msg.replace(v, len(v) * '*')
        return msg, kwargs


class Logger(object):
    def __init__(self):
        self.logger = CensorLoggingAdapter(logging.getLogger('sickrage'), censoredItems)
        self.consoleLogging = False
        self.fileLogging = False
        self.debugLogging = False
        self.logFile = None

    def initLogging(self, consoleLogging=False, fileLogging=False, debugLogging=False):
        # set logging filename
        if not self.logFile:
            self.logFile = os.path.join(sickbeard.LOG_DIR, 'sickrage.log')

        # add a new logging level DB
        logging.addLevelName(DB, 'DB')

        # don't propergate to root logger
        logging.getLogger('sickrage').propagate = False

        # set minimum logging level allowed
        logging.getLogger('sickrage').setLevel(DB)

        # console log handler
        if consoleLogging:
            console = logging.StreamHandler()
            console.setLevel(INFO if not debugLogging else DEBUG)
            console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s::%(message)s', '%H:%M:%S'))
            logging.getLogger('sickrage').addHandler(console)

        # rotating log file handler
        if fileLogging:
            rfh = logging.handlers.RotatingFileHandler(self.logFile, maxBytes=1024 * 1024, backupCount=5, encoding='utf-8')
            rfh.setLevel(DEBUG)
            rfh.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S'))
            logging.getLogger('sickrage').addHandler(rfh)

    def log(self, msg, level=INFO, *args, **kwargs):
        meThread = threading.currentThread().getName()
        message = meThread + u" :: " + msg

        self.logger.log(level, message, *args, **kwargs)
        if level == ERROR:
            classes.ErrorViewer.add(classes.UIError(message))

    def log_error_and_exit(self, error_msg, *args, **kwargs):
        self.log(error_msg, ERROR, *args, **kwargs)

        if not self.consoleLogging:
            sys.exit(error_msg.encode(sickbeard.SYS_ENCODING, 'xmlcharrefreplace'))
        else:
            sys.exit(1)

class Wrapper(object):
    instance = Logger()

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):
        try:
            return getattr(self.wrapped, name)
        except AttributeError:
            return getattr(self.instance, name)

_globals = sys.modules[__name__] = Wrapper(sys.modules[__name__])

