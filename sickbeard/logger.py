# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

"""
Custom Logger for SickRage
"""

from __future__ import print_function, unicode_literals

import io
import locale
import logging
import logging.handlers
import os
import platform
import re
import sys
import threading
import traceback
from logging import NullHandler

import six
from github import InputFileContent, RateLimitExceededException, TwoFactorException

# noinspection PyUnresolvedReferences
from six.moves.urllib.parse import quote

import sickbeard
from sickbeard import classes
from sickrage.helper.common import dateTimeFormat
from sickrage.helper.encoding import ek, ss
from sickrage.helper.exceptions import ex

# pylint: disable=line-too-long

# log levels
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
DB = 5

LOGGING_LEVELS = {
    'ERROR': ERROR,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'DB': DB,
}

censored_items = {}  # pylint: disable=invalid-name


class CensoredFormatter(logging.Formatter, object):
    """
    Censor information such as API keys, user names, and passwords from the Log
    """
    def __init__(self, fmt=None, datefmt=None, encoding='utf-8'):
        super(CensoredFormatter, self).__init__(fmt, datefmt)
        self.encoding = encoding

    def format(self, record):
        """
        Strips censored items from string

        :param record: to censor
        """
        msg = super(CensoredFormatter, self).format(record)

        if not isinstance(msg, six.text_type):
            msg = msg.decode(self.encoding, 'replace')  # Convert to unicode

        # set of censored items
        censored = {item for _, item in six.iteritems(censored_items) if item}
        # set of censored items and urlencoded counterparts
        censored = censored | {quote(item) for item in censored}
        # convert set items to unicode and typecast to list
        censored = list({
            item.decode(self.encoding, 'replace')
            if not isinstance(item, six.text_type) else item
            for item in censored
        })
        # sort the list in order of descending length so that entire item is censored
        # e.g. password and password_1 both get censored instead of getting ********_1
        censored.sort(key=len, reverse=True)

        for item in censored:
            msg = msg.replace(item, len(item) * '*')

        # Needed because Newznab apikey isn't stored as key=value in a section.
        msg = re.sub(r'([&?]r|[&?]apikey|[&?]api_key)(?:=|%3D)[^&]*([&\w]?)', r'\1=**********\2', msg, re.I)
        return msg


class Logger(object):  # pylint: disable=too-many-instance-attributes
    """
    Logger to create log entries
    """
    def __init__(self):
        self.logger = logging.getLogger('sickrage')

        self.loggers = [
            logging.getLogger('sickrage'),
            logging.getLogger('tornado.general'),
            logging.getLogger('tornado.application'),
            # logging.getLogger('subliminal'),
            # logging.getLogger('tornado.access'),
            # logging.getLogger('tvdb_api'),
            # logging.getLogger("requests.packages.urllib3")
        ]

        self.console_logging = False
        self.file_logging = False
        self.debug_logging = False
        self.database_logging = False
        self.log_file = None

        self.submitter_running = False

    def init_logging(self, console_logging=False, file_logging=False, debug_logging=False, database_logging=False):
        """
        Initialize logging

        :param console_logging: True if logging to console
        :param file_logging: True if logging to file
        :param debug_logging: True if debug logging is enabled
        :param database_logging: True if logging database access
        """
        self.log_file = self.log_file or ek(os.path.join, sickbeard.LOG_DIR, 'sickrage.log')

        global log_file
        log_file = self.log_file

        self.debug_logging = debug_logging
        self.console_logging = console_logging
        self.file_logging = file_logging
        self.database_logging = database_logging

        logging.addLevelName(DB, 'DB')  # add a new logging level DB
        logging.getLogger().addHandler(NullHandler())  # nullify root logger

        # set custom root logger
        for logger in self.loggers:
            if logger is not self.logger:
                logger.root = self.logger
                logger.parent = self.logger

        log_level = DB if self.database_logging else DEBUG if self.debug_logging else INFO

        # set minimum logging level allowed for loggers
        for logger in self.loggers:
            logger.setLevel(log_level)

        logging.getLogger("tornado.general").setLevel('ERROR')

        # console log handler
        if self.console_logging:
            console = logging.StreamHandler()
            console.setFormatter(CensoredFormatter('%(asctime)s %(levelname)s::%(message)s', '%H:%M:%S'))
            console.setLevel(log_level)

            for logger in self.loggers:
                logger.addHandler(console)

        # rotating log file handler
        if self.file_logging:
            rfh = logging.handlers.RotatingFileHandler(
                self.log_file, maxBytes=int(sickbeard.LOG_SIZE * 1048576), backupCount=sickbeard.LOG_NR, encoding='utf-8'
            )
            rfh.setFormatter(CensoredFormatter('%(asctime)s %(levelname)-8s %(message)s', dateTimeFormat))
            rfh.setLevel(log_level)

            for logger in self.loggers:
                logger.addHandler(rfh)

    def set_level(self):
        self.debug_logging = sickbeard.DEBUG
        self.database_logging = sickbeard.DBDEBUG

        level = DB if self.database_logging else DEBUG if self.debug_logging else INFO
        for logger in self.loggers:
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)

    @staticmethod
    def shutdown():
        """
        Shut down the logger
        """
        logging.shutdown()

    def log(self, msg, level=INFO, *args, **kwargs):
        """
        Create log entry

        :param msg: to log
        :param level: of log, e.g. DEBUG, INFO, etc.
        :param args: to pass to logger
        :param kwargs: to pass to logger
        """
        cur_thread = threading.currentThread().getName()

        cur_hash = ''
        if level == ERROR and sickbeard.CUR_COMMIT_HASH and len(sickbeard.CUR_COMMIT_HASH) > 6:
            cur_hash = '[{0}] '.format(
                sickbeard.CUR_COMMIT_HASH[:7]
            )

        message = '{thread} :: {hash}{message}'.format(
            thread=cur_thread, hash=cur_hash, message=msg)

        # Change the SSL error to a warning with a link to information about how to fix it.
        # Check for 'error [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure (_ssl.c:590)'

        ssl_errors = [
            r'error \[Errno \d+\] _ssl.c:\d+: error:\d+\s*:SSL routines:SSL23_GET_SERVER_HELLO:tlsv1 alert internal error',
            r'error \[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE\] sslv3 alert handshake failure \(_ssl\.c:\d+\)',
        ]
        for ssl_error in ssl_errors:
            check = re.sub(ssl_error, 'See: http://git.io/vuU5V', message)
            if check != message:
                message = check
                level = WARNING

        if level == ERROR:
            classes.ErrorViewer.add(classes.UIError(message))
        elif level == WARNING:
            classes.WarningViewer.add(classes.UIError(message))

        try:
            if level == ERROR:
                self.logger.exception(message, *args, **kwargs)
            else:
                self.logger.log(level, message, *args, **kwargs)
        except Exception:
            if msg and msg.strip():  # Otherwise creates empty messages in log...
                print(msg.strip())

    def log_error_and_exit(self, error_msg, *args, **kwargs):
        self.log(error_msg, ERROR, *args, **kwargs)

        if not self.console_logging:
            sys.exit(error_msg.encode(sickbeard.SYS_ENCODING, 'xmlcharrefreplace'))
        else:
            sys.exit(1)

    def submit_errors(self):  # pylint: disable=too-many-branches,too-many-locals

        submitter_result = ''
        issue_id = None

        gh_credentials = (sickbeard.GIT_AUTH_TYPE == 0 and sickbeard.GIT_USERNAME and sickbeard.GIT_PASSWORD) \
            or (sickbeard.GIT_AUTH_TYPE == 1 and sickbeard.GIT_TOKEN)

        if not all((gh_credentials, sickbeard.DEBUG, sickbeard.gh, classes.ErrorViewer.errors)):
            submitter_result = 'Please set your GitHub token or username and password in the config and enable debug. Unable to submit issue ticket to GitHub!'
            return submitter_result, issue_id

        try:
            from sickbeard.versionChecker import CheckVersion
            checkversion = CheckVersion()
            checkversion.check_for_new_version()
            commits_behind = checkversion.updater.get_num_commits_behind()
        except Exception:  # pylint: disable=broad-except
            submitter_result = 'Could not check if your SickRage is updated, unable to submit issue ticket to GitHub!'
            return submitter_result, issue_id

        if commits_behind is None or commits_behind > 0:
            submitter_result = 'Please update SickRage, unable to submit issue ticket to GitHub with an outdated version!'
            return submitter_result, issue_id

        if self.submitter_running:
            submitter_result = 'Issue submitter is running, please wait for it to complete'
            return submitter_result, issue_id

        self.submitter_running = True

        try:
            # read log file
            __log_data = None

            if ek(os.path.isfile, self.log_file):
                with io.open(self.log_file, encoding='utf-8') as log_f:
                    __log_data = log_f.readlines()

            for i in range(1, int(sickbeard.LOG_NR)):
                f_name = '{0}.{1:d}'.format(self.log_file, i)
                if ek(os.path.isfile, f_name) and (len(__log_data) <= 500):
                    with io.open(f_name, encoding='utf-8') as log_f:
                        __log_data += log_f.readlines()

            __log_data = list(reversed(__log_data))

            # parse and submit errors to issue tracker
            for cur_error in sorted(classes.ErrorViewer.errors, key=lambda error: error.time, reverse=True)[:500]:
                try:
                    title_error = ss(str(cur_error.title))
                    if not title_error or title_error == 'None':
                        title_error = re.match(r'^[A-Z0-9\-\[\] :]+::\s*(.*)(?: \[[\w]{7}\])$', ss(cur_error.message)).group(1)

                    if len(title_error) > 1000:
                        title_error = title_error[0:1000]

                except Exception as err_msg:  # pylint: disable=broad-except
                    self.log('Unable to get error title : {0}'.format(ex(err_msg)), ERROR)
                    title_error = 'UNKNOWN'

                gist = None
                regex = r'^({0})\s+([A-Z]+)\s+([0-9A-Z\-]+)\s*(.*)(?: \[[\w]{{7}}\])$'.format(cur_error.time)
                for i, data in enumerate(__log_data):
                    match = re.match(regex, data)
                    if match:
                        level = match.group(2)
                        if LOGGING_LEVELS[level] == ERROR:
                            paste_data = ''.join(__log_data[i:i + 50])
                            if paste_data:
                                gist = sickbeard.gh.get_user().create_gist(False, {'sickrage.log': InputFileContent(paste_data)})
                            break
                    else:
                        gist = 'No ERROR found'

                try:
                    locale_name = locale.getdefaultlocale()[1]
                except Exception:  # pylint: disable=broad-except
                    locale_name = 'unknown'

                if gist and gist != 'No ERROR found':
                    log_link = 'Link to Log: {0}'.format(gist.html_url)
                else:
                    log_link = 'No Log available with ERRORS:'

                msg = [
                    '### INFO',
                    'Python Version: **{0}**'.format(sys.version[:120].replace('\n', '')),
                    'Operating System: **{0}**'.format(platform.platform()),
                    'Locale: {0}'.format(locale_name),
                    'Branch: **{0}**'.format(sickbeard.BRANCH),
                    'Commit: SickRage/SickRage@{0}'.format(sickbeard.CUR_COMMIT_HASH),
                    log_link,
                    '### ERROR',
                    '```',
                    cur_error.message,
                    '```',
                    '---',
                    '_STAFF NOTIFIED_: @SickRage/owners @SickRage/moderators',
                ]

                message = '\n'.join(msg)
                title_error = '[APP SUBMITTED]: {0}'.format(title_error)

                repo = sickbeard.gh.get_organization(sickbeard.GIT_ORG).get_repo(sickbeard.GIT_REPO)
                reports = repo.get_issues(state='all')

                def is_ascii_error(title):
                    # [APP SUBMITTED]: 'ascii' codec can't encode characters in position 00-00: ordinal not in range(128)
                    # [APP SUBMITTED]: 'charmap' codec can't decode byte 0x00 in position 00: character maps to <undefined>
                    return re.search(r'.* codec can\'t .*code .* in position .*:', title) is not None

                def is_malformed_error(title):
                    # [APP SUBMITTED]: not well-formed (invalid token): line 0, column 0
                    return re.search(r'.* not well-formed \(invalid token\): line .* column .*', title) is not None

                ascii_error = is_ascii_error(title_error)
                malformed_error = is_malformed_error(title_error)

                issue_found = False
                for report in reports:
                    if title_error.rsplit(' :: ')[-1] in report.title or \
                        (malformed_error and is_malformed_error(report.title)) or \
                            (ascii_error and is_ascii_error(report.title)):

                        issue_id = report.number
                        if not report.raw_data['locked']:
                            if report.create_comment(message):
                                submitter_result = 'Commented on existing issue #{0} successfully!'.format(issue_id)
                            else:
                                submitter_result = 'Failed to comment on found issue #{0}!'.format(issue_id)
                        else:
                            submitter_result = 'Issue #{0} is locked, check GitHub to find info about the error.'.format(issue_id)

                        issue_found = True
                        break

                if not issue_found:
                    issue = repo.create_issue(title_error, message)
                    if issue:
                        issue_id = issue.number
                        submitter_result = 'Your issue ticket #{0} was submitted successfully!'.format(issue_id)
                    else:
                        submitter_result = 'Failed to create a new issue!'

                if issue_id and cur_error in classes.ErrorViewer.errors:
                    # clear error from error list
                    classes.ErrorViewer.errors.remove(cur_error)
        except RateLimitExceededException:
            submitter_result = 'Your Github user has exceeded its API rate limit, please try again later'
            issue_id = None
        except TwoFactorException:
            submitter_result = ('Your Github account requires Two-Factor Authentication, '
                                'please change your auth method in the config')
            issue_id = None
        except Exception:  # pylint: disable=broad-except
            self.log(traceback.format_exc(), ERROR)
            submitter_result = 'Exception generated in issue submitter, please check the log'
            issue_id = None
        finally:
            self.submitter_running = False

        return submitter_result, issue_id


# pylint: disable=too-few-public-methods
class Wrapper(object):
    instance = Logger()

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):
        try:
            return getattr(self.wrapped, name)
        except AttributeError:
            return getattr(self.instance, name)


_globals = sys.modules[__name__] = Wrapper(sys.modules[__name__])  # pylint: disable=invalid-name


def init_logging(*args, **kwargs):
    return Wrapper.instance.init_logging(*args, **kwargs)


def log(*args, **kwargs):
    return Wrapper.instance.log(*args, **kwargs)


def log_error_and_exit(*args, **kwargs):
    return Wrapper.instance.log_error_and_exit(*args, **kwargs)


def set_level(*args, **kwargs):
    return Wrapper.instance.set_level(*args, **kwargs)


def shutdown():
    return Wrapper.instance.shutdown()


def submit_errors(*args, **kwargs):
    return Wrapper.instance.submit_errors(*args, **kwargs)

log_file = None

LOG_FILTERS = {
    '<NONE>': _('&lt;No Filter&gt;'),
    'DAILYSEARCHER': _('Daily Searcher'),
    'BACKLOG': _('Backlog'),
    'SHOWUPDATER': _('Show Updater'),
    'CHECKVERSION': _('Check Version'),
    'SHOWQUEUE': _('Show Queue'),
    'SEARCHQUEUE': _('Search Queue (All)'),
    'SEARCHQUEUE-DAILY-SEARCH': _('Search Queue (Daily Searcher)'),
    'SEARCHQUEUE-BACKLOG': _('Search Queue (Backlog)'),
    'SEARCHQUEUE-MANUAL': _('Search Queue (Manual)'),
    'SEARCHQUEUE-RETRY': _('Search Queue (Retry/Failed)'),
    'SEARCHQUEUE-RSS': _('Search Queue (RSS)'),
    'FINDPROPERS': _('Find Propers'),
    'POSTPROCESSOR': _('Postprocessor'),
    'FINDSUBTITLES': _('Find Subtitles'),
    'TRAKTCHECKER': _('Trakt Checker'),
    'EVENT': _('Event'),
    'ERROR': _('Error'),
    'TORNADO': _('Tornado'),
    'Thread': _('Thread'),
    'MAIN': _('Main'),
}


def log_data(min_level, log_filter, log_search, max_lines):
    regex = r"^(\d\d\d\d)\-(\d\d)\-(\d\d)\s*(\d\d)\:(\d\d):(\d\d)\s*([A-Z]+)\s*(.+?)\s*\:\:\s*(.*)$"
    if log_filter not in LOG_FILTERS:
        log_filter = '<NONE>'

    final_data = []

    log_files = []
    if ek(os.path.isfile, Wrapper.instance.log_file):
        log_files.append(Wrapper.instance.log_file)

        for i in range(1, int(sickbeard.LOG_NR)):
            name = Wrapper.instance.log_file + "." + str(i)
            if not ek(os.path.isfile, name):
                break
            log_files.append(name)
    else:
        return final_data

    data = []
    for _log_file in log_files:
        if len(data) < max_lines:
            with io.open(_log_file, 'r', encoding='utf-8') as f:
                data += [line.strip() + '\n' for line in reversed(f.readlines()) if line.strip()]
        else:
            break

    found_lines = 0
    for x in data:
        match = re.match(regex, x)

        if match:
            level = match.group(7)
            log_name = match.group(8)

            if not sickbeard.DEBUG and level == 'DEBUG':
                continue

            if not sickbeard.DBDEBUG and level == 'DB':
                continue

            if level not in LOGGING_LEVELS:
                final_data.append('AA ' + x)
                found_lines += 1
            elif log_search and log_search.lower() in x.lower():
                final_data.append(x)
                found_lines += 1
            elif not log_search and LOGGING_LEVELS[level] >= int(min_level) and (log_filter == '<NONE>' or log_name.startswith(log_filter)):
                final_data.append(x)
                found_lines += 1
        else:
            final_data.append('AA ' + x)
            found_lines += 1

        if found_lines >= max_lines:
            break

    return final_data
