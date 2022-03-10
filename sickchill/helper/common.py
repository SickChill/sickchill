import re
from fnmatch import fnmatch
from pathlib import Path

import appdirs
from github import Github
from github.GithubException import (
    BadAttributeException,
    BadCredentialsException,
    BadUserAgentException,
    GithubException,
    RateLimitExceededException,
    TwoFactorException,
    UnknownObjectException,
)

import sickchill
from sickchill import settings

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
        return "({0})".format(", ".join(description))

    return description


def is_sync_file(filename):
    """
    Check if the provided ``filename`` is a sync file, based on its name.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a sync file, ``False`` otherwise
    """

    if isinstance(filename, str):
        extension = filename.rpartition(".")[2].lower()

        return (
            extension in settings.SYNC_FILES.split(",")
            or filename.startswith(".syncthing")
            or any(fnmatch(filename, match) for match in settings.SYNC_FILES.split(","))
        )

    return False


def is_torrent_or_nzb_file(filename):
    """
    Check if the provided ``filename`` is a NZB file or a torrent file, based on its extension.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a NZB file or a torrent file, ``False`` otherwise
    """

    if not isinstance(filename, str):
        return False

    return filename.rpartition(".")[2].lower() in ["nzb", "torrent"]


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
        default is lowest unit on the scale, e.g. bytes

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


def remove_extension(filename):
    """
    Remove the extension of the provided ``filename``.
    The extension is only removed if it is in MEDIA_EXTENSIONS or ['nzb', 'torrent'].
    :param filename: The filename from which we want to remove the extension
    :return: The ``filename`` without its extension.
    """

    if isinstance(filename, str) and "." in filename:
        basename, dot, extension = filename.rpartition(".")

        if basename and extension.lower() in ["nzb", "torrent"] + MEDIA_EXTENSIONS:
            return basename

    return filename


def replace_extension(filename, new_extension):
    """
    Replace the extension of the provided ``filename`` with a new extension.
    :param filename: The filename for which we want to change the extension
    :param new_extension: The new extension to apply on the ``filename``
    :return: The ``filename`` with the new extension
    """

    if isinstance(filename, str) and "." in filename:
        basename = filename.rpartition(".")[0]
        if basename:
            return "{0}.{1}".format(basename, new_extension)

    return filename


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
        filename = re.sub(r"™|-u2122", "", filename)  # Trade Mark Sign unicode: \u2122
        filename = filename.strip(" .")

        return filename

    return ""


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

    numbering = kwargs.pop("numbering", "standard")

    if numbering == "standard":
        if season is not None and episode:
            return "S{0:0>2}E{1:02}".format(season, episode)
    elif numbering == "absolute":
        if not (season and episode) and (season or episode):
            return "{0:0>3}".format(season or episode)


def setup_github():
    """
    Instantiate the global github connection, for checking for updates and submitting issues
    """

    try:
        if settings.GIT_TOKEN:
            # Token Auth - allows users with Two-Factor Authorization (2FA) enabled on Github to connect their account.
            settings.gh = Github(login_or_token=settings.GIT_TOKEN, user_agent="SickChill")
            # This will trigger:
            # * BadCredentialsException if token is invalid
            # * TwoFactorException if user has enabled Github-2FA
            #   but didn't set a personal token in the configuration.
            settings.gh.get_organization(settings.GIT_ORG)
        if not settings.gh:
            settings.gh = Github(user_agent="SickChill")
            settings.gh.get_organization(settings.GIT_ORG)
    except BadCredentialsException as error:
        settings.gh = None
        sickchill.logger.warning(_("Unable to setup GitHub properly with your github token. Please check your credentials. Error: {0}").format(error))
    except TwoFactorException as error:
        settings.gh = None
        sickchill.logger.warning(
            _("Unable to setup GitHub properly with your github token due to 2FA - Make sure this token works with 2FA. Error: {0}").format(error)
        )
    except RateLimitExceededException as error:
        settings.gh = None
        if settings.GIT_TOKEN:
            sickchill.logger.warning(
                _("Unable to setup GitHub properly, You are currently being throttled by rate limiting for too many requests. Error: {0}").format(error)
            )
        else:
            sickchill.logger.warning(
                _(
                    "Unable to setup GitHub properly, You are currently being throttled by rate limiting for too many requests - Try adding an access token. Error: {0}"
                ).format(error)
            )
    except UnknownObjectException as error:
        settings.gh = None
        sickchill.logger.warning(_("Unable to setup GitHub properly, it seems to be down or your organization/repo is set wrong. Error: {0}").format(error))
    except BadUserAgentException as error:
        settings.gh = None
        sickchill.logger.warning(_("Unable to setup GitHub properly, GitHub doesn't like the user-agent. Error: {0}").format(error))
    except BadAttributeException as error:
        settings.gh = None
        sickchill.logger.error(_("Unable to setup GitHub properly, There might be an error with the library. Error: {0}").format(error))
    except (GithubException, Exception) as error:
        settings.gh = None
        sickchill.logger.error(_("Unable to setup GitHub properly. GitHub will not be available. Error: {0}").format(error))


def choose_data_dir(program_dir):
    old_data_dir = Path(program_dir).parent
    old_profile_path = Path.home().joinpath("sickchill")
    proper_data_dir = Path(appdirs.user_config_dir(appname="sickchill"))
    for location in [old_data_dir, old_profile_path, proper_data_dir]:
        for check in ["sickbeard.db", "sickchill.db", "config.ini"]:
            if location.joinpath(check).exists():
                return location
    return proper_data_dir
