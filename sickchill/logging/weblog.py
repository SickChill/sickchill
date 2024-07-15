import datetime
import logging
import sys
from logging import ERROR, WARNING

from sickchill.helper.common import dateTimeFormat
from sickchill.oldbeard.notifiers import notify_logged_error


class __WebErrorViewer(object):
    """
    Keeps a static list of UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    __errors = []
    __warnings = []

    def __init__(self):
        self.__errors = []
        self.__warnings = []

    def __len__(self):
        return self.len()

    def add_error(self, error):
        self.__errors = [e for e in self.__errors if e.message != error.message]
        self.__errors.append(error)

    def add_warning(self, warning):
        self.__warnings = [w for w in self.__warnings if w.message != warning.message]
        self.__warnings.append(warning)

    def add(self, record):
        if record.levelno in (ERROR, WARNING):
            ui_error = UIError(record.msg, record.levelno)
            if record.levelno == ERROR:
                self.add_error(ui_error)
            if record.levelno == WARNING:
                self.add_warning(ui_error)

            if record.levelno == ERROR:
                notify_logged_error(ui_error)

    def get_errors(self):
        return self.__errors

    def get_warnings(self):
        return self.__warnings

    def have_errors(self):
        return len(self.__errors)

    def have_warnings(self):
        return len(self.__warnings)

    def clear_errors(self):
        self.__errors = []

    def clear_warnings(self):
        self.__warnings = []

    def clear(self, level: str) -> str:
        level = logging.getLevelName(level.upper())
        if level == logging.ERROR:
            message = "Error logs cleared"
            self.clear_errors()
        elif level == logging.WARNING:
            message = "Warning logs cleared"
            self.clear_warnings()
        else:
            message = "Warning and Error logs cleared"
            self.clear_warnings()
            self.clear_errors()

        return message

    def num_errors(self):
        return len(self.__errors)

    def num_warnings(self):
        return len(self.__warnings)

    def has_errors(self):
        return len(self.__errors) > 0

    def has_warnings(self):
        return len(self.__warnings) > 0

    def len(self):
        return self.num_errors() + self.num_warnings()

    def get(self):
        return self.__errors


WebErrorViewer = __WebErrorViewer()


class UIError(object):
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message, level):
        self.title = sys.exc_info()[-2] or message
        self.message = message
        self.time = datetime.datetime.now().strftime(dateTimeFormat)
        self.level = level
