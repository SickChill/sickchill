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

dateFormat = '%Y-%m-%d'
dateTimeFormat = '%Y-%m-%d %H:%M:%S'
media_extensions = [
    '3gp', 'avi', 'divx', 'dvr-ms', 'f4v', 'flv', 'img', 'iso', 'm2ts', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg',
    'ogm', 'ogv', 'rmvb', 'tp', 'ts', 'vob', 'webm', 'wmv', 'wtv',
]
subtitle_extensions = ['ass', 'idx', 'srt', 'ssa', 'sub']
timeFormat = '%A %I:%M %p'


def remove_extension(filename):
    """
    Remove the extension of the provided ``filename``.
    The extension is only removed if it is in `sickrage.helper.common.media_extensions` or ['nzb', 'torrent'].
    :param filename: The filename from which we want to remove the extension
    :return: The ``filename`` without its extension.
    """

    if filename and '.' in filename:
        # pylint: disable=W0612
        basename, separator, extension = filename.rpartition('.')  # @UnusedVariable

        if basename and extension.lower() in ['nzb', 'torrent'] + media_extensions:
            return basename

    return filename
