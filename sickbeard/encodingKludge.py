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
import chardet
import sickbeard

def fixStupidEncodings(x, silent=False):
    if type(x) == str:
        try:
            return x.decode(sickbeard.SYS_ENCODING)
        except UnicodeDecodeError:
            logger.log(u"Unable to decode value: " + repr(x), logger.ERROR)
            return None
    elif type(x) == unicode:
        return x
    else:
        logger.log(
            u"Unknown value passed in, ignoring it: " + str(type(x)) + " (" + repr(x) + ":" + repr(type(x)) + ")",
            logger.DEBUG if silent else logger.ERROR)
        return None
        
def _toUnicode(x):
    try:
        if not isinstance(x, unicode):
            if chardet.detect(x).get('encoding') == 'utf-8':
                x = x.decode('utf-8')
            elif isinstance(x, str):
                x = x.decode(sickbeard.SYS_ENCODING)
    finally:
        return x

def ss(x):
    x = _toUnicode(x)

    try:
        try:
            try:
                x = x.encode(sickbeard.SYS_ENCODING)
            except:
                x = x.encode(sickbeard.SYS_ENCODING, 'ignore')
        except:
            x = x.encode('utf-8', 'ignore')
    finally:
        return x

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