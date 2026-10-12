import datetime
import functools
import locale

from sickchill import settings
from sickchill.oldbeard.network_timezones import sc_now, sc_timezone

date_presets = (
    "%Y-%m-%d",
    "%a, %Y-%m-%d",
    "%A, %Y-%m-%d",
    "%y-%m-%d",
    "%a, %y-%m-%d",
    "%A, %y-%m-%d",
    "%m/%d/%Y",
    "%a, %m/%d/%Y",
    "%A, %m/%d/%Y",
    "%m/%d/%y",
    "%a, %m/%d/%y",
    "%A, %m/%d/%y",
    "%m-%d-%Y",
    "%a, %m-%d-%Y",
    "%A, %m-%d-%Y",
    "%m-%d-%y",
    "%a, %m-%d-%y",
    "%A, %m-%d-%y",
    "%m.%d.%Y",
    "%a, %m.%d.%Y",
    "%A, %m.%d.%Y",
    "%m.%d.%y",
    "%a, %m.%d.%y",
    "%A, %m.%d.%y",
    "%d-%m-%Y",
    "%a, %d-%m-%Y",
    "%A, %d-%m-%Y",
    "%d-%m-%y",
    "%a, %d-%m-%y",
    "%A, %d-%m-%y",
    "%d/%m/%Y",
    "%a, %d/%m/%Y",
    "%A, %d/%m/%Y",
    "%d/%m/%y",
    "%a, %d/%m/%y",
    "%A, %d/%m/%y",
    "%d.%m.%Y",
    "%a, %d.%m.%Y",
    "%A, %d.%m.%Y",
    "%d.%m.%y",
    "%a, %d.%m.%y",
    "%A, %d.%m.%y",
    "%d. %b %Y",
    "%a, %d. %b %Y",
    "%A, %d. %b %Y",
    "%d. %b %y",
    "%a, %d. %b %y",
    "%A, %d. %b %y",
    "%d. %B %Y",
    "%a, %d. %B %Y",
    "%A, %d. %B %Y",
    "%d. %B %y",
    "%a, %d. %B %y",
    "%A, %d. %B %y",
    "%b %d, %Y",
    "%a, %b %d, %Y",
    "%A, %b %d, %Y",
    "%B %d, %Y",
    "%a, %B %d, %Y",
    "%A, %B %d, %Y",
)

time_presets = ("%I:%M:%S %p", "%H:%M:%S")


# helper class
class static_or_instance(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return functools.partial(self.func, instance)


# subclass datetime.datetime to add function to display custom date and time formats
class scdatetime(datetime.datetime):
    has_locale = True
    en_US_norm = locale.normalize("en_US.utf-8")

    @static_or_instance
    def convert_to_setting(self, dt=None):
        try:
            if settings.TIMEZONE_DISPLAY == "local":
                return dt.astimezone(sc_timezone) if self is None else self.astimezone(sc_timezone)
            else:
                return self if self else dt
        except Exception:
            return self if self else dt

    @static_or_instance
    def scftime(self, dt=None, show_seconds=False, t_preset=None):
        """
        Display time in SC format

        :param dt: datetime object
        :param show_seconds: Boolean, show seconds
        :param t_preset: Preset time format
        :return: time string
        """

        try:
            locale.setlocale(locale.LC_TIME, "")
        except Exception:
            pass

        try:
            if scdatetime.has_locale:
                locale.setlocale(locale.LC_TIME, "en_US")
        except Exception:
            try:
                if scdatetime.has_locale:
                    locale.setlocale(locale.LC_TIME, scdatetime.en_US_norm)
            except Exception:
                scdatetime.has_locale = False

        strt = ""
        try:
            if self is None:
                if dt is not None:
                    if t_preset is not None:
                        strt = dt.strftime(t_preset)
                    elif show_seconds:
                        strt = dt.strftime(settings.TIME_PRESET_W_SECONDS)
                    else:
                        strt = dt.strftime(settings.TIME_PRESET)
            else:
                if t_preset is not None:
                    strt = self.strftime(t_preset)
                elif show_seconds:
                    strt = self.strftime(settings.TIME_PRESET_W_SECONDS)
                else:
                    strt = self.strftime(settings.TIME_PRESET)
        finally:
            try:
                if scdatetime.has_locale:
                    locale.setlocale(locale.LC_TIME, "")
            except Exception:
                scdatetime.has_locale = False

        return strt

    # display Date in SickChill Format
    @static_or_instance
    def scfdate(self, dt=None, d_preset=None):
        """
        Display date in SC format

        :param dt: datetime object
        :param d_preset: Preset date format
        :return: date string
        """

        try:
            locale.setlocale(locale.LC_TIME, "")
        except Exception:
            pass

        strd = ""
        try:
            if self is None:
                if dt is not None:
                    if d_preset is not None:
                        strd = dt.strftime(d_preset)
                    else:
                        strd = dt.strftime(settings.DATE_PRESET)
            else:
                if d_preset is not None:
                    strd = self.strftime(d_preset)
                else:
                    strd = self.strftime(settings.DATE_PRESET)
        except (ValueError, OSError):
            strd = "UNK"

        finally:
            try:
                locale.setlocale(locale.LC_TIME, "")
            except Exception:
                pass

        return strd

    # display Datetime in SickChill Format
    @static_or_instance
    def scfdatetime(self, dt=None, show_seconds=False, d_preset=None, t_preset=None):
        """
        Show datetime in SC format

        :param dt: datetime object
        :param show_seconds: Boolean, show seconds as well
        :param d_preset: Preset date format
        :param t_preset: Preset time format
        :return: datetime string
        """

        try:
            locale.setlocale(locale.LC_TIME, "")
        except Exception:
            pass

        strd = ""
        try:
            if self is None:
                if dt is not None:
                    if d_preset is not None:
                        strd = dt.strftime(d_preset)
                    else:
                        strd = dt.strftime(settings.DATE_PRESET)
                    try:
                        if scdatetime.has_locale:
                            locale.setlocale(locale.LC_TIME, "en_US")
                    except Exception:
                        try:
                            if scdatetime.has_locale:
                                locale.setlocale(locale.LC_TIME, scdatetime.en_US_norm)
                        except Exception:
                            scdatetime.has_locale = False
                    if t_preset is not None:
                        strd += ", " + dt.strftime(t_preset)
                    elif show_seconds:
                        strd += ", " + dt.strftime(settings.TIME_PRESET_W_SECONDS)
                    else:
                        strd += ", " + dt.strftime(settings.TIME_PRESET)
            else:
                if d_preset is not None:
                    strd = self.strftime(d_preset)
                else:
                    strd = self.strftime(settings.DATE_PRESET)
                try:
                    if scdatetime.has_locale:
                        locale.setlocale(locale.LC_TIME, "en_US")
                except Exception:
                    try:
                        if scdatetime.has_locale:
                            locale.setlocale(locale.LC_TIME, scdatetime.en_US_norm)
                    except Exception:
                        scdatetime.has_locale = False
                if t_preset is not None:
                    strd += ", " + self.strftime(t_preset)
                elif show_seconds:
                    strd += ", " + self.strftime(settings.TIME_PRESET_W_SECONDS)
                else:
                    strd += ", " + self.strftime(settings.TIME_PRESET)
        except (ValueError, OSError):
            strd = "UNK"
        finally:
            try:
                if scdatetime.has_locale:
                    locale.setlocale(locale.LC_TIME, "")
            except Exception:
                scdatetime.has_locale = False

        return strd


_TIMEAGO_STEPS = (60.0, 60.0, 24.0, 7.0, 365.0 / 7.0 / 12.0, 12.0)
_TIMEAGO_TEMPLATES = (
    ("just now", "a while"),
    ("%s seconds ago", "in %s seconds"),
    ("1 minute ago", "in 1 minute"),
    ("%s minutes ago", "in %s minutes"),
    ("1 hour ago", "in 1 hour"),
    ("%s hours ago", "in %s hours"),
    ("1 day ago", "in 1 day"),
    ("%s days ago", "in %s days"),
    ("1 week ago", "in 1 week"),
    ("%s weeks ago", "in %s weeks"),
    ("1 month ago", "in 1 month"),
    ("%s months ago", "in %s months"),
    ("1 year ago", "in 1 year"),
    ("%s years ago", "in %s years"),
)


def _format_timeago(delta: datetime.timedelta) -> str:
    """English relative time matching the previous timeago package strings."""
    seconds = int(delta.total_seconds())
    ago_in = 0
    if seconds < 0:
        ago_in = 1
        seconds *= -1
    value = float(seconds)
    index = 0
    while index < len(_TIMEAGO_STEPS) and value >= _TIMEAGO_STEPS[index]:
        value /= _TIMEAGO_STEPS[index]
        index += 1
    count = int(value)
    index *= 2
    if count > (9 if index == 0 else 1):
        index += 1
    template = _TIMEAGO_TEMPLATES[index][ago_in]
    return template % count if "%s" in template else template


def sctimeago(date) -> str:
    """Return a timeago string using SickChill timezone data."""
    if date is None:
        return ""

    now = sc_now()
    if isinstance(date, datetime.timedelta):
        date = now + date

    if date.tzinfo is None:
        date = date.replace(tzinfo=sc_timezone)

    return _format_timeago(now - date)
