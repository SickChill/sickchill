# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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


import io
import os
import re
import sys
import logging
import logging.handlers
import threading
import platform
import locale
import traceback

from github import Github, InputFileContent

import sickbeard
from sickbeard import classes
from sickrage.helper.common import dateTimeFormat
from sickrage.helper.exceptions import ex
from sickrage.helper.encoding import ss


# log levels
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
DB = 5

reverseNames = {
    u'ERROR': ERROR,
    u'WARNING': WARNING,
    u'INFO': INFO,
    u'DEBUG': DEBUG,
    u'DB': DB
}

censoredItems = {}


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


class CensoredFormatter(logging.Formatter, object):
    def __init__(self, fmt=None, datefmt=None, encoding='utf-8'):
        super(CensoredFormatter, self).__init__(fmt, datefmt)
        self.encoding = encoding

    def format(self, record):
        """Strips censored items from string"""
        msg = super(CensoredFormatter, self).format(record)

        if not isinstance(msg, unicode):
            msg = msg.decode(self.encoding, 'replace') # Convert to unicode

        for _, v in censoredItems.iteritems():
            if not isinstance(v, unicode):
                v = v.decode(self.encoding, 'replace') # Convert to unicode
            msg = msg.replace(v, len(v) * u'*')

        # Needed because Newznab apikey isn't stored as key=value in a section.
        msg = re.sub(ur'([&?]r|[&?]apikey|[&?]api_key)=[^&]*([&\w]?)', ur'\1=**********\2', msg)
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

        self.submitter_running = False

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
            console.setFormatter(CensoredFormatter(u'%(asctime)s %(levelname)s::%(message)s', '%H:%M:%S', encoding='utf-8'))
            console.setLevel(INFO if not self.debugLogging else DEBUG)

            for logger in self.loggers:
                logger.addHandler(console)

        # rotating log file handler
        if self.fileLogging:
            rfh = logging.handlers.RotatingFileHandler(self.logFile, maxBytes=sickbeard.LOG_SIZE, backupCount=sickbeard.LOG_NR, encoding='utf-8')
            rfh.setFormatter(CensoredFormatter(u'%(asctime)s %(levelname)-8s %(message)s', dateTimeFormat, encoding='utf-8'))
            rfh.setLevel(INFO if not self.debugLogging else DEBUG)

            for logger in self.loggers:
                logger.addHandler(rfh)

    @staticmethod
    def shutdown():
        logging.shutdown()

    def log(self, msg, level=INFO, *args, **kwargs):
        meThread = threading.currentThread().getName()
        message = meThread + u" :: " + msg

        # Change the SSL error to a warning with a link to information about how to fix it.
        check = re.sub(ur'error \[Errno 1\] _ssl.c:\d{3}: error:\d{8}:SSL routines:SSL23_GET_SERVER_HELLO:tlsv1 alert internal error', 'See: http://git.io/vJrkM', message)
        if check is not message:
            message = check
            level = WARNING

        if level == ERROR:
            classes.ErrorViewer.add(classes.UIError(message))
        elif level == WARNING:
            classes.WarningViewer.add(classes.UIError(message))

            # if sickbeard.GIT_AUTOISSUES:
            #    self.submit_errors()

        if level == ERROR:
            self.logger.exception(message, *args, **kwargs)
        else:
            self.logger.log(level, message, *args, **kwargs)

    def log_error_and_exit(self, error_msg, *args, **kwargs):
        self.log(error_msg, ERROR, *args, **kwargs)

        if not self.consoleLogging:
            sys.exit(error_msg.encode(sickbeard.SYS_ENCODING, 'xmlcharrefreplace'))
        else:
            sys.exit(1)

    def submit_errors(self): # Too many local variables, too many branches, pylint: disable=R0912,R0914

        submitter_result = u''
        issue_id = None

        if not (sickbeard.GIT_USERNAME and sickbeard.GIT_PASSWORD and sickbeard.DEBUG and len(classes.ErrorViewer.errors) > 0):
            submitter_result = u'Please set your GitHub username and password in the config and enable debug. Unable to submit issue ticket to GitHub!'
            return submitter_result, issue_id

        try:
            from sickbeard.versionChecker import CheckVersion
            checkversion = CheckVersion()
            checkversion.check_for_new_version()
            commits_behind = checkversion.updater.get_num_commits_behind()
        except Exception:
            submitter_result = u'Could not check if your SickRage is updated, unable to submit issue ticket to GitHub!'
            return submitter_result, issue_id

        if commits_behind is None or commits_behind > 0:
            submitter_result = u'Please update SickRage, unable to submit issue ticket to GitHub with an outdated version!'
            return  submitter_result, issue_id

        if self.submitter_running:
            submitter_result = u'Issue submitter is running, please wait for it to complete'
            return submitter_result, issue_id

        self.submitter_running = True

        gh_org = sickbeard.GIT_ORG or 'SiCKRAGETV'
        gh_repo = 'sickrage-issues'

        gh = Github(login_or_token=sickbeard.GIT_USERNAME, password=sickbeard.GIT_PASSWORD, user_agent="SiCKRAGE")

        try:
            # read log file
            log_data = None

            if os.path.isfile(self.logFile):
                with io.open(self.logFile, 'r', encoding='utf-8') as f:
                    log_data = f.readlines()

            for i in range(1, int(sickbeard.LOG_NR)):
                if os.path.isfile(self.logFile + ".%i" % i) and (len(log_data) <= 500):
                    with io.open(self.logFile + ".%i" % i, 'r', encoding='utf-8') as f:
                        log_data += f.readlines()

            log_data = [line for line in reversed(log_data)]

            # parse and submit errors to issue tracker
            for curError in sorted(classes.ErrorViewer.errors, key=lambda error: error.time, reverse=True)[:500]:

                try:
                    title_Error = ss(curError.title)
                    if not len(title_Error) or title_Error == 'None':
                        title_Error = re.match(r"^[A-Z0-9\-\[\] :]+::\s*(.*)$", ss(curError.message)).group(1)

                    if len(title_Error) > 1000:
                        title_Error = title_Error[0:1000]
                except Exception as e:
                    self.log("Unable to get error title : " + ex(e), ERROR)

                gist = None
                regex = ur"^(%s)\s+([A-Z]+)\s+([0-9A-Z\-]+)\s*(.*)$" % curError.time
                for i, x in enumerate(log_data):
                    match = re.match(regex, x)
                    if match:
                        level = match.group(2)
                        if reverseNames[level] == ERROR:
                            paste_data = u"".join(log_data[i:i+50])
                            if paste_data:
                                gist = gh.get_user().create_gist(True, {"sickrage.log": InputFileContent(paste_data)})
                            break
                    else:
                        gist = 'No ERROR found'

                message = u"### INFO\n"
                message += u"Python Version: **" + sys.version[:120].replace('\n', '') + "**\n"
                message += u"Operating System: **" + platform.platform() + "**\n"
                try:
                    message += u"Locale: " + locale.getdefaultlocale()[1] + "\n"
                except Exception:
                    message += u"Locale: unknown" + "\n"
                message += u"Branch: **" + sickbeard.BRANCH + "**\n"
                message += u"Commit: SiCKRAGETV/SickRage@" + sickbeard.CUR_COMMIT_HASH + "\n"
                if gist and gist != 'No ERROR found':
                    message += u"Link to Log: " + gist.html_url + "\n"
                else:
                    message += u"No Log available with ERRORS: " + "\n"
                message += u"### ERROR\n"
                message += u"```\n"
                message += curError.message + "\n"
                message += u"```\n"
                message += u"---\n"
                message += u"_STAFF NOTIFIED_: @SiCKRAGETV/owners @SiCKRAGETV/moderators"

                title_Error = u"[APP SUBMITTED]: " + title_Error
                reports = gh.get_organization(gh_org).get_repo(gh_repo).get_issues(state="all")

                def is_ascii_error(title):
                    # [APP SUBMITTED]: 'ascii' codec can't encode characters in position 00-00: ordinal not in range(128)
                    # [APP SUBMITTED]: 'charmap' codec can't decode byte 0x00 in position 00: character maps to <undefined>
                    return re.search(ur".* codec can't .*code .* in position .*:", title) is not None

                def is_malformed_error(title):
                    # [APP SUBMITTED]: not well-formed (invalid token): line 0, column 0
                    return re.search(ur".* not well-formed \(invalid token\): line .* column .*", title) is not None

                ascii_error = is_ascii_error(title_Error)
                malformed_error = is_malformed_error(title_Error)

                issue_found = False
                for report in reports:
                    if title_Error.rsplit(' :: ')[-1] in report.title or \
                        (malformed_error and is_malformed_error(report.title)) or \
                            (ascii_error and is_ascii_error(report.title)):

                        issue_id = report.number
                        if not report.raw_data['locked']:
                            if report.create_comment(message):
                                submitter_result = u'Commented on existing issue #%s successfully!' % issue_id
                            else:
                                submitter_result = u'Failed to comment on found issue #%s!' % issue_id
                        else:
                            submitter_result = u'Issue #%s is locked, check github to find info about the error.' % issue_id

                        issue_found = True
                        break

                if not issue_found:
                    issue = gh.get_organization(gh_org).get_repo(gh_repo).create_issue(title_Error, message)
                    if issue:
                        issue_id = issue.number
                        submitter_result = u'Your issue ticket #%s was submitted successfully!' % issue_id
                    else:
                        submitter_result = u'Failed to create a new issue!'

                if issue_id and curError in classes.ErrorViewer.errors:
                    # clear error from error list
                    classes.ErrorViewer.errors.remove(curError)

        except Exception as e:
            self.log(traceback.format_exc(), ERROR)
            submitter_result = u'Exception generated in issue submitter, please check the log'
            issue_id = None
        finally:
            self.submitter_running = False

        return submitter_result, issue_id

# pylint: disable=R0903
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
