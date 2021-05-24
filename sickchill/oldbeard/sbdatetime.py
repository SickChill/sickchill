import datetime
import functools
import locale

from sickchill import settings

from .network_timezones import sb_timezone

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
class sbdatetime(datetime.datetime):
    has_locale = True
    en_US_norm = locale.normalize("en_US.utf-8")

    @static_or_instance
    def convert_to_setting(self, dt=None):
        try:
            if settings.TIMEZONE_DISPLAY == "local":
                return dt.astimezone(sb_timezone) if self is None else self.astimezone(sb_timezone)
            else:
                return dt if self is None else self
        except Exception:
            return dt if self is None else self

    # display Time in SickChill Format
    @static_or_instance
    def sbftime(self, dt=None, show_seconds=False, t_preset=None):
        """
        Display time in SR format
        TODO: Rename this to srftime

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
            if sbdatetime.has_locale:
                locale.setlocale(locale.LC_TIME, "en_US")
        except Exception:
            try:
                if sbdatetime.has_locale:
                    locale.setlocale(locale.LC_TIME, sbdatetime.en_US_norm)
            except Exception:
                sbdatetime.has_locale = False

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
                if sbdatetime.has_locale:
                    locale.setlocale(locale.LC_TIME, "")
            except Exception:
                sbdatetime.has_locale = False

        return strt

    # display Date in SickChill Format
    @static_or_instance
    def sbfdate(self, dt=None, d_preset=None):
        """
        Display date in SR format
        TODO: Rename this to srfdate

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
    def sbfdatetime(self, dt=None, show_seconds=False, d_preset=None, t_preset=None):
        """
        Show datetime in SR format
        TODO: Rename this to srfdatetime

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
                        if sbdatetime.has_locale:
                            locale.setlocale(locale.LC_TIME, "en_US")
                    except Exception:
                        try:
                            if sbdatetime.has_locale:
                                locale.setlocale(locale.LC_TIME, sbdatetime.en_US_norm)
                        except Exception:
                            sbdatetime.has_locale = False
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
                    if sbdatetime.has_locale:
                        locale.setlocale(locale.LC_TIME, "en_US")
                except Exception:
                    try:
                        if sbdatetime.has_locale:
                            locale.setlocale(locale.LC_TIME, sbdatetime.en_US_norm)
                    except Exception:
                        sbdatetime.has_locale = False
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
                if sbdatetime.has_locale:
                    locale.setlocale(locale.LC_TIME, "")
            except Exception:
                sbdatetime.has_locale = False

        return strd
