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

import sickbeard
import six
import chardet

from sickbeard import logger

# This module tries to deal with the apparently random behavior of python when dealing with unicode <-> utf-8
# encodings. It tries to just use unicode, but if that fails then it tries forcing it to utf-8. Any functions
# which return something should always return unicode.

def _toUnicode(x):
    try:
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
                    raise
    except:
        logger.log('Unable to decode value "%s..." : %s ' % (repr(x)[:20], traceback.format_exc()), logger.WARNING)
        ascii_text = str(x).encode('string_escape')
        return _toUnicode(ascii_text)

def ss(x):
    u_x = _toUnicode(x)

    try:
        return u_x.encode(sickbeard.SYS_ENCODING)
    except Exception as e:
        logger.log('Failed ss encoding char, force UTF8: %s' % e, logger.WARNING)
        try:
            return u_x.encode(sickbeard.SYS_ENCODING, 'replace')
        except:
            return u_x.encode('utf-8', 'replace')

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
