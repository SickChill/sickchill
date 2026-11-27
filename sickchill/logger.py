import json
import logging
import logging.handlers
import os
import re
import sys
from logging import NullHandler
from urllib.parse import parse_qsl, quote, quote_plus

from sickchill import settings
from sickchill.helper.common import dateTimeFormat
from sickchill.logging.weblog import WebErrorViewer

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

CENSOR_PLACEHOLDER = "*" * 8
# Placeholders / type names that show up in logs (empty preferred quality is "None",
# qBittorrent args use Python None, post-process release_name can be None).
_CENSOR_SKIP = frozenset(
    {
        "none",
        "true",
        "false",
        "yes",
        "no",
        "on",
        "off",
        "null",
        "nil",
        "0",
        "1",
        "-1",
        "tv",
        "anime",
        "sickchill",
        "http",
        "https",
        "nzbget",
    }
)
_MIN_CENSOR_LEN = 3
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "passkey",
        "pass",
        "pwd",
        "username",
        "user",
        "api_key",
        "apikey",
        "jackett_apikey",
        "hash",
        "digest",
        "pin",
        "token",
        "secret",
        "cookies",
        "cookie",
        "authorization",
        "authorizationtoken",
        "webhook",
        "access_token",
        "refresh_token",
        "api_secret",
        "auth_token",
    }
)
_SECRET_NAME_TOKENS = frozenset(
    {
        "password",
        "passwd",
        "passkey",
        "username",
        "apikey",
        "token",
        "secret",
        "webhook",
        "hash",
        "digest",
        "pin",
        "cookies",
        "cookie",
        "authorization",
    }
)


def usable_censor_value(value) -> str | None:
    """Return a string worth masking, or None for placeholders / empty / too-short values."""
    if value is None:
        return None
    if isinstance(value, bytes):
        try:
            value = value.decode()
        except UnicodeDecodeError:
            return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    text = str(value).strip()
    if not text or len(text) < _MIN_CENSOR_LEN:
        return None
    if text.lower() in _CENSOR_SKIP:
        return None
    return text


def register_censored(key, value) -> None:
    """Store a secret for log masking, or drop the key when the value is not usable."""
    text = usable_censor_value(value)
    if text is None:
        censored_items.pop(key, None)
        return
    censored_items[key] = text


def field_should_censor(name: str, field_type: str = "", secret: bool = False) -> bool:
    if secret or (field_type or "").lower() == "password":
        return True
    lowered = str(name or "").lower().replace("-", "_")
    if lowered in _SENSITIVE_KEYS:
        return True
    return any(token in lowered.split("_") for token in _SECRET_NAME_TOKENS)


def is_sensitive_key(name: str) -> bool:
    lowered = str(name or "").lower().replace("-", "_")
    if lowered in _SENSITIVE_KEYS:
        return True
    return any(token in lowered.split("_") for token in _SECRET_NAME_TOKENS)


def _redact_structure(value):
    if isinstance(value, dict):
        return {key: (CENSOR_PLACEHOLDER if is_sensitive_key(key) else _redact_structure(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_structure(item) for item in value]
    return value


def redact_post_body(body) -> str:
    """Mask credential fields in a logged POST body (form or JSON)."""
    if body is None:
        return ""
    if isinstance(body, bytes):
        try:
            text = body.decode()
        except UnicodeDecodeError:
            return "<binary>"
    else:
        text = str(body)
    stripped = text.strip()
    if not stripped:
        return text
    if stripped[0] in "{[":
        try:
            return json.dumps(_redact_structure(json.loads(stripped)))
        except (TypeError, ValueError):
            pass
    if "=" in stripped:
        pairs = parse_qsl(stripped, keep_blank_values=True)
        if pairs:
            parts = []
            for key, value in pairs:
                masked = CENSOR_PLACEHOLDER if is_sensitive_key(key) else quote_plus(str(value))
                parts.append(f"{quote_plus(str(key))}={masked}")
            return "&".join(parts)
    return text


def _censor_values() -> list[str]:
    values = []
    seen: set[str] = set()
    for item in censored_items.values():
        text = usable_censor_value(item)
        if not text or text in seen:
            continue
        seen.add(text)
        values.append(text)
        for encoded in (quote(text, safe=""), quote_plus(text)):
            if encoded and encoded not in seen:
                seen.add(encoded)
                values.append(encoded)
    values.sort(key=len, reverse=True)
    return values


def _replace_secret(msg: str, item: str) -> str:
    if re.fullmatch(r"\w+", item):
        try:
            return re.sub(rf"\b{re.escape(item)}\b", CENSOR_PLACEHOLDER, msg)
        except re.error:
            pass
    return msg.replace(item, CENSOR_PLACEHOLDER)


def rotated_log_namer(default_name: str) -> str:
    """
    RotatingFileHandler default: sickchill.log.1
    Desired: sickchill.1.log (always end with .log)
    """
    # default_name is "{baseFilename}.{n}" e.g. /path/sickchill.log.1
    base, dot, number = default_name.rpartition(".")
    if not dot or not number.isdigit() or not base.endswith(".log"):
        return default_name
    stem = base[: -len(".log")]
    return f"{stem}.{number}.log"


def rotated_log_path(log_file: str, index: int) -> str:
    """Path for rotated backup index (1..N): sickchill.1.log"""
    if log_file.endswith(".log"):
        return f"{log_file[: -len('.log')]}.{index}.log"
    return f"{log_file}.{index}.log"


def migrate_legacy_rotated_logs(log_file: str, backup_count: int) -> None:
    """
    One-time fold of legacy RotatingFileHandler names into the new scheme:

        sickchill.log.N  →  sickchill.N.log

    After this, the next rotate of sickchill.log → sickchill.1.log shifts
    existing sickchill.N.log → sickchill.(N+1).log via the normal handler loop.
    Rename highest index first to avoid clobbering.
    """
    if not log_file or backup_count < 1:
        return

    for i in range(int(backup_count), 0, -1):
        legacy = f"{log_file}.{i}"
        target = rotated_log_path(log_file, i)
        if not os.path.isfile(legacy):
            continue
        if os.path.abspath(legacy) == os.path.abspath(target):
            continue
        if os.path.exists(target):
            # New-style file already present; leave legacy for manual cleanup
            continue
        try:
            os.rename(legacy, target)
        except OSError:
            pass


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

        try:
            msg = record.getMessage()
        except Exception:
            msg = record.msg

        if isinstance(msg, bytes):
            try:
                msg = msg.decode()
            except UnicodeDecodeError:
                msg = repr(msg)
        elif not isinstance(msg, str):
            msg = repr(msg)

        for item in _censor_values():
            msg = _replace_secret(msg, item)

        # Needed because Newznab apikey isn't stored as key=value in a section.
        msg = re.sub(r"([&?]r|[&?]apikey|[&?]jackett_apikey|[&?]api_key)(?:=|%3D)[^&]*([&\w]?)", r"\1=**********\2", msg, flags=re.IGNORECASE)

        record.msg = msg
        record.args = ()

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
            # Fold sickchill.log.N → sickchill.N.log before the handler runs, so the
            # next rotate shifts them to .2.log, .3.log, … under the new naming.
            migrate_legacy_rotated_logs(self.log_file, settings.LOG_NR)
            rfh = logging.handlers.RotatingFileHandler(self.log_file, maxBytes=int(settings.LOG_SIZE * 1048576), backupCount=settings.LOG_NR)
            rfh.namer = rotated_log_namer
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
    "SEARCHQUEUE-PROPER-SEARCH": _("Search Queue (Proper Search)"),
    "SEARCHQUEUE-SUBTITLE": _("Search Queue (Subtitles)"),
    "SEARCHQUEUE-CONNECTIVITY-CHECK": _("Search Queue (Connectivity)"),
    "FINDPROPERS": _("Find Propers"),
    "POSTPROCESSOR": _("Postprocessor"),
    "FINDSUBTITLES": _("Find Subtitles"),
    "TRAKTCHECKER": _("Trakt Checker"),
    # Matches the scheduler thread and every NOTIFICATIONS-<notifier> task.
    "NOTIFICATIONS": _("Notifications"),
    "EVENT": _("Event"),
    # Matches the server thread and every WEBSERVER-<page> worker.
    "WEBSERVER": _("Web Server"),
    "WEBSERVER-HOME": _("Web Server (Home)"),
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

        # Match RotatingFileHandler backupCount (1..LOG_NR) using sickchill.N.log names.
        # Fall back to legacy sickchill.log.N until those rotate away.
        for i in range(1, int(settings.LOG_NR) + 1):
            name = rotated_log_path(Wrapper.instance.log_file, i)
            if not os.path.isfile(name):
                legacy = f"{Wrapper.instance.log_file}.{i}"
                if not os.path.isfile(legacy):
                    break
                name = legacy
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
            elif (log_search and log_search.lower() in x.lower()) or (
                not log_search and LOGGING_LEVELS[level] >= int(min_level) and (log_filter == "<NONE>" or log_name.startswith(log_filter))
            ):
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
