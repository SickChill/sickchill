import logging
import logging.handlers
import os
import re
import sys
from logging import NullHandler
from urllib.parse import quote

from sickchill import settings
from sickchill.helper.common import dateTimeFormat
from sickchill.logging.weblog import WebErrorViewer
from sickchill.oldbeard import notifiers

# log levels
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
DB = 5

LOGGING_LEVELS = {
    "ERROR": ERROR,
    "WARNING": WARNING,
    "INFO": INFO,
    "DEBUG": DEBUG,
    "DB": DB,
}

censored_items = {}


class DispatchFormatter(logging.Formatter, object):
    """
    Censor information such as API keys, usernames, and passwords from the Log
    """

    def __init__(self, fmt=None, datefmt=None, style="{"):
        super().__init__(fmt, datefmt, style=style)

    def format(self, record):
        """
        Strips censored items from string and formats the log line

        :param record: to format
        """

        msg = record.msg

        # set of censored items
        censored = {item for _, item in censored_items.items() if item}
        # set of censored items and urlencoded counterparts
        censored = list(censored | {quote(item) for item in censored})
        # sort the list in order of descending length so that entire item is censored
        # e.g. password and password_1 both get censored instead of getting ********_1
        censored.sort(key=len, reverse=True)

        if not isinstance(msg, (str, bytes)):
            msg = repr(msg)

        for item in censored:
            try:
                # passwords that include ++ for example will error. Cannot escape or it won't match at all.
                # Always use 8 *'s, so people cant guess censored item length for things like passwords.
                msg = re.sub(rf"\b({item})\b", "*" * 8, msg)
            except re.error:
                msg = msg.replace(item, "*" * 8)
            except TypeError:
                print(msg)

        # Needed because Newznab apikey isn't stored as key=value in a section.
        msg = re.sub(r"([&?]r|[&?]apikey|[&?]jackett_apikey|[&?]api_key)(?:=|%3D)[^&]*([&\w]?)", r"\1=**********\2", msg, re.I)

        # Set the new message into the record!
        record.msg = msg

        WebErrorViewer.add(record)

        return super().format(record)


class Logger(object):
    """
    Logger to create log entries
    """

    def __init__(self):
        self.logger = logging.getLogger("sickchill")

        self.loggers = [
            logging.getLogger("sickchill"),
            logging.getLogger("sickchill.movie"),
            logging.getLogger("tornado.general"),
            logging.getLogger("tornado.application"),
            logging.getLogger("subliminal"),
            logging.getLogger("tornado.access"),
            logging.getLogger("imdbpy.parser.http.piculet"),
            logging.getLogger("imdbpy.parser.http.domparser"),
            logging.getLogger("sqlalchemy.engine"),
            logging.getLogger("sqlalchemy.pool"),
            logging.getLogger("sqlalchemy.dialect"),
            logging.getLogger("imdbpy"),
            logging.getLogger("imdbpy.parser.s3"),
        ]

        self.console_logging = False
        self.file_logging = False
        self.debug_logging = False
        self.database_logging = False
        self.log_file = None

    def init_logging(self, console_logging=False, file_logging=False, debug_logging=False, database_logging=False):
        """
        Initialize logging

        :param console_logging: True if logging to console
        :param file_logging: True if logging to file
        :param debug_logging: True if debug logging is enabled
        :param database_logging: True if logging database access
        """
        self.log_file = self.log_file or os.path.join(settings.LOG_DIR, "sickchill.log")

        global log_file
        log_file = self.log_file

        self.debug_logging = debug_logging
        self.console_logging = console_logging
        self.file_logging = file_logging
        self.database_logging = database_logging

        logging.addLevelName(DB, "DB")  # add a new logging level DB
        logging.getLogger().addHandler(NullHandler())  # nullify root logger

        # set custom root logger
        for logger in self.loggers:
            if logger is not self.logger:
                logger.root = self.logger
                logger.parent = self.logger

        log_level = DB if self.database_logging else DEBUG if self.debug_logging else INFO

        # set minimum logging level allowed for loggers
        for logger in self.loggers:
            if logger.name in ("subliminal", "tornado.access", "tornado.general", "imdbpy.parser.http.piculet", "imdbpy.parser.http.domparser"):
                logger.setLevel("CRITICAL")
            elif (logger.name.startswith("sqlalchemy") or logger.name.startswith("imdb")) and not self.database_logging:
                logger.setLevel("WARNING")
            else:
                logger.setLevel(log_level)

        log_format = "{asctime} {levelname} :: {threadName} :: {message}"
        # console log handler
        if self.console_logging:
            console = logging.StreamHandler()
            console.setFormatter(DispatchFormatter(log_format, dateTimeFormat))
            console.setLevel(log_level)

            for logger in self.loggers:
                logger.addHandler(console)

        # rotating log file handler
        if self.file_logging:
            rfh = logging.handlers.RotatingFileHandler(self.log_file, maxBytes=int(settings.LOG_SIZE * 1048576), backupCount=settings.LOG_NR)
            rfh.setFormatter(DispatchFormatter(log_format, dateTimeFormat))
            rfh.setLevel(log_level)

            for logger in self.loggers:
                logger.addHandler(rfh)

    def restart(self, change_log_dir: bool = False):
        """
        Sets the logging level for root and all of our loggers
        """
        if self.debug_logging == settings.DEBUG and self.database_logging == settings.DBDEBUG and not change_log_dir:
            return

        self.debug_logging = settings.DEBUG
        self.database_logging = settings.DBDEBUG

        if not change_log_dir:
            self.logger.info(f"Changing DEBUG to {settings.DEBUG} and DATABASE DEBUG to {settings.DBDEBUG}")

        # Set these back to None, so they are reset on init
        global log_file
        self.log_file = None
        log_file = self.log_file

        self.close_and_remove_handlers()
        self.init_logging(self.console_logging, self.file_logging, self.debug_logging, self.database_logging)

    def close_and_remove_handlers(self):
        for logger in self.loggers:
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

    def shutdown(self):
        """
        Shut down the logger
        """
        self.close_and_remove_handlers()
        logging.shutdown()

    def log_error_and_exit(self, error_msg, *args, **kwargs):
        self.logger.log(ERROR, error_msg, *args, **kwargs)

        if not self.console_logging:
            sys.exit(error_msg)
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

LOG_FILTERS = {
    "<NONE>": _("&lt;No Filter&gt;"),
    "DAILYSEARCHER": _("Daily Searcher"),
    "BACKLOG": _("Backlog"),
    "SHOWUPDATER": _("Show Updater"),
    "CHECKVERSION": _("Check Version"),
    "SHOWQUEUE": _("Show Queue"),
    "SEARCHQUEUE": _("Search Queue (All)"),
    "SEARCHQUEUE-DAILY-SEARCH": _("Search Queue (Daily Searcher)"),
    "SEARCHQUEUE-BACKLOG": _("Search Queue (Backlog)"),
    "SEARCHQUEUE-MANUAL": _("Search Queue (Manual)"),
    "SEARCHQUEUE-RETRY": _("Search Queue (Retry/Failed)"),
    "SEARCHQUEUE-RSS": _("Search Queue (RSS)"),
    "FINDPROPERS": _("Find Propers"),
    "POSTPROCESSOR": _("Postprocessor"),
    "FINDSUBTITLES": _("Find Subtitles"),
    "TRAKTCHECKER": _("Trakt Checker"),
    "EVENT": _("Event"),
    "ERROR": _("Error"),
    "TORNADO": _("Tornado"),
    "Thread": _("Thread"),
    "MAIN": _("Main"),
}


def log_data(min_level, log_filter, log_search, max_lines):
    regex = r"^\d{4}\-\d{2}\-\d{2} \d{2}\:\d{2}:\d{2} ([A-Z]+) \:\: (.+?) \:\: (.*)$"
    if log_filter not in LOG_FILTERS:
        log_filter = "<NONE>"

    final_data = []

    log_files = []
    if os.path.isfile(Wrapper.instance.log_file):
        log_files.append(Wrapper.instance.log_file)

        for i in range(1, int(settings.LOG_NR)):
            name = f"{Wrapper.instance.log_file}.{i}"
            if not os.path.isfile(name):
                break
            log_files.append(name)
    else:
        return final_data

    data = []
    for _log_file in log_files:
        if len(data) < max_lines:
            with open(_log_file) as f:
                data += [line.strip() + "\n" for line in reversed(f.readlines()) if line.strip()]
        else:
            break

    found_lines = 0
    for x in data:
        match = re.match(regex, x)

        if match:
            level = match.group(1)
            log_name = match.group(2)

            if not settings.DEBUG and level == "DEBUG":
                continue

            if not settings.DBDEBUG and level == "DB":
                continue

            if level not in LOGGING_LEVELS:
                final_data.append("AA " + x)
                found_lines += 1
            elif log_search and log_search.lower() in x.lower():
                final_data.append(x)
                found_lines += 1
            elif not log_search and LOGGING_LEVELS[level] >= int(min_level) and (log_filter == "<NONE>" or log_name.startswith(log_filter)):
                final_data.append(x)
                found_lines += 1
        else:
            final_data.append("AA " + x)
            found_lines += 1

        if found_lines >= max_lines:
            break

    return final_data


log_error_and_exit = Wrapper.instance.log_error_and_exit
log_file = Wrapper.instance.log_file

log = Wrapper.instance.logger.log
debug = Wrapper.instance.logger.debug
info = Wrapper.instance.logger.info
warning = Wrapper.instance.logger.warning
error = Wrapper.instance.logger.error
exception = error
critical = Wrapper.instance.logger.critical


def database(msg, *args, **kwargs):
    """
    Handler to add database sql logging
    @param msg: message to be logged
    @param args: arguments to logger
    @param kwargs:  kwargs to logger
    """
    if settings.DBDEBUG:
        debug(msg, args, kwargs)


init_logging = Wrapper.instance.init_logging
restart = Wrapper.instance.restart
shutdown = Wrapper.instance.shutdown
