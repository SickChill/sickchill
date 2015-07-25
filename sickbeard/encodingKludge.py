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

def _toUnicode(x):
    if isinstance(x, str):
        try:
            x = unicode(x)
        except Exception:
            try:
                x = unicode(x, 'utf-8')
            except Exception:
                try:
                   x = unicode(x, 'latin-1')
                except Exception:
                    try:
                        x = unicode(x, sickbeard.SYS_ENCODING)
                    except Exception:
                        try:
                            # Chardet can be wrong, so try it last
                            x = unicode(x, chardet.detect(x).get('encoding'))
                        except Exception:
                            x = unicode(x, sickbeard.SYS_ENCODING, 'replace')
    return x

def ss(x):
    x = _toUnicode(x)

    try:
        x = x.encode(sickbeard.SYS_ENCODING)
    except Exception:
        try:
            x = x.encode('utf-8')
        except Exception:
            try:
                x = x.encode(sickbeard.SYS_ENCODING, 'replace')
            except Exception:
                x = x.encode('utf-8', 'ignore')
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
