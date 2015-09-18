# This file is part of SickRage.
#
# URL: https://www.sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

from sickrage.helper.encoding import ss

dateFormat = '%Y-%m-%d'
dateTimeFormat = '%Y-%m-%d %H:%M:%S'
timeFormat = '%A %I:%M %p'


def ex(e):
    """
    :param e: The exception to convert into a unicode string
    :return: A unicode string from the exception text if it exists
    """

    message = u''

    if not e or not e.args:
        return message

    for arg in e.args:
        if arg is not None:
            if isinstance(arg, (str, unicode)):
                fixed_arg = ss(arg)
            else:
                try:
                    fixed_arg = u'error %s' % ss(str(arg))
                except:
                    fixed_arg = None

            if fixed_arg:
                if not message:
                    message = fixed_arg
                else:
                    message = '%s : %s' % (message, fixed_arg)

    return message
