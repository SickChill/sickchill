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

import datetime
import locale
import functools

import sickbeard

date_presets = ('%Y-%m-%d',
                '%a, %Y-%m-%d',
                '%A, %Y-%m-%d',
                '%y-%m-%d',
                '%a, %y-%m-%d',
                '%A, %y-%m-%d',
                '%m/%d/%Y',
                '%a, %m/%d/%Y',
                '%A, %m/%d/%Y',
                '%m/%d/%y',
                '%a, %m/%d/%y',
                '%A, %m/%d/%y',
                '%m-%d-%Y',
                '%a, %m-%d-%Y',
                '%A, %m-%d-%Y',
                '%m-%d-%y',
                '%a, %m-%d-%y',
                '%A, %m-%d-%y',
                '%m.%d.%Y',
                '%a, %m.%d.%Y',
                '%A, %m.%d.%Y',
                '%m.%d.%y',
                '%a, %m.%d.%y',
                '%A, %m.%d.%y',
                '%d-%m-%Y',
                '%a, %d-%m-%Y',
                '%A, %d-%m-%Y',
                '%d-%m-%y',
                '%a, %d-%m-%y',
                '%A, %d-%m-%y',
                '%d.%m.%Y',
                '%a, %d.%m.%Y',
                '%A, %d.%m.%Y',
                '%d.%m.%y',
                '%a, %d.%m.%y',
                '%A, %d.%m.%y',
                '%d. %b %Y',
                '%a, %d. %b %Y',
                '%A, %d. %b %Y',
                '%d. %b %y',
                '%a, %d. %b %y',
                '%A, %d. %b %y',
                '%d. %B %Y',
                '%a, %d. %B %Y',
                '%A, %d. %B %Y',
                '%d. %B %y',
                '%a, %d. %B %y',
                '%A, %d. %B %y',
                '%b %d, %Y',
                '%a, %b %d, %Y',
                '%A, %b %d, %Y',
                '%B %d, %Y',
                '%a, %B %d, %Y',
                '%A, %B %d, %Y'
)

time_presets = ('%I:%M:%S %p',
                '%H:%M:%S'
)

# helper class
class static_or_instance(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return functools.partial(self.func, instance)


# subclass datetime.datetime to add function to display custom date and time formats
class sbdatetime(datetime.datetime):
    has_locale = True
    ORIG_LC_TIME = locale.LC_TIME

    # display Time in SickRage Format
    @static_or_instance
    def sbftime(self, dt=None, show_seconds=False, t_preset=None):

        try:locale.setlocale(locale.LC_TIME, self.ORIG_LC_TIME)
        except:pass

        try:
            if sbdatetime.has_locale:
                locale.setlocale(locale.LC_TIME, 'us_US')
        except:
            sbdatetime.has_locale = False

        strt = ''
        try:
            if self is None:
                if dt is not None:
                    if t_preset is not None:
                        strt = dt.strftime(t_preset)
                    elif show_seconds:
                        strt = dt.strftime(sickbeard.TIME_PRESET_W_SECONDS)
                    else:
                        strt = dt.strftime(sickbeard.TIME_PRESET)
            else:
                if t_preset is not None:
                    strt = self.strftime(t_preset)
                elif show_seconds:
                    strt = self.strftime(sickbeard.TIME_PRESET_W_SECONDS)
                else:
                    strt = self.strftime(sickbeard.TIME_PRESET)
        finally:
            try:
                if sbdatetime.has_locale:
                    locale.setlocale(locale.LC_TIME, self.ORIG_LC_TIME)
            except:
                sbdatetime.has_locale = False

            return strt

    # display Date in SickRage Format
    @static_or_instance
    def sbfdate(self, dt=None, d_preset=None):

        try:
            locale.setlocale(locale.LC_TIME, self.ORIG_LC_TIME)
        except:
            pass

        strd = ''
        try:
            if self is None:
                if dt is not None:
                    if d_preset is not None:
                        strd = dt.strftime(d_preset)
                    else:
                        strd = dt.strftime(sickbeard.DATE_PRESET)
            else:
                if d_preset is not None:
                    strd = self.strftime(d_preset)
                else:
                    strd = self.strftime(sickbeard.DATE_PRESET)
        finally:

            try:
                locale.setlocale(locale.LC_TIME, self.ORIG_LC_TIME)
            except:
                pass

            return strd

    # display Datetime in SickRage Format
    @static_or_instance
    def sbfdatetime(self, dt=None, show_seconds=False, d_preset=None, t_preset=None):

        try:
            locale.setlocale(locale.LC_TIME, self.ORIG_LC_TIME)
        except:
            pass

        strd = ''
        try:
            if self is None:
                if dt is not None:
                    if d_preset is not None:
                        strd = dt.strftime(d_preset)
                    else:
                        strd = dt.strftime(sickbeard.DATE_PRESET)
                    try:
                        if sbdatetime.has_locale:
                            locale.setlocale(locale.LC_TIME, 'us_US')
                    except:
                        sbdatetime.has_locale = False
                    if t_preset is not None:
                        strd += u', ' + dt.strftime(t_preset)
                    elif show_seconds:
                        strd += u', ' + dt.strftime(sickbeard.TIME_PRESET_W_SECONDS)
                    else:
                        strd += u', ' + dt.strftime(sickbeard.TIME_PRESET)
            else:
                if d_preset is not None:
                    strd = self.strftime(d_preset)
                else:
                    strd = self.strftime(sickbeard.DATE_PRESET)
                try:
                    if sbdatetime.has_locale:
                        locale.setlocale(locale.LC_TIME, 'us_US')
                except:
                    sbdatetime.has_locale = False
                if t_preset is not None:
                    strd += u', ' + self.strftime(t_preset)
                elif show_seconds:
                    strd += u', ' + self.strftime(sickbeard.TIME_PRESET_W_SECONDS)
                else:
                    strd += u', ' + self.strftime(sickbeard.TIME_PRESET)
        finally:
            try:
                if sbdatetime.has_locale:
                    locale.setlocale(locale.LC_TIME, self.ORIG_LC_TIME)
            except:
                sbdatetime.has_locale = False

            return strd
