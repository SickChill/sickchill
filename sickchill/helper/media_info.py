# coding=utf-8
# This file is part of SickChill.
#
# Author: Dustyn Gibson (miigotu) <miigotu@gmail.com>
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import binascii
import io

import six
from enzyme import MKV
from pkg_resources import DistributionNotFound, get_distribution

import sickchill

try:
    get_distribution('pymediainfo')
    from pymediainfo import MediaInfo as mediainfo
except (ImportError, DistributionNotFound):
    mediainfo = None


def _avi_screen_size(filename):
    """
    Parses avi file header for width and height
    :param filename: full path and filename to a video file
    :type: six.text_type
    :returns tuple: (width, height)
    """
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

            return width, height
    except Exception:
        pass

    return None, None


def _mkv_screen_size(filename):
    """
    Parses mkv file for width and height
    :param filename: full path and filename to a video file
    :type: six.text_type
    :returns tuple: (width, height)
    """
    try:
        if filename.endswith('.mkv'):
            with io.open(filename, 'rb') as f:
                mkv = MKV(f)

            return mkv.video_tracks[0].width, mkv.video_tracks[0].height
    except Exception:
        pass

    return None, None


def _mediainfo_screen_size(filename):
    """
    Attempts to read the width and height of a video file, using mediainfo
    :param filename: full path and filename to a video file
    :type: six.text_type
    :returns tuple: (width, height)
    """
    try:
        if mediainfo:
            _media_info = mediainfo.parse(filename)
            for track in _media_info.tracks:
                if track.track_type == 'Video':
                    return track.width, track.height
    except (OSError, TypeError):
        pass

    return None, None


# Only try to parse processable files once. Resets on restart ofc
bad_files = set()


def video_screen_size(filename):
    """
    Attempts to read the width and height of a video file,
    first using mediainfo and then enzyme, and then a custom avi reader

    :param filename: full path and filename to a video file
    :type: six.text_type
    :returns tuple: (width, height)
    """

    if filename in bad_files or not sickchill.helpers.is_media_file(filename):
        return None, None

    # Need to implement mediainfo another way, pymediainfo 2.0 causes segfaults
    # for method in [_mediainfo_screen_size, _mkv_screen_size, _avi_screen_size]:
    for method in [_mkv_screen_size, _avi_screen_size]:

        screen_size = method(filename)
        if screen_size != (None, None):
            return screen_size

    bad_files.add(filename)
    return None, None
