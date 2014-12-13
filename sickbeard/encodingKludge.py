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

import os
import traceback
import re
import sickbeard
import six
import chardet
import unicodedata

from string import ascii_letters, digits
from sickbeard import logger

def toSafeString(original):
    valid_chars = "-_.() %s%s" % (ascii_letters, digits)
    cleaned_filename = unicodedata.normalize('NFKD', _toUnicode(original)).encode('ASCII', 'ignore')
    valid_string = ''.join(c for c in cleaned_filename if c in valid_chars)
    return ' '.join(valid_string.split())


def simplifyString(original):
    string = stripAccents(original.lower())
    string = toSafeString(' '.join(re.split('\W+', string)))
    split = re.split('\W+|_', string.lower())
    return _toUnicode(' '.join(split))

def _toUnicode(x):
    if isinstance(x, unicode):
        return x
    else:
        try:
            return six.text_type(x)
        except:
            try:
                if chardet.detect(x).get('encoding') == 'utf-8':
                    return x.decode('utf-8')
                if isinstance(x, str):
                    try:
                        return x.decode(sickbeard.SYS_ENCODING)
                    except UnicodeDecodeError:
                        raise
                return x
            except:
                return x

def ss(x):
    u_x = _toUnicode(x)

    try:
        u_x_encoded = u_x.encode(sickbeard.SYS_ENCODING, 'xmlcharrefreplace')
    except:
        try:
            u_x_encoded = u_x.encode(sickbeard.SYS_ENCODING)
        except:
            try:
                u_x_encoded = u_x.encode(sickbeard.SYS_ENCODING, 'replace')
            except:
                try:
                    u_x_encoded = u_x.encode('utf-8', 'replace')
                except:
                    try:
                        u_x_encoded = str(x)
                    except:
                        u_x_encoded = x

    return u_x_encoded

def fixListEncodings(x):
    if not isinstance(x, (list, tuple)):
        return x
    else:
        return filter(lambda x: x != None, map(_toUnicode, x))


def ek(func, *args, **kwargs):
    if os.name == 'nt':
        result = func(*args, **kwargs)
    else:
        result = func(*[ss(x) if isinstance(x, (str, unicode)) else x for x in args], **kwargs)

    if isinstance(result, (list, tuple)):
        return fixListEncodings(result)
    elif isinstance(result, str):
        return _toUnicode(result)
    else:
        return result

def stripAccents(s):
    return ''.join((c for c in unicodedata.normalize('NFD', _toUnicode(s)) if unicodedata.category(c) != 'Mn'))