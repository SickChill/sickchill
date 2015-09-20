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

import sickbeard

from chardet import detect
from os import name


def ek(function, *args, **kwargs):
    """
    Encoding Kludge: Call function with arguments and unicode-encode output

    :param function:  Function to call
    :param args:  Arguments for function
    :param kwargs:  Arguments for function
    :return: Unicode-converted function output (string, list or tuple, depends on input)
    """

    if name == 'nt':
        result = function(*args, **kwargs)
    else:
        result = function(*[ss(x) if isinstance(x, (str, unicode)) else x for x in args], **kwargs)

    if isinstance(result, (list, tuple)):
        return _fix_list_encoding(result)

    if isinstance(result, str):
        return _to_unicode(result)

    return result


def ss(var):
    """
    Converts string to Unicode, fallback encoding is forced UTF-8

    :param var: String to convert
    :return: Converted string
    """

    var = _to_unicode(var)

    try:
        var = var.encode(sickbeard.SYS_ENCODING)
    except Exception:
        try:
            var = var.encode('utf-8')
        except Exception:
            try:
                var = var.encode(sickbeard.SYS_ENCODING, 'replace')
            except Exception:
                var = var.encode('utf-8', 'ignore')

    return var


def _fix_list_encoding(var):
    """
    Converts each item in a list to Unicode

    :param var: List or tuple to convert to Unicode
    :return: Unicode converted input
    """

    if isinstance(var, (list, tuple)):
        return filter(lambda x: x is not None, map(_to_unicode, var))

    return var


def _to_unicode(var):
    """
    Converts string to Unicode, using in order: UTF-8, Latin-1, System encoding or finally what chardet wants

    :param var: String to convert
    :return: Converted string as unicode, fallback is System encoding
    """

    if isinstance(var, str):
        try:
            var = unicode(var)
        except Exception:
            try:
                var = unicode(var, 'utf-8')
            except Exception:
                try:
                    var = unicode(var, 'latin-1')
                except Exception:
                    try:
                        var = unicode(var, sickbeard.SYS_ENCODING)
                    except Exception:
                        try:
                            # Chardet can be wrong, so try it last
                            var = unicode(var, detect(var).get('encoding'))
                        except Exception:
                            var = unicode(var, sickbeard.SYS_ENCODING, 'replace')

    return var
