# coding=utf-8
# This file is part of SickRage.
#
# Author: Dustyn Gibson (miigotu) <miigotu@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals, print_function

import io
import binascii
from enzyme import MKV

from pkg_resources import get_distribution
import sickbeard

try:
    get_distribution('pymediainfo')
    from pymediainfo import MediaInfo as mediainfo  # pylint: disable=import-error
except Exception:
    mediainfo = None


def _avi_screen_size(filename):
    """
    Parses avi file header for width and height
    :param filename: full path and filename to a video file
    :type: unicode
    :returns tuple: (width, height)
    """
    width = height = None
    try:
        if not filename.endswith('.avi'):
            with io.open(filename, 'rb') as f:
                header = f.read(72)

            x = binascii.hexlify(header[68:72])
            height = int(x[6:8] + x[4:6] + x[2:4] + x[0:2], 16)
            assert 100 < height < 4320

            x = binascii.hexlify(header[64:68])
            width = int(x[6:8] + x[4:6] + x[2:4] + x[0:2], 16)
            assert 100 < width < 7680

            del header
    except Exception:
        pass

    return width, height


def _mkv_screen_size(filename):
    """
    Parses mkv file for width and height
    :param filename: full path and filename to a video file
    :type: unicode
    :returns tuple: (width, height)
    """
    width = height = None
    try:
        if filename.endswith('.mkv'):
            with io.open(filename, 'rb') as f:
                mkv = MKV(f)

            if mkv:
                width, height = mkv.video_tracks[0].width, mkv.video_tracks[0].height
                del mkv
    except Exception:
        pass

    return width, height


def _mediainfo_screen_size(filename):
    """
    Attempts to read the width and height of a video file, using mediainfo
    :param filename: full path and filename to a video file
    :type: unicode
    :returns tuple: (width, height)
    """
    width = height = None
    try:
        if mediainfo:
            _media_info = mediainfo.parse(filename)
            if _media_info:
                for track in _media_info.tracks:
                    if track.track_type == 'Video':
                        width, height = track.width, track.height
                        break

                del _media_info
    except Exception:
        pass

    return width, height


def video_screen_size(filename):
    """
    Attempts to read the width and height of a video file,
    first using mediainfo and then enzyme, and then a custom avi reader

    :param filename: full path and filename to a video file
    :type: unicode
    :returns tuple: (width, height)
    """

    if not sickbeard.helpers.isMediaFile(filename):
        return None, None

    for method in (_mediainfo_screen_size, _mkv_screen_size, _avi_screen_size):
        screen_size = method(filename)
        if all(screen_size):
            return screen_size

    return None, None
