import platform
import re
import uuid
from fnmatch import fnmatch
from os import PathLike
from pathlib import Path
from typing import Union

import appdirs
import rarfile
import validators

from sickchill import settings
from sickchill.init_helpers import get_current_version

INSTANCE_ID = str(uuid.uuid1())
USER_AGENT = "SickChill/{version} ({os} {architecture} {os_version}; {instance})".format(
    version=get_current_version(), os=platform.system(), architecture=platform.machine(), os_version=platform.release(), instance=INSTANCE_ID
)

dateFormat = "%Y-%m-%d"
dateTimeFormat = "%Y-%m-%d %H:%M:%S"

# Mapping HTTP status codes to official W3C names
HTTP_STATUS_CODES = {
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    306: "Switch Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    418: "Im a teapot",
    419: "Authentication Timeout",
    420: "Enhance Your Calm",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    440: "Login Timeout",
    444: "No Response",
    449: "Retry With",
    450: "Blocked by Windows Parental Controls",
    451: [
        "Redirect",
        "Unavailable For Legal Reasons",
    ],
    494: "Request Header Too Large",
    495: "Cert Error",
    496: "No Cert",
    497: "HTTP to HTTPS",
    498: "Token expired/invalid",
    499: [
        "Client Closed Request",
        "Token required",
    ],
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    509: "Bandwidth Limit Exceeded",
    510: "Not Extended",
    511: "Network Authentication Required",
    520: "CloudFlare - Web server is returning an unknown error",
    521: "CloudFlare - Web server is down",
    522: "CloudFlare - Connection timed out",
    523: "CloudFlare - Origin is unreachable",
    524: "CloudFlare - A timeout occurred",
    525: "CloudFlare - SSL handshake failed",
    526: "CloudFlare - Invalid SSL certificate",
    598: "Network read timeout error",
    599: "Network connect timeout error",
}
MEDIA_EXTENSIONS = [
    "3gp",
    "avi",
    "divx",
    "dvr-ms",
    "f4v",
    "flv",
    "m2ts",
    "m4v",
    "mkv",
    "mov",
    "mp4",
    "mpeg",
    "mpg",
    "ogm",
    "ogv",
    "rmvb",
    "tp",
    "ts",
    "vob",
    "webm",
    "wmv",
    "wtv",
]

SUBTITLE_EXTENSIONS = ["ass", "idx", "srt", "ssa", "sub"]
timeFormat = "%A %I:%M %p"


def http_code_description(http_code):
    """
    Get the description of the provided HTTP status code.
    :param http_code: The HTTP status code
    :return: The description of the provided ``http_code``
    """

    description = HTTP_STATUS_CODES.get(try_int(http_code))

    if isinstance(description, list):
        return f"({', '.join(description)})"

    return description


def get_extension(path: Union[Path, PathLike, str] = None, lower: bool = False) -> str:
    path = Path(path)
    result = path.suffix.lstrip(".")
    if lower:
        result = result.lower()

    return result


def is_sync_file(filename: Union[Path, PathLike, str] = None) -> bool:
    """
    Check if the provided ``filename`` is a sync file, based on its name.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a sync file, ``False`` otherwise
    """
    sync_extensions = settings.SYNC_FILES.split(",")
    return (
        filename.startswith(".syncthing")
        or get_extension(filename, lower=True) in sync_extensions
        or any(fnmatch(filename, match) for match in sync_extensions)
    )


def is_torrent_or_nzb_file(filename: Union[Path, PathLike, str] = None) -> bool:
    """
    Check if the provided ``filename`` is a NZB file or a torrent file, based on its extension.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a NZB file or a torrent file, ``False`` otherwise
    """
    return get_extension(filename, lower=True) in ("nzb", "torrent")


def is_media_file(filename):
    """
    Check if named file may contain media

    Parameters:
        filename: Filename to check
    Returns:
        True if this is a known media file, False if not
    """

    # ignore samples
    is_rar = is_rar_file(filename)

    path = Path(filename)
    if re.search(r"(^|[\W_])(?<!shomin.)(sample\d*)[\W_]", path.name, re.I):
        return False

    # ignore RARBG release intro
    if re.search(r"^RARBG\.(\w+\.)?(mp4|avi|txt)$", path.name, re.I):
        return False

    # ignore Kodi tvshow trailers
    if path.name == "tvshow-trailer.mp4":
        return False

    # ignore MACOS's retarded "resource fork" files
    if path.name.startswith("._"):
        return False

    if re.search("extras?$", path.name, re.I):
        return False

    return (get_extension(path, lower=True) in MEDIA_EXTENSIONS) or (is_rar and settings.UNPACK == settings.UNPACK_PROCESS_INTACT)


def is_rar_file(filename: Union[Path, PathLike, str]) -> bool:
    """
    Check if file is a RAR file, or part of a RAR set

    Parameters:
        filename: Filename to check
    Returns:
         True if this is RAR/Part file, False if not
    """
    result = False
    path = Path(filename)
    archive_regex = r"(?P<file>^(?P<base>(?:(?!\.part\d+\.rar$).)*)\.(?:(?:part0*1\.)?rar)$)"
    try:
        if path.is_file():
            result = rarfile.is_rarfile(path)
        else:
            result = re.search(archive_regex, path.name) is not None
    except (IOError, OSError):
        return result

    return result


def pretty_file_size(size, use_decimal=False, **kwargs):
    """
    Return a human-readable representation of the provided ``size``.

    :param size: The size to convert
    :param use_decimal: use decimal instead of binary prefixes (e.g. kilo = 1000 instead of 1024)

    :keyword units: A list of unit names in ascending order.
        Default units: ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    :return: The converted size
    """
    try:
        size = max(float(size), 0.0)
    except (ValueError, TypeError):
        size = 0.0

    remaining_size = size
    units = kwargs.pop("units", ["B", "KB", "MB", "GB", "TB", "PB"])
    block = 1024.0 if not use_decimal else 1000.0
    for unit in units:
        if remaining_size < block:
            return "{0:3.2f} {1}".format(remaining_size, unit)
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
        default is the lowest unit on the scale, e.g. bytes

    :returns: the number of bytes, the default value, or 0
    """
    result = None

    try:
        sep = kwargs.pop("sep", " ")
        scale = kwargs.pop("units", ["B", "KB", "MB", "GB", "TB", "PB"])
        default_units = kwargs.pop("default_units", scale[0])

        if sep:
            size_tuple = size.strip().split(sep)
            scalar, units = size_tuple[0], size_tuple[1:]
            units = units[0].upper() if units else default_units
        else:
            regex_scalar = re.search(r"([\d. ]+)", size, re.I)
            scalar = regex_scalar.group() if regex_scalar else -1
            units = size.strip(scalar) if scalar != -1 else "B"

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


def remove_extension(filename: Union[Path, PathLike, str]) -> Union[Path, PathLike, str]:
    """
    Remove the extension of the provided ``filename``.
    The extension is only removed if it is in MEDIA_EXTENSIONS or ['nzb', 'torrent'].
    :param filename: The filename from which we want to remove the extension
    :return: The ``filename`` without its extension.
    """
    path = Path(filename)
    if not path.name:
        return filename

    is_media = get_extension(path, lower=True) in ["nzb", "torrent"] + MEDIA_EXTENSIONS
    return type(filename)((path, path.with_suffix(""))[is_media])


def replace_extension(filename: Union[Path, PathLike, str], new_extension: str) -> Union[Path, PathLike, str]:
    """
    Replace the extension of the provided ``filename`` with a new extension.
    :param filename: The filename for which we want to change the extension
    :param new_extension: The new extension to apply on the ``filename``
    :return: The ``filename`` with the new extension
    """
    if not isinstance(new_extension, (PathLike, str)):
        raise TypeError()

    path = Path(filename)
    if not path.name:
        return filename
    if not path.suffix:
        return filename

    if new_extension and not new_extension.startswith("."):
        new_extension = f".{new_extension}"

    return type(filename)(path.with_suffix(new_extension))


def sanitize_filename(filename):
    """
    Remove specific characters from the provided ``filename``.
    :param filename: The filename to clean
    :return: The ``filename``cleaned
    """

    if isinstance(filename, bytes):
        filename = filename.decode()

    if isinstance(filename, str):
        filename = re.sub(r"[\\/*]", "-", filename)
        filename = re.sub(r'[:"<>|?]', "", filename)
        filename = re.sub(r"™|-u2122", "", filename)  # Trademark Sign unicode: \u2122
        filename = filename.strip(" .")

        return filename

    return ""


def valid_url(url):
    try:
        valid = validators.url(url)
    except validators.utils.ValidationError:
        valid = False  # ValidationError isn't an exception so doesn't actually get here

    if not valid:
        valid = False  # if ValidationError in response set to False

    return valid


def try_int(candidate, default_value=0) -> int:
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


def try_float(candidate, default_value=0) -> float:
    """
    Try to convert ``candidate`` to int, or return the ``default_value``.
    :param candidate: The value to convert to int
    :param default_value: The value to return if the conversion fails
    :return: ``candidate`` as int, or ``default_value`` if the conversion fails
    """

    try:
        return float(candidate)
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

    numbering = kwargs.pop("numbering", "standard")

    if season or episode:
        if numbering == "standard":
            if season is not None and episode is not None:
                return f"S{season:02}E{episode:02}"
        elif numbering == "absolute":
            if episode is None:
                return f"{season:03}"


def choose_data_dir(program_dir) -> Path:
    old_data_dir = Path(program_dir).parent
    old_profile_path = Path.home().joinpath("sickchill")
    proper_data_dir = Path(appdirs.user_config_dir(appname="sickchill"))
    for location in [old_data_dir, old_profile_path, proper_data_dir]:
        for check in ["sickbeard.db", "sickchill.db", "config.ini"]:
            if location.joinpath(check).exists():
                return location.resolve()
    return proper_data_dir.resolve()
