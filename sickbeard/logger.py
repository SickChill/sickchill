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
import re
import sys
import logging
import logging.handlers
import threading
import platform

import sickbeard
from sickbeard import classes, encodingKludge as ek
from github import Github, InputFileContent

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


class CensoredFormatter(logging.Formatter, object):
    def __init__(self, *args, **kwargs):
        super(CensoredFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        msg = super(CensoredFormatter, self).format(record)
        for k, v in censoredItems.items():
            if v and len(v) > 0 and v in msg:
                msg = msg.replace(v, len(v) * '*')
        return msg


class Logger(object):
    def __init__(self):
        self.logger = logging.getLogger('sickrage')

        self.loggers = [
            logging.getLogger('sickrage'),
            logging.getLogger('tornado.general'),
            logging.getLogger('tornado.application'),
            # logging.getLogger('tornado.access'),
        ]

        self.consoleLogging = False
        self.fileLogging = False
        self.debugLogging = False
        self.logFile = None

    def initLogging(self, consoleLogging=False, fileLogging=False, debugLogging=False):
        self.logFile = self.logFile or os.path.join(sickbeard.LOG_DIR, 'sickrage.log')
        self.debugLogging = debugLogging
        self.consoleLogging = consoleLogging
        self.fileLogging = fileLogging

        # add a new logging level DB
        logging.addLevelName(DB, 'DB')

        # nullify root logger
        logging.getLogger().addHandler(NullHandler())

        # set custom root logger
        for logger in self.loggers:
            if logger is not self.logger:
                logger.root = self.logger
                logger.parent = self.logger

        # set minimum logging level allowed for loggers
        for logger in self.loggers:
            logger.setLevel(DB)

        # console log handler
        if self.consoleLogging:
            console = logging.StreamHandler()
            console.setFormatter(CensoredFormatter('%(asctime)s %(levelname)s::%(message)s', '%H:%M:%S'))
            console.setLevel(INFO if not self.debugLogging else DEBUG)

            for logger in self.loggers:
                logger.addHandler(console)

        # rotating log file handler
        if self.fileLogging:
            rfh = logging.handlers.RotatingFileHandler(self.logFile, maxBytes=sickbeard.LOG_SIZE, backupCount=sickbeard.LOG_NR, encoding='utf-8')
            rfh.setFormatter(CensoredFormatter('%(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S'))
            rfh.setLevel(DEBUG)

            for logger in self.loggers:
                logger.addHandler(rfh)

    def log(self, msg, level=INFO, *args, **kwargs):
        meThread = threading.currentThread().getName()
        message = meThread + u" :: " + msg

        # pass exception information if debugging enabled

        if level == ERROR:
            self.logger.exception(message, *args, **kwargs)
            classes.ErrorViewer.add(classes.UIError(message))

            # if sickbeard.GIT_AUTOISSUES:
            #    self.submit_errors()
        else:
            self.logger.log(level, message, *args, **kwargs)

    def log_error_and_exit(self, error_msg, *args, **kwargs):
        self.log(error_msg, ERROR, *args, **kwargs)

        if not self.consoleLogging:
            sys.exit(error_msg.encode(sickbeard.SYS_ENCODING, 'xmlcharrefreplace'))
        else:
            sys.exit(1)

    def submit_errors(self):
        if not (sickbeard.GIT_USERNAME and sickbeard.GIT_PASSWORD and len(classes.ErrorViewer.errors) > 0):
            return

        gh_org = sickbeard.GIT_ORG or 'SiCKRAGETV'
        gh_repo = 'sickrage-issues'

        gh = Github(login_or_token=sickbeard.GIT_USERNAME, password=sickbeard.GIT_PASSWORD, user_agent="SiCKRAGE")

        try:
            # read log file
            log_data = None
            if self.logFile and os.path.isfile(self.logFile):
                with ek.ek(open, self.logFile) as f:
                    log_data = f.readlines()
                log_data = [line for line in reversed(log_data)]

            # parse and submit errors to issue tracker
            for curError in sorted(classes.ErrorViewer.errors, key=lambda error: error.time, reverse=True)[:500]:
                if not curError.title:
                    continue

                gist = None
                regex = "^(%s)\s*([A-Z]+)\s*(.+?)\s*\:\:\s*(.*)$" % curError.time
                for i, x in enumerate(log_data):
                    x = ek.ss(x)
                    match = re.match(regex, x)
                    if match:
                        level = match.group(2)
                        if reverseNames[level] == ERROR:
                            paste_data = "".join(log_data[i:i+50])
                            if paste_data:
                                gist = gh.get_user().create_gist(True, {"sickrage.log": InputFileContent(paste_data)})
                            break

                message = u"### INFO\n"
                message += u"Python Version: **" + sys.version[:120] + "**\n"
                message += u"Operating System: **" + platform.platform() + "**\n"
                message += u"Branch: **" + sickbeard.BRANCH + "**\n"
                message += u"Commit: SiCKRAGETV/SickRage@" + sickbeard.CUR_COMMIT_HASH + "\n"
                if gist:
                    message += u"Link to Log: " + gist.html_url + "\n"
                message += u"### ERROR\n"
                message += u"```\n"
                message += curError.message + "\n"
                message += u"```\n"
                message += u"---\n"
                message += u"_STAFF NOTIFIED_: @SiCKRAGETV/owners @SiCKRAGETV/moderators"

                issue = gh.get_organization(gh_org).get_repo(gh_repo).create_issue("[APP SUBMITTED]: " + str(curError.title), message)
                if issue:
                    self.log('Your issue ticket #%s was submitted successfully!' % issue.number)

                # clear error from error list
                classes.ErrorViewer.errors.remove(curError)

                return issue
        except Exception as e:
            self.log(sickbeard.exceptions.ex(e), ERROR)


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

