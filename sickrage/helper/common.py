# This file is part of SickRage.
#
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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

import re
import sickbeard

dateFormat = '%Y-%m-%d'
dateTimeFormat = '%Y-%m-%d %H:%M:%S'
media_extensions = [
    '3gp', 'avi', 'divx', 'dvr-ms', 'f4v', 'flv', 'img', 'iso', 'm2ts', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg',
    'ogm', 'ogv', 'rmvb', 'tp', 'ts', 'vob', 'webm', 'wmv', 'wtv',
]
subtitle_extensions = ['ass', 'idx', 'srt', 'ssa', 'sub']
timeFormat = '%A %I:%M %p'


def is_sync_file(filename):
    """
    Check if the provided ``filename`` is a sync file, based on its name.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a sync file, ``False`` otherwise
    """

    if isinstance(filename, (str, unicode)):
        extension = filename.rpartition('.')[2].lower()

        return extension in sickbeard.SYNC_FILES.split(',') or filename.startswith('.syncthing')

    return False


def is_torrent_or_nzb_file(filename):
    """
    Check if the provided ``filename`` is a NZB file or a torrent file, based on its extension.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a NZB file or a torrent file, ``False`` otherwise
    """

    if not isinstance(filename, (str, unicode)):
        return False

    return filename.rpartition('.')[2].lower() in ['nzb', 'torrent']


def pretty_file_size(size):
    """
    Return a human readable representation of the provided ``size``.
    :param size: The size to convert
    :return: The converted size
    """
    if isinstance(size, (str, unicode)) and size.isdigit():
        size = float(size)
    elif not isinstance(size, (int, long, float)):
        return ''

    remaining_size = size

    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if remaining_size < 1024.:
            return '%3.2f %s' % (remaining_size, unit)

        remaining_size /= 1024.

    return size


def remove_extension(filename):
    """
    Remove the extension of the provided ``filename``.
    The extension is only removed if it is in `sickrage.helper.common.media_extensions` or ['nzb', 'torrent'].
    :param filename: The filename from which we want to remove the extension
    :return: The ``filename`` without its extension.
    """

    if isinstance(filename, (str, unicode)) and '.' in filename:
        # pylint: disable=W0612
        basename, separator, extension = filename.rpartition('.')  # @UnusedVariable

        if basename and extension.lower() in ['nzb', 'torrent'] + media_extensions:
            return basename

    return filename


def replace_extension(filename, new_extension):
    """
    Replace the extension of the provided ``filename`` with a new extension.
    :param filename: The filename for which we want to change the extension
    :param new_extension: The new extension to apply on the ``filename``
    :return: The ``filename`` with the new extension
    """

    if isinstance(filename, (str, unicode)) and '.' in filename:
        # pylint: disable=W0612
        basename, separator, extension = filename.rpartition('.')  # @UnusedVariable

        if basename:
            return '%s.%s' % (basename, new_extension)

    return filename


def sanitize_filename(filename):
    """
    Remove specific characters from the provided ``filename``.
    :param filename: The filename to clean
    :return: The ``filename``cleaned
    """

    if isinstance(filename, (str, unicode)):
        filename = re.sub(r'[\\/\*]', '-', filename)
        filename = re.sub(r'[:"<>|?]', '', filename)
        filename = re.sub(ur'\u2122', '', filename)  # Trade Mark Sign
        filename = filename.strip(' .')

        return filename

    return ''
