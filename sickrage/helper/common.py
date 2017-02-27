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

"""
Common helper functions
"""

from __future__ import print_function, unicode_literals

import os
import re
import glob
from fnmatch import fnmatch

from github import Github, BadCredentialsException, TwoFactorException
import six

import sickbeard

dateFormat = '%Y-%m-%d'
dateTimeFormat = '%Y-%m-%d %H:%M:%S'
# Mapping HTTP status codes to official W3C names
HTTP_STATUS_CODES = {
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
MEDIA_EXTENSIONS = [
    '3gp', 'avi', 'divx', 'dvr-ms', 'f4v', 'flv', 'm2ts', 'm4v',
    'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'ogm', 'ogv', 'rmvb', 'tp', 'ts', 'vob',
    'webm', 'wmv', 'wtv',
]

SUBTITLE_EXTENSIONS = ['ass', 'idx', 'srt', 'ssa', 'sub']
timeFormat = '%A %I:%M %p'


def http_code_description(http_code):
    """
    Get the description of the provided HTTP status code.
    :param http_code: The HTTP status code
    :return: The description of the provided ``http_code``
    """

    description = HTTP_STATUS_CODES.get(try_int(http_code))

    if isinstance(description, list):
        return '({0})'.format(', '.join(description))

    return description


def is_sync_file(filename):
    """
    Check if the provided ``filename`` is a sync file, based on its name.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a sync file, ``False`` otherwise
    """

    if isinstance(filename, six.string_types):
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

    if not isinstance(filename, six.string_types):
        return False

    return filename.rpartition('.')[2].lower() in ['nzb', 'torrent']


def pretty_file_size(size, use_decimal=False, **kwargs):
    """
    Return a human readable representation of the provided ``size``.

    :param size: The size to convert
    :param use_decimal: use decimal instead of binary prefixes (e.g. kilo = 1000 instead of 1024)

    :keyword units: A list of unit names in ascending order.
        Default units: ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

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
    :keyword units: A list of (uppercase) unit names in ascending order.
        Default units: ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    :keyword default_units: Default unit if none is given,
        default is lowest unit on the scale, e.g. bytes

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
                result = max(int(result), 0)
        except (TypeError, ValueError):
            pass

    return result


def remove_extension(filename):
    """
    Remove the extension of the provided ``filename``.
    The extension is only removed if it is in MEDIA_EXTENSIONS or ['nzb', 'torrent'].
    :param filename: The filename from which we want to remove the extension
    :return: The ``filename`` without its extension.
    """

    if isinstance(filename, six.string_types) and '.' in filename:
        basename, _, extension = filename.rpartition('.')

        if basename and extension.lower() in ['nzb', 'torrent'] + MEDIA_EXTENSIONS:
            return basename

    return filename


def replace_extension(filename, new_extension):
    """
    Replace the extension of the provided ``filename`` with a new extension.
    :param filename: The filename for which we want to change the extension
    :param new_extension: The new extension to apply on the ``filename``
    :return: The ``filename`` with the new extension
    """

    if isinstance(filename, six.string_types) and '.' in filename:
        basename = filename.rpartition('.')[0]
        if basename:
            return '{0}.{1}'.format(basename, new_extension)

    return filename


def sanitize_filename(filename):
    """
    Remove specific characters from the provided ``filename``.
    :param filename: The filename to clean
    :return: The ``filename``cleaned
    """

    if isinstance(filename, six.string_types):
        filename = re.sub(r'[\\/\*]', '-', filename)
        filename = re.sub(r'[:"<>|?]', '', filename)
        filename = re.sub(r'™|-u2122', '', filename)  # Trade Mark Sign unicode: \u2122
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


# Backport glob.escape from python 3.4
# https://hg.python.org/cpython/file/3.4/Lib/glob.py#l87
MAGIC_CHECK = re.compile('([*?[])')
MAGIC_CHECK_BYTES = re.compile(b'([*?[])')


# https://hg.python.org/cpython/file/3.4/Lib/glob.py#l100
def glob_escape(pathname):
    """Escape all special characters.
    """
    # Escaping is done by wrapping any of "*?[" between square brackets.
    # Metacharacters do not work in the drive part and shouldn't be escaped.
    drive, pathname = os.path.splitdrive(pathname)
    if isinstance(pathname, bytes):
        pathname = MAGIC_CHECK_BYTES.sub(br'[\1]', pathname)
    else:
        pathname = MAGIC_CHECK.sub(r'[\1]', pathname)
    return drive + pathname

CUSTOM_GLOB = glob
CUSTOM_GLOB.escape = glob_escape


def setup_github():
    """
    Instantiate the global github connection, for checking for updates and submitting issues
    """

    try:
        if sickbeard.GIT_AUTH_TYPE == 0 and sickbeard.GIT_USERNAME and sickbeard.GIT_PASSWORD:
            # Basic Username/Password Auth
            sickbeard.gh = Github(
                login_or_token=sickbeard.GIT_USERNAME,
                password=sickbeard.GIT_PASSWORD, user_agent="SickRage")
            # This will trigger BadCredentialsException if user/pass are wrong
            sickbeard.gh.get_organization(sickbeard.GIT_ORG)

        elif sickbeard.GIT_AUTH_TYPE == 1 and sickbeard.GIT_TOKEN:
            # Token Auth - allows users with Two-Factor Authorization (2FA) enabled on Github to connect their account.
            sickbeard.gh = Github(
                login_or_token=sickbeard.GIT_TOKEN, user_agent="SickRage")
            # This will trigger:
            # * BadCredentialsException if token is invalid
            # * TwoFactorException if user has enabled Github-2FA
            #   but didn't set a personal token in the configuration.
            sickbeard.gh.get_organization(sickbeard.GIT_ORG)

            # Update GIT_USERNAME if it's not the same, so we don't run into problems later on.
            gh_user = sickbeard.gh.get_user().login
            sickbeard.GIT_USERNAME = gh_user if sickbeard.GIT_USERNAME != gh_user else sickbeard.GIT_USERNAME

    except (Exception, BadCredentialsException, TwoFactorException) as error:
        sickbeard.gh = None
        sickbeard.logger.log('Unable to setup GitHub properly with your github login. Please'
                             ' check your credentials. Error: {0}'.format(error), sickbeard.logger.WARNING)

    if not sickbeard.gh:
        try:
            sickbeard.gh = Github(user_agent="SickRage")
        except Exception as error:
            sickbeard.gh = None
            sickbeard.logger.log('Unable to setup GitHub properly. GitHub will not be '
                                 'available. Error: {0}'.format(error), sickbeard.logger.WARNING)
