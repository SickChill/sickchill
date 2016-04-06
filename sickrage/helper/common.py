# coding=utf-8
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import io
import re
import binascii
from enzyme import MKV
from fnmatch import fnmatch

import sickbeard

dateFormat = '%Y-%m-%d'
dateTimeFormat = '%Y-%m-%d %H:%M:%S'
# Mapping HTTP status codes to official W3C names
http_status_code = {
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: 'Switch Proxy',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: 'Im a teapot',
    419: 'Authentication Timeout',
    420: 'Enhance Your Calm',
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    440: 'Login Timeout',
    444: 'No Response',
    449: 'Retry With',
    450: 'Blocked by Windows Parental Controls',
    451: [
        'Redirect',
        'Unavailable For Legal Reasons',
    ],
    494: 'Request Header Too Large',
    495: 'Cert Error',
    496: 'No Cert',
    497: 'HTTP to HTTPS',
    498: 'Token expired/invalid',
    499: [
        'Client Closed Request',
        'Token required',
    ],
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',
    507: 'Insufficient Storage',
    508: 'Loop Detected',
    509: 'Bandwidth Limit Exceeded',
    510: 'Not Extended',
    511: 'Network Authentication Required',
    520: 'CloudFlare - Web server is returning an unknown error',
    521: 'CloudFlare - Web server is down',
    522: 'CloudFlare - Connection timed out',
    523: 'CloudFlare - Origin is unreachable',
    524: 'CloudFlare - A timeout occurred',
    525: 'CloudFlare - SSL handshake failed',
    526: 'CloudFlare - Invalid SSL certificate',
    598: 'Network read timeout error',
    599: 'Network connect timeout error',
}
media_extensions = [
    '3gp', 'avi', 'divx', 'dvr-ms', 'f4v', 'flv', 'img', 'iso', 'm2ts', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg',
    'ogm', 'ogv', 'rmvb', 'tp', 'ts', 'vob', 'webm', 'wmv', 'wtv',
]
subtitle_extensions = ['ass', 'idx', 'srt', 'ssa', 'sub']
timeFormat = '%A %I:%M %p'


def http_code_description(http_code):
    """
    Get the description of the provided HTTP status code.
    :param http_code: The HTTP status code
    :return: The description of the provided ``http_code``
    """

    description = http_status_code.get(try_int(http_code))

    if isinstance(description, list):
        return '({0})'.format(', '.join(description))

    return description


def is_sync_file(filename):
    """
    Check if the provided ``filename`` is a sync file, based on its name.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a sync file, ``False`` otherwise
    """

    if isinstance(filename, (str, unicode)):
        extension = filename.rpartition('.')[2].lower()

        return extension in sickbeard.SYNC_FILES.split(',') or \
            filename.startswith('.syncthing') or \
            any(fnmatch(filename, match) for match in sickbeard.SYNC_FILES.split(','))

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


def pretty_file_size(size, use_decimal=False, **kwargs):
    """
    Return a human readable representation of the provided ``size``.

    :param size: The size to convert
    :param use_decimal: use decimal instead of binary prefixes (e.g. kilo = 1000 instead of 1024)

    :keyword units: A list of unit names in ascending order. Default units: ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    :return: The converted size
    """
    try:
        size = max(float(size), 0.)
    except (ValueError, TypeError):
        size = 0.

    remaining_size = size
    units = kwargs.pop('units', ['B', 'KB', 'MB', 'GB', 'TB', 'PB'])
    block = 1024. if not use_decimal else 1000.
    for unit in units:
        if remaining_size < block:
            return '{0:3.2f} {1}'.format(remaining_size, unit)
        remaining_size /= block
    return size


def convert_size(size, default=None, use_decimal=False, **kwargs):
    """
    Convert a file size into the number of bytes

    :param size: to be converted
    :param default: value to return if conversion fails
    :param use_decimal: use decimal instead of binary prefixes (e.g. kilo = 1000 instead of 1024)

    :keyword sep: Separator between size and units, default is space
    :keyword units: A list of (uppercase) unit names in ascending order. Default units: ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    :keyword default_units: Default unit if none is given, default is lowest unit in the scale, e.g. bytes

    :returns: the number of bytes, the default value, or 0
    """
    result = None

    try:
        sep = kwargs.pop('sep', ' ')
        scale = kwargs.pop('units', ['B', 'KB', 'MB', 'GB', 'TB', 'PB'])
        default_units = kwargs.pop('default_units', scale[0])

        if sep:
            size_tuple = size.strip().split(sep)
            scalar, units = size_tuple[0], size_tuple[1:]
            units = units[0].upper() if units else default_units
        else:
            regex_scalar = re.search(r'([\d. ]+)', size, re.I)
            scalar = regex_scalar.group() if regex_scalar else -1
            units = size.strip(scalar) if scalar != -1 else 'B'

        scalar = float(scalar)
        scalar *= (1024 if not use_decimal else 1000) ** scale.index(units)

        result = scalar

    # TODO: Make sure fallback methods obey default units
    except AttributeError:
        result = size if size is not None else default

    except ValueError:
        result = default

    finally:
        try:
            if result != default:
                result = long(result)
                result = max(result, 0)
        except (TypeError, ValueError):
            pass

    return result


def remove_extension(filename):
    """
    Remove the extension of the provided ``filename``.
    The extension is only removed if it is in `sickrage.helper.common.media_extensions` or ['nzb', 'torrent'].
    :param filename: The filename from which we want to remove the extension
    :return: The ``filename`` without its extension.
    """

    if isinstance(filename, (str, unicode)) and '.' in filename:
        basename, _, extension = filename.rpartition('.')

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
        basename, _, _ = filename.rpartition('.')

        if basename:
            return '{0}.{1}'.format(basename, new_extension)

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
        filename = re.sub(r'™', '', filename)  # Trade Mark Sign unicode: \u2122
        filename = filename.strip(' .')

        return filename

    return ''


def try_int(candidate, default_value=0):
    """
    Try to convert ``candidate`` to int, or return the ``default_value``.
    :param candidate: The value to convert to int
    :param default_value: The value to return if the conversion fails
    :return: ``candidate`` as int, or ``default_value`` if the conversion fails
    """

    try:
        return int(candidate)
    except (ValueError, TypeError):
        return default_value


def episode_num(season=None, episode=None, **kwargs):
    """
    Convert season and episode into string

    :param season: Season number
    :param episode: Episode Number
    :keyword numbering: Absolute for absolute numbering
    :returns: a string in s01e01 format or absolute numbering
    """

    numbering = kwargs.pop('numbering', 'standard')

    if numbering == 'standard':
        if season is not None and episode:
            return 'S{0:0>2}E{1:02}'.format(season, episode)
    elif numbering == 'absolute':
        if not (season and episode) and (season or episode):
            return '{0:0>3}'.format(season or episode)


def avi_screen_size(filename):
    """
    Parses avi file header for width and height
    :param filname: the filename to parse
    :returns: a tuple in (width, height) format or a tuple of (None, None)
    """
    try:
        if not filename.endswith('.avi'):
            raise

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
        return None, None


def mkv_screen_size(filename):
    """
    Parses mkv file for width and height
    :param filname: the filename to parse
    :returns: a tuple in (width, height) format or a tuple of (None, None)
    """
    try:
        if not filename.endswith('.mkv'):
            raise
        with io.open(filename, 'rb') as f:
            mkv = MKV(f)

        return mkv.video_tracks[0].width, mkv.video_tracks[0].height
    except Exception:
        return None, None
