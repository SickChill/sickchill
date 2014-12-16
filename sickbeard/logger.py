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

censoredItems = {}

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

# send logging to null
class NullFilter(logging.Filter):
    def filter(self, record):
        pass

class CensorFilter(logging.Filter):
    def filter(self, record):
        for k, v in censoredItems.items():
            if v and len(v) > 0 and v in record.msg:
                record.msg = record.msg.replace(v, len(v) * '*')
        return True

def initLogging(logFile=os.path.join(sickbeard.LOG_DIR, 'sickrage.log'), consoleLogging=False, fileLogging=False, debug=False):
    # Add a new logging level DB
    logging.addLevelName(DB, 'DB')

    # sickrage logger
    sr_log = logging.getLogger()
    sr_log.setLevel(DB)

    # tornado loggers
    logging.getLogger("tornado.access").addFilter(NullFilter())

    # console log handler
    if consoleLogging:
        console = logging.StreamHandler()
        console.addFilter(CensorFilter())
        console.setLevel(INFO if not debug else DEBUG)
        console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s::%(message)s', '%H:%M:%S'))
        sr_log.addHandler(console)

    # rotating log file handler
    if fileLogging:
        rfh = logging.handlers.RotatingFileHandler(logFile, maxBytes=1024 * 1024, backupCount=5, encoding='utf-8')
        rfh.addFilter(CensorFilter())
        rfh.setLevel(DEBUG)
        rfh.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S'))
        sr_log.addHandler(rfh)


def log(msg, level=INFO, *args, **kwargs):
    meThread = threading.currentThread().getName()
    message = meThread + u" :: " + msg

    logging.log(level, message, *args, **kwargs)
    if level == ERROR:
        classes.ErrorViewer.add(classes.UIError(message))

def log_error_and_exit(self, error_msg, *args, **kwargs):
    log(error_msg, ERROR, *args, **kwargs)

    if not self.consoleLogging:
        sys.exit(error_msg.encode(sickbeard.SYS_ENCODING, 'xmlcharrefreplace'))
    else:
        sys.exit(1)