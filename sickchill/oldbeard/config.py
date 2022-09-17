import datetime
import os.path
import platform
import re
from urllib import parse

import rarfile
from tornado.escape import xhtml_unescape

import sickchill.start
from sickchill import logger, settings
from sickchill.helper.common import try_int

from . import db, helpers, naming

# Address poor support for scgi over unix domain sockets
# this is not nicely handled by python currently
# http://bugs.python.org/issue23636
parse.uses_netloc.append("scgi")

naming_ep_type = (
    "%(seasonnumber)dx%(episodenumber)02d",
    "s%(seasonnumber)02de%(episodenumber)02d",
    "S%(seasonnumber)02dE%(episodenumber)02d",
    "%(seasonnumber)02dx%(episodenumber)02d",
)

sports_ep_type = (
    "%(seasonnumber)dx%(episodenumber)02d",
    "s%(seasonnumber)02de%(episodenumber)02d",
    "S%(seasonnumber)02dE%(episodenumber)02d",
    "%(seasonnumber)02dx%(episodenumber)02d",
)

naming_ep_type_text = ("1x02", "s01e02", "S01E02", "01x02")

naming_multi_ep_type = {
    0: ["-%(episodenumber)02d"] * len(naming_ep_type),
    1: [" - " + x for x in naming_ep_type],
    2: [x + "%(episodenumber)02d" for x in ("x", "e", "E", "x")],
}
naming_multi_ep_type_text = ("extend", "duplicate", "repeat")

naming_sep_type = (" - ", " ")
naming_sep_type_text = (" - ", "space")


def change_https_cert(https_cert):
    """
    Replace HTTPS Certificate file path

    :param https_cert: path to the new certificate file
    :return: True on success, False on failure
    """
    if https_cert == "":
        settings.HTTPS_CERT = ""
        return True

    if os.path.normpath(settings.HTTPS_CERT) != os.path.normpath(https_cert):
        if helpers.makeDir(os.path.dirname(os.path.abspath(https_cert))):
            settings.HTTPS_CERT = os.path.normpath(https_cert)
            logger.info("Changed https cert path to " + https_cert)
        else:
            return False

    return True


def change_https_key(https_key):
    """
    Replace HTTPS Key file path

    :param https_key: path to the new key file
    :return: True on success, False on failure
    """
    if not https_key:
        settings.HTTPS_KEY = ""
        return True

    if os.path.normpath(settings.HTTPS_KEY) != os.path.normpath(https_key):
        if helpers.makeDir(os.path.dirname(os.path.abspath(https_key))):
            settings.HTTPS_KEY = os.path.normpath(https_key)
            logger.info("Changed https key path to " + https_key)
        else:
            return False

    return True


def change_unrar_tool(unrar_tool, unar_tool):
    try:
        rarfile.tool_setup()
    except rarfile.RarCannotExec:
        pass
    else:
        settings.UNAR_TOOL = rarfile.UNRAR_TOOL
        settings.UNAR_TOOL = rarfile.UNAR_TOOL
        return True

    _unrar_tool = rarfile.UNRAR_TOOL
    _unar_tool = rarfile.UNAR_TOOL

    if unrar_tool and unrar_tool != rarfile.UNRAR_TOOL:
        rarfile.UNRAR_TOOL = unrar_tool

    if unar_tool and unar_tool != rarfile.UNAR_TOOL:
        rarfile.UNAR_TOOL = unar_tool

    try:
        rarfile.tool_setup()
    except rarfile.RarCannotExec:
        pass
    else:
        settings.UNAR_TOOL = rarfile.UNRAR_TOOL
        settings.UNAR_TOOL = rarfile.UNAR_TOOL
        return True

    rarfile.UNRAR_TOOL = _unar_tool
    rarfile.UNAR_TOOL = _unar_tool

    if platform.system() == "Windows":
        # Look for WinRAR installations
        winrar_path = "WinRAR\\UnRAR.exe"
        # Make a set of unique paths to check from existing environment variables
        check_locations = {
            os.path.join(location, winrar_path)
            for location in (
                os.environ.get("ProgramW6432"),
                os.environ.get("ProgramFiles(x86)"),
                os.environ.get("ProgramFiles"),
                re.sub(r"\s?\(x86\)", "", os.environ["ProgramFiles"]),
            )
            if location
        }
        check_locations.add(os.path.join(settings.DATA_DIR, "unrar\\unrar.exe"))

        for check in check_locations:
            if os.path.isfile(check):
                try:
                    rarfile.UNRAR_TOOL = check
                    rarfile.tool_setup()
                    settings.UNRAR_TOOL = check
                    return True
                except rarfile.RarCannotExec:
                    pass

        logger.info("Trying to download unrar.exe and set the path")
        unrar_store = os.path.join(settings.DATA_DIR, "unrar")  # ./unrar (folder)
        unrar_zip = os.path.join(settings.DATA_DIR, "unrar_win.zip")  # file download

        if helpers.download_file("https://sickchill.github.io/unrar/unrar_win.zip", filename=unrar_zip, session=helpers.make_session()) and helpers.extractZip(
            archive=unrar_zip, targetDir=unrar_store
        ):
            try:
                os.remove(unrar_zip)
            except OSError as error:
                logger.info(f"Unable to delete downloaded file {unrar_zip}: {error}. You may delete it manually")

            check = os.path.join(unrar_store, "unrar.exe")
            try:
                rarfile.UNRAR_TOOL = check
                rarfile.tool_setup()
                settings.UNRAR_TOOL = check
                logger.info("Successfully downloaded unrar.exe and set as unrar tool")
                return True
            except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
                logger.info("Sorry, unrar was not set up correctly. Try installing WinRAR and make sure it is on the system PATH")
        else:
            logger.info("Unable to download unrar.exe")

    # These must always be set to something before returning
    settings.UNRAR_TOOL = rarfile.UNRAR_TOOL = _unrar_tool
    settings.UNAR_TOOL = rarfile.UNAR_TOOL = _unar_tool

    try:
        rarfile.tool_setup()
        return True
    except rarfile.RarCannotExec:
        if settings.UNPACK == settings.UNPACK_PROCESS_CONTENTS:
            logger.info(_("Disabling UNPACK setting because no unrar/unar/bsdtar is found and accessible in the path or setting."))
            settings.UNPACK = settings.UNPACK_DISABLED
        return False


def change_sickchill_background(background):
    """
    Replace background image file path

    :param background: path to the new background image
    :return: True on success, False on failure
    """
    if not background:
        settings.SICKCHILL_BACKGROUND_PATH = ""
        return True

    background = os.path.normpath(background)
    if not os.path.exists(background):
        logger.info(f"Background image does not exist: {background}")
        return False

    settings.SICKCHILL_BACKGROUND_PATH = background

    return True


def change_custom_css(new_css):
    """
    Replace custom css file path

    :param new_css: path to the new css file
    :return: True on success, False on failure
    """
    if not new_css:
        settings.CUSTOM_CSS_PATH = ""
        return True

    new_css = os.path.normpath(new_css)
    if not os.path.isfile(new_css):
        logger.info(f"Custom css file does not exist: {new_css}")
        return False
    if not new_css.endswith("css"):
        logger.info(f"Custom css file should have the .css extension: {new_css}")
        return False

    settings.CUSTOM_CSS_PATH = new_css
    return True


def change_nzb_dir(nzb_dir):
    """
    Change NZB Folder

    :param nzb_dir: New NZB Folder location
    :return: True on success, False on failure
    """
    if nzb_dir == "":
        settings.NZB_DIR = ""
        return True

    if os.path.normpath(settings.NZB_DIR) != os.path.normpath(nzb_dir):
        if helpers.makeDir(nzb_dir):
            settings.NZB_DIR = os.path.normpath(nzb_dir)
            logger.info("Changed NZB folder to " + nzb_dir)
        else:
            return False

    return True


def change_torrent_dir(torrent_dir):
    """
    Change torrent directory

    :param torrent_dir: New torrent directory
    :return: True on success, False on failure
    """
    if torrent_dir == "":
        settings.TORRENT_DIR = ""
        return True

    if os.path.normpath(settings.TORRENT_DIR) != os.path.normpath(torrent_dir):
        if helpers.makeDir(torrent_dir):
            settings.TORRENT_DIR = os.path.normpath(torrent_dir)
            logger.info("Changed torrent folder to " + torrent_dir)
        else:
            return False

    return True


def change_tv_download_dir(tv_download_dir):
    """
    Change TV_DOWNLOAD directory (used by postprocessor)

    :param tv_download_dir: New tv download directory
    :return: True on success, False on failure
    """
    if tv_download_dir == "":
        settings.TV_DOWNLOAD_DIR = ""
        return True

    if os.path.normpath(settings.TV_DOWNLOAD_DIR) != os.path.normpath(tv_download_dir):
        if helpers.makeDir(tv_download_dir):
            settings.TV_DOWNLOAD_DIR = os.path.normpath(tv_download_dir)
            logger.info("Changed TV download folder to " + tv_download_dir)
        else:
            return False

    return True


def change_unpack_dir(unpack_dir):
    """
    Change UNPACK directory (used by postprocessor)

    :param unpack_dir: New unpack directory
    :return: True on success, False on failure
    """
    if unpack_dir == "":
        settings.UNPACK_DIR = ""
        return True

    if os.path.normpath(settings.UNPACK_DIR) != os.path.normpath(unpack_dir):
        if bool(settings.ROOT_DIRS) and any(helpers.is_subdirectory(unpack_dir, rd) for rd in settings.ROOT_DIRS.split("|")[1:]):
            # don't change if it's in any of the TV root directories
            logger.info("Unable to change unpack directory to a sub-directory of a TV root dir")
            return False

        if helpers.makeDir(unpack_dir):
            settings.UNPACK_DIR = os.path.normpath(unpack_dir)
            logger.info("Changed unpack directory to " + unpack_dir)
        else:
            logger.info("Unable to create unpack directory " + os.path.normpath(unpack_dir) + ", dir not changed.")
            return False

    return True


def change_postprocessor_frequency(freq):
    """
    Change frequency of automatic postprocessing thread

    :param freq: New frequency
    """
    settings.AUTOPOSTPROCESSOR_FREQUENCY = try_int(freq, settings.DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY)

    if settings.AUTOPOSTPROCESSOR_FREQUENCY < settings.MIN_AUTOPOSTPROCESSOR_FREQUENCY:
        settings.AUTOPOSTPROCESSOR_FREQUENCY = settings.MIN_AUTOPOSTPROCESSOR_FREQUENCY

    settings.autoPostProcessorScheduler.cycleTime = datetime.timedelta(minutes=settings.AUTOPOSTPROCESSOR_FREQUENCY)
    return True


def change_daily_search_frequency(freq):
    """
    Change frequency of daily search thread

    :param freq: New frequency
    """
    settings.DAILYSEARCH_FREQUENCY = try_int(freq, settings.DEFAULT_DAILYSEARCH_FREQUENCY)

    if settings.DAILYSEARCH_FREQUENCY < settings.MIN_DAILYSEARCH_FREQUENCY:
        settings.DAILYSEARCH_FREQUENCY = settings.MIN_DAILYSEARCH_FREQUENCY

    settings.dailySearchScheduler.cycleTime = datetime.timedelta(minutes=settings.DAILYSEARCH_FREQUENCY)
    return True


def change_backlog_frequency(freq):
    """
    Change frequency of backlog thread

    :param freq: New frequency
    """
    settings.BACKLOG_FREQUENCY = try_int(freq, settings.DEFAULT_BACKLOG_FREQUENCY)

    settings.MIN_BACKLOG_FREQUENCY = settings.get_backlog_cycle_time()
    if settings.BACKLOG_FREQUENCY < settings.MIN_BACKLOG_FREQUENCY:
        settings.BACKLOG_FREQUENCY = settings.MIN_BACKLOG_FREQUENCY

    settings.backlogSearchScheduler.cycleTime = datetime.timedelta(minutes=settings.BACKLOG_FREQUENCY)
    return True


def change_update_frequency(freq):
    """
    Change frequency of daily updater thread

    :param freq: New frequency
    """
    settings.UPDATE_FREQUENCY = try_int(freq, settings.DEFAULT_UPDATE_FREQUENCY)

    if settings.UPDATE_FREQUENCY < settings.MIN_UPDATE_FREQUENCY:
        settings.UPDATE_FREQUENCY = settings.MIN_UPDATE_FREQUENCY

    settings.versionCheckScheduler.cycleTime = datetime.timedelta(hours=settings.UPDATE_FREQUENCY)
    return True


def change_showupdate_hour(freq):
    """
    Change frequency of show updater thread

    :param freq: New frequency
    """
    settings.SHOWUPDATE_HOUR = try_int(freq, settings.DEFAULT_SHOWUPDATE_HOUR)

    if settings.SHOWUPDATE_HOUR > 23:
        settings.SHOWUPDATE_HOUR = 0
    elif settings.SHOWUPDATE_HOUR < 0:
        settings.SHOWUPDATE_HOUR = 0

    settings.showUpdateScheduler.start_time = datetime.time(hour=settings.SHOWUPDATE_HOUR)
    return True


def change_subtitle_finder_frequency(subtitles_finder_frequency):
    """
    Change frequency of subtitle thread

    :param subtitles_finder_frequency: New frequency
    """
    if subtitles_finder_frequency == "" or subtitles_finder_frequency is None:
        subtitles_finder_frequency = 1

    settings.SUBTITLES_FINDER_FREQUENCY = try_int(subtitles_finder_frequency, 1)
    return True


def change_version_notify(version_notify):
    """
    Enable/Disable versioncheck thread

    :param version_notify: New desired state
    """
    version_notify = checkbox_to_value(version_notify)

    if settings.VERSION_NOTIFY == version_notify:
        return True

    settings.VERSION_NOTIFY = version_notify
    if settings.VERSION_NOTIFY:
        if not settings.versionCheckScheduler.enable:
            logger.info("Starting VERSIONCHECK thread")
            settings.versionCheckScheduler.silent = False
            settings.versionCheckScheduler.enable = True
            settings.versionCheckScheduler.forceRun()
    else:
        settings.versionCheckScheduler.enable = False
        settings.versionCheckScheduler.silent = True
        logger.info("Stopping VERSIONCHECK thread")

    return True


def change_download_propers(download_propers):
    """
    Enable/Disable proper download thread

    :param download_propers: New desired state
    """
    download_propers = checkbox_to_value(download_propers)

    if settings.DOWNLOAD_PROPERS == download_propers:
        return True

    settings.DOWNLOAD_PROPERS = download_propers
    if settings.DOWNLOAD_PROPERS:
        if not settings.properFinderScheduler.enable:
            logger.info("Starting PROPERFINDER thread")
            settings.properFinderScheduler.silent = False
            settings.properFinderScheduler.enable = True
    else:
        settings.properFinderScheduler.enable = False
        settings.properFinderScheduler.silent = True
        logger.info("Stopping PROPERFINDER thread")

    return True


def change_use_trakt(use_trakt):
    """
    Enable/disable trakt thread

    :param use_trakt: New desired state
    """
    use_trakt = checkbox_to_value(use_trakt)

    if settings.USE_TRAKT == use_trakt:
        return True

    settings.USE_TRAKT = use_trakt
    if settings.USE_TRAKT:
        if not settings.traktCheckerScheduler.enable:
            logger.info("Starting TRAKTCHECKER thread")
            settings.traktCheckerScheduler.silent = False
            settings.traktCheckerScheduler.enable = True
    else:
        settings.traktCheckerScheduler.enable = False
        settings.traktCheckerScheduler.silent = True
        logger.info("Stopping TRAKTCHECKER thread")

    return True


def change_use_subtitles(use_subtitles):
    """
    Enable/Disable subtitle searcher

    :param use_subtitles: New desired state
    """
    use_subtitles = checkbox_to_value(use_subtitles)

    if settings.USE_SUBTITLES == use_subtitles:
        return True

    settings.USE_SUBTITLES = use_subtitles
    if settings.USE_SUBTITLES:
        if not settings.subtitlesFinderScheduler.enable:
            logger.info("Starting SUBTITLESFINDER thread")
            settings.subtitlesFinderScheduler.silent = False
            settings.subtitlesFinderScheduler.enable = True
    else:
        settings.subtitlesFinderScheduler.enable = False
        settings.subtitlesFinderScheduler.silent = True
        logger.debug("Stopping SUBTITLESFINDER thread")

    return True


def change_process_automatically(process_automatically):
    """
    Enable/Disable postprocessor thread

    :param process_automatically: New desired state
    """
    process_automatically = checkbox_to_value(process_automatically)

    if settings.PROCESS_AUTOMATICALLY == process_automatically:
        return True

    settings.PROCESS_AUTOMATICALLY = process_automatically
    if settings.PROCESS_AUTOMATICALLY:
        if not settings.autoPostProcessorScheduler.enable:
            logger.info("Starting POSTPROCESSOR thread")
            settings.autoPostProcessorScheduler.silent = False
            settings.autoPostProcessorScheduler.enable = True
    else:
        logger.info("Stopping POSTPROCESSOR thread")
        settings.autoPostProcessorScheduler.enable = False
        settings.autoPostProcessorScheduler.silent = True

    return True


def change_log_dir(log_dir):
    """
    Change logs directory

    :param log_dir: New logs directory
    :return: True on success, False on failure
    """
    if log_dir == "":
        settings.LOG_DIR = os.path.normpath(os.path.join(settings.DATA_DIR, "Logs"))
        return True

    if os.path.normpath(settings.LOG_DIR) != os.path.normpath(log_dir):
        if helpers.makeDir(os.path.normpath(log_dir)) and os.access(os.path.normpath(log_dir), os.W_OK):
            settings.LOG_DIR = os.path.normpath(log_dir)
            logger.info(_("Changed logs folder to {directory} sickchill must be restarted for changes de take effect").format(directory=log_dir))

        else:
            return False

    return True


def check_section(cfg, sec):
    """Check if INI section exists, if not create it"""

    if sec in cfg:
        return True

    cfg[sec] = {}
    return False


def checkbox_to_value(option, value_on=True, value_off=False):
    """
    Turns checkbox option 'on' or 'true' to value_on (True)
    any other value returns value_off (False)
    """

    if isinstance(option, list):
        option = option[-1]
    if isinstance(option, str):
        option = option.strip().lower()

    if option in (True, "on", "true", value_on) or try_int(option) > 0:
        return value_on

    return value_off


def clean_host(host, default_port=None):
    """
    Returns host or host:port or empty string from a given url or host
    If no port is found and default_port is given use host:default_port
    """

    host = host.strip()
    if host:
        match_host_port = re.search(r"(?:http.*://)?(?P<host>[^:/]+).?(?P<port>[0-9]*).*", host)

        cleaned_host = match_host_port.group("host")
        cleaned_port = match_host_port.group("port")
        if cleaned_host:
            if cleaned_port:
                host = cleaned_host + ":" + cleaned_port
            elif default_port:
                host = f"{cleaned_host}:{default_port}"
            else:
                host = cleaned_host
        else:
            host = ""

    return host


def clean_hosts(hosts, default_port=None):
    """
    Returns list of cleaned hosts by clean_host

    :param hosts: list of hosts
    :param default_port: default port to use
    :return: list of cleaned hosts
    """
    cleaned_hosts = []

    for cur_host in [host.strip() for host in hosts.split(",") if host.strip()]:
        cleaned_host = clean_host(cur_host, default_port)
        if cleaned_host:
            cleaned_hosts.append(cleaned_host)

    cleaned_hosts = ",".join(cleaned_hosts) if cleaned_hosts else ""

    return cleaned_hosts


def clean_url(url):
    """
    Returns an cleaned url starting with a scheme and folder with trailing /
    or an empty string
    """

    if url and url.strip():
        url = xhtml_unescape(url.strip())

        if "://" not in url:
            url = "//" + url

        scheme, netloc, path, query, fragment = parse.urlsplit(url, "http")
        if not path:
            path += "/"

        cleaned_url = parse.urlunsplit((scheme, netloc, path, query, fragment))

    else:
        cleaned_url = ""

    return cleaned_url


################################################################################
# min_max                                                                      #
################################################################################
def min_max(val, default, low, high):
    """Return value forced within range"""

    val = try_int(val, default)

    if val < low:
        return low
    if val > high:
        return high

    return val


################################################################################
# check_setting_int                                                            #
################################################################################
def check_setting_int(config, cfg_name, item_name, def_val=0, min_val=None, max_val=None, fallback_def=True, silent=True):
    """
    Checks config setting of integer type

    :param config: config object
    :type config: ConfigObj()
    :param cfg_name: section name of config
    :param item_name: item name of section
    :param def_val: default value to return in case a value can't be retrieved from config,
                    or in case value couldn't be converted,
                    or if `value < min_val` or `value > max_val` (default: 0)
    :param min_val: force value to be greater than or equal to `min_val` (optional)
    :param max_val: force value to be lesser than or equal to `max_val` (optional)
    :param fallback_def: if True, `def_val` will be returned when value not in range of `min_val` and `max_val`.
                         otherwise, `min_val`/`max_val` value will be returned respectively (default: True)
    :param silent: don't log result to debug log (default: True)

    :return: value of `config[cfg_name][item_name]` or `min_val`/`max_val` (see def_low_high) `def_val` (see def_val)
    :rtype: int
    """
    if not isinstance(def_val, int):
        logger.error("{dom}:{key} default value is not the correct type. Expected {t}, got {dt}".format(dom=cfg_name, key=item_name, t="int", dt=type(def_val)))

    if not (min_val is None or isinstance(min_val, int)):
        logger.error("{dom}:{key} min_val value is not the correct type. Expected {t}, got {dt}".format(dom=cfg_name, key=item_name, t="int", dt=type(min_val)))

    if not (max_val is None or isinstance(max_val, int)):
        logger.error("{dom}:{key} max_val value is not the correct type. Expected {t}, got {dt}".format(dom=cfg_name, key=item_name, t="int", dt=type(max_val)))

    try:
        if not (check_section(config, cfg_name) and check_section(config[cfg_name], item_name)):
            raise ValueError

        my_val = config[cfg_name][item_name]

        if str(my_val).lower() == "true":
            my_val = 1
        elif str(my_val).lower() == "false":
            my_val = 0

        my_val = int(my_val)

        if isinstance(min_val, int) and my_val < min_val:
            my_val = config[cfg_name][item_name] = (min_val, def_val)[fallback_def]
        if isinstance(max_val, int) and my_val > max_val:
            my_val = config[cfg_name][item_name] = (max_val, def_val)[fallback_def]

    except (ValueError, IndexError, KeyError, TypeError):
        my_val = def_val

        if cfg_name not in config:
            config[cfg_name] = {}

        config[cfg_name][item_name] = my_val

    if not silent:

        logger.debug(f"{item_name} -> {my_val}")

    return my_val


################################################################################
# check_setting_float                                                          #
################################################################################
def check_setting_float(config, cfg_name, item_name, def_val=0.0, min_val=None, max_val=None, fallback_def=True, silent=True):
    """
    Checks config setting of float type

    :param config: config object
    :type config: ConfigObj()
    :param cfg_name: section name of config
    :param item_name: item name of section
    :param def_val: default value to return in case a value can't be retrieved from config
                    or if couldn't be converted,
                    or if `value < min_val` or `value > max_val` (default: 0.0)
    :param min_val: force value to be greater than or equal to `min_val` (optional)
    :param max_val: force value to be lesser than or equal to `max_val` (optional)
    :param fallback_def: if True, `def_val` will be returned when value not in range of `min_val` and `max_val`.
                         otherwise, `min_val`/`max_val` value will be returned respectively (default: True)
    :param silent: don't log result to debug log (default: True)

    :return: value of `config[cfg_name][item_name]` or `min_val`/`max_val` (see def_low_high) `def_val` (see def_val)
    :rtype: float
    """
    if not isinstance(def_val, float):
        logger.error(
            "{dom}:{key} default value is not the correct type. Expected {t}, got {dt}".format(dom=cfg_name, key=item_name, t="float", dt=type(def_val))
        )

    if not (min_val is None or isinstance(min_val, float)):
        logger.error(
            "{dom}:{key} min_val value is not the correct type. Expected {t}, got {dt}".format(dom=cfg_name, key=item_name, t="float", dt=type(min_val))
        )

    if not (max_val is None or isinstance(max_val, float)):
        logger.error(
            "{dom}:{key} max_val value is not the correct type. Expected {t}, got {dt}".format(dom=cfg_name, key=item_name, t="float", dt=type(max_val))
        )

    try:
        if not (check_section(config, cfg_name) and check_section(config[cfg_name], item_name)):
            raise ValueError

        my_val = float(config[cfg_name][item_name])

        if isinstance(min_val, float) and my_val < min_val:
            my_val = config[cfg_name][item_name] = (min_val, def_val)[fallback_def]
        if isinstance(max_val, float) and my_val > max_val:
            my_val = config[cfg_name][item_name] = (max_val, def_val)[fallback_def]
    except (ValueError, IndexError, KeyError, TypeError):
        my_val = def_val

        if cfg_name not in config:
            config[cfg_name] = {}

        config[cfg_name][item_name] = my_val

    if not silent:
        logger.debug(f"{item_name} -> {my_val}")

    return my_val


################################################################################
# check_setting_str                                                            #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val=str(""), silent=True, censor_log=False):
    """
    Checks config setting of string types

    :param config: config object
    :type config: ConfigObj()
    :param cfg_name: section name of config
    :param item_name: item name of section
    :param def_val: default value to return in case a value can't be retrieved from config
                    or if couldn't be converted (default: empty str)
    :param silent: don't log result to debug log (default: True)
    :param censor_log: overrides and adds this setting to logger censored items (default: False)

    :return: decrypted value of `config[cfg_name][item_name]`
             or `def_val` (see cases of def_val)
    :rtype: str
    """
    if not isinstance(def_val, str):
        logger.error(
            "{dom}:{key} default value is not the correct type. Expected {t}, got {dt}".format(dom=cfg_name, key=item_name, t="string", dt=type(def_val))
        )

    # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
    encryption_version = (0, settings.ENCRYPTION_VERSION)["password" in item_name]

    try:
        if not (check_section(config, cfg_name) and item_name in config[cfg_name]):
            raise ValueError

        my_val = helpers.decrypt(config[cfg_name][item_name], encryption_version)
        if str(my_val) == str(None) or not str(my_val):
            raise ValueError
    except (ValueError, IndexError, KeyError):
        my_val = def_val

        if cfg_name not in config:
            config[cfg_name] = {}

        config[cfg_name][item_name] = helpers.encrypt(my_val, encryption_version)

    if (censor_log or (cfg_name, item_name) in logger.censored_items.items()) and not item_name.endswith("custom_url"):
        logger.censored_items[cfg_name, item_name] = my_val

    if not silent:
        logger.debug(item_name + " -> " + my_val)

    return str(my_val)


################################################################################
# check_setting_bool                                                           #
################################################################################
def check_setting_bool(config, cfg_name, item_name, def_val=False, silent=True):
    """
    Checks config setting of boolean type

    :param config: config object
    :type config: ConfigObj()
    :param cfg_name: section name of config
    :param item_name: item name of section
    :param def_val: default value to return in case a value can't be retrieved from config
                    or if couldn't be converted (default: False)
    :param silent: don't log result to debug log (default: True)

    :return: value of `config[cfg_name][item_name]`
             or `def_val` (see cases of def_val)
    :rtype: bool
    """
    try:
        if not isinstance(def_val, bool):
            logger.error(
                "{dom}:{key} default value is not the correct type. Expected {t}, got {dt}".format(dom=cfg_name, key=item_name, t="bool", dt=type(def_val))
            )

        if not (check_section(config, cfg_name) and item_name in config[cfg_name]):
            raise ValueError

        my_val = config[cfg_name][item_name]
        my_val = str(my_val)
        if my_val == str(None) or not my_val:
            raise ValueError

        my_val = checkbox_to_value(my_val)
    except (KeyError, IndexError, ValueError):
        my_val = bool(def_val)

        if cfg_name not in config:
            config[cfg_name] = {}

        config[cfg_name][item_name] = my_val

    if not silent:
        logger.debug(f"{item_name} -> {my_val}")

    return my_val


class ConfigMigrator(object):
    def __init__(self, config_obj):
        """
        Initializes a config migrator that can take the config from the version indicated in the config
        file up to the version required by SB
        """

        self.config_obj = config_obj

        # check the version of the config
        self.config_version = check_setting_int(config_obj, "General", "config_version", settings.CONFIG_VERSION)
        self.expected_config_version = settings.CONFIG_VERSION
        self.migration_names = {
            1: "Custom naming",
            2: "Sync backup number with version number",
            3: "Rename omgwtfnzb variables",
            4: "Add newznab catIDs",
            5: "Metadata update",
            6: "Convert from XBMC to new KODI variables",
            7: "Use version 2 for password encryption",
            8: "Convert Plex setting keys",
            9: "Rename autopostprocesser (typo) to autopostprocessor",
            10: "Refactor flatten_folders_default to season_folders_default",
            11: "Remove old Kodi notifier, and move Kodi 12+ settings under the correct variables",
            12: "Convert new_qbittorrent and rtorrent9 setting to qbittorent and rtorrent",
        }

    def migrate_config(self):
        """
        Calls each successive migration until the config is the same version as SB expects
        """

        if self.config_version > self.expected_config_version:
            logger.log_error_and_exit(
                """Your config version ({0:d}) has been incremented past what this version of SickChill supports ({1:d}).
                If you have used other forks or a newer version of SickChill, your config file may be unusable due to their modifications.""".format(
                    self.config_version, self.expected_config_version
                )
            )

        settings.CONFIG_VERSION = self.config_version

        while self.config_version < self.expected_config_version:
            next_version = self.config_version + 1

            if next_version in self.migration_names:
                migration_name = ": " + self.migration_names[next_version]
            else:
                migration_name = ""

            logger.info("Backing up config before upgrade")
            if not helpers.backupVersionedFile(settings.CONFIG_FILE, self.config_version):
                logger.log_error_and_exit("Config backup failed, abort upgrading config")
            else:
                logger.info("Proceeding with upgrade")

            # do the migration, expect a method named _migrate_v<num>
            logger.info(f"Migrating cofig up to version {next_version}{migration_name}")
            getattr(self, f"_migrate_v{next_version}")()
            self.config_version = next_version

            # save new config after migration
            settings.CONFIG_VERSION = self.config_version
            logger.info("Saving config file to disk")
            sickchill.start.save_config()

    # Migration v1: Custom naming
    def _migrate_v1(self):
        """
        Reads in the old naming settings from your config and generates a new config template from them.
        """

        settings.NAMING_PATTERN = self._name_to_pattern()
        logger.info("Based on your old settings I'm setting your new naming pattern to: " + settings.NAMING_PATTERN)

        settings.NAMING_CUSTOM_ABD = check_setting_bool(self.config_obj, "General", "naming_dates")

        if settings.NAMING_CUSTOM_ABD:
            settings.NAMING_ABD_PATTERN = self._name_to_pattern(True)
            logger.info("Adding a custom air-by-date naming pattern to your config: " + settings.NAMING_ABD_PATTERN)
        else:
            settings.NAMING_ABD_PATTERN = naming.name_abd_presets[0]

        settings.NAMING_MULTI_EP = int(check_setting_int(self.config_obj, "General", "naming_multi_ep_type", 1))

        # see if any of their shows used season folders
        main_db_con = db.DBConnection()
        season_folder_shows = main_db_con.select("SELECT indexer_id FROM tv_shows WHERE flatten_folders = 0 LIMIT 1")

        # if any shows had season folders on then prepend season folder to the pattern
        if season_folder_shows:

            old_season_format = check_setting_str(self.config_obj, "General", "season_folders_format", "Season %02d")

            if old_season_format:
                try:
                    new_season_format = old_season_format % 9
                    new_season_format = str(new_season_format).replace("09", "%0S")
                    new_season_format = new_season_format.replace("9", "%S")

                    logger.info("Changed season folder format from " + old_season_format + " to " + new_season_format + ", prepending it to your naming config")
                    settings.NAMING_PATTERN = new_season_format + os.sep + settings.NAMING_PATTERN

                except (TypeError, ValueError):
                    logger.exception("Can't change " + old_season_format + " to new season format")

        # if no shows had it on then don't flatten any shows and don't put season folders in the config
        else:

            logger.info("No shows were using season folders before, so I'm disabling flattening on all shows")

            # don't flatten any shows at all
            main_db_con.action("UPDATE tv_shows SET flatten_folders = 0 WHERE 1")

        settings.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()

    def _name_to_pattern(self, abd=False):

        # get the old settings from the file
        use_periods = check_setting_bool(self.config_obj, "General", "naming_use_periods")
        ep_type = check_setting_int(self.config_obj, "General", "naming_ep_type")
        sep_type = check_setting_int(self.config_obj, "General", "naming_sep_type")
        use_quality = check_setting_bool(self.config_obj, "General", "naming_quality")

        use_show_name = check_setting_bool(self.config_obj, "General", "naming_show_name", True)
        use_ep_name = check_setting_bool(self.config_obj, "General", "naming_ep_name", True)

        # make the presets into templates
        _naming_ep_type = ("%Sx%0E", "s%0Se%0E", "S%0SE%0E", "%0Sx%0E")

        # set up our data to use
        if use_periods:
            show_name = "%S.N"
            ep_name = "%E.N"
            ep_quality = "%Q.N"
            abd_string = "%A.D"
        else:
            show_name = "%SN"
            ep_name = "%EN"
            ep_quality = "%QN"
            abd_string = "%A-D"

        if abd and abd_string:
            ep_string = abd_string
        else:
            ep_string = _naming_ep_type[ep_type]

        finalName = ""

        # start with the show name
        if use_show_name and show_name:
            finalName += show_name + naming_sep_type[sep_type]

        # add the season/ep stuff
        finalName += ep_string

        # add the episode name
        if use_ep_name and ep_name:
            finalName += naming_sep_type[sep_type] + ep_name

        # add the quality
        if use_quality and ep_quality:
            finalName += naming_sep_type[sep_type] + ep_quality

        if use_periods:
            finalName = re.sub(r"\s+", ".", finalName)

        return finalName

    # Migration v2: Dummy migration to sync backup number with config version number
    @staticmethod
    def _migrate_v2():
        return

    # Migration v3: Rename omgwtfnzb variables
    def _migrate_v3(self):
        """
        Reads in the old naming settings from your config and generates a new config template from them.
        """
        # get the old settings from the file and store them in the new variable names
        settings.OMGWTFNZBS_USERNAME = check_setting_str(self.config_obj, "omgwtfnzbs", "omgwtfnzbs_uid")
        settings.OMGWTFNZBS_APIKEY = check_setting_str(self.config_obj, "omgwtfnzbs", "omgwtfnzbs_key")

    # Migration v4: Add default newznab catIDs
    def _migrate_v4(self):
        """Update newznab providers so that the category IDs can be set independently via the config"""

        new_newznab_data = []
        old_newznab_data = check_setting_str(self.config_obj, "Newznab", "newznab_data")

        if old_newznab_data:
            old_newznab_data_list = old_newznab_data.split("!!!")

            for cur_provider_data in old_newznab_data_list:
                try:
                    name, url, key, enabled = cur_provider_data.split("|")
                except ValueError:
                    logger.error("Skipping Newznab provider string: '" + cur_provider_data + "', incorrect format")
                    continue

                if name == "Sick Beard Index":
                    key = "0"

                if name == "NZBs.org":
                    catIDs = "5030,5040,5060,5070,5090"
                else:
                    catIDs = "5030,5040,5060"

                cur_provider_data_list = [name, url, key, catIDs, enabled]
                new_newznab_data.append("|".join(cur_provider_data_list))

            settings.NEWZNAB_DATA = "!!!".join(new_newznab_data)

    # Migration v5: Metadata upgrade
    def _migrate_v5(self):
        """Updates metadata values to the new format"""

        """ Quick overview of what the upgrade does:

        new | old | description (new)
        ----+-----+--------------------
          1 |  1  | show metadata
          2 |  2  | episode metadata
          3 |  4  | show fanart
          4 |  3  | show poster
          5 |  -  | show banner
          6 |  5  | episode thumb
          7 |  6  | season poster
          8 |  -  | season banner
          9 |  -  | season all poster
         10 |  -  | season all banner

        Note that the ini places start at 1 while the list index starts at 0.
        old format: 0|0|0|0|0|0 -- 6 places
        new format: 0|0|0|0|0|0|0|0|0|0 -- 10 places

        Drop the use of use_banner option.
        Migrate the poster override to just using the banner option (applies to xbmc only).
        """

        metadata_xbmc = check_setting_str(self.config_obj, "General", "metadata_xbmc", "0|0|0|0|0|0")
        metadata_xbmc_12plus = check_setting_str(self.config_obj, "General", "metadata_xbmc_12plus", "0|0|0|0|0|0")
        metadata_mediabrowser = check_setting_str(self.config_obj, "General", "metadata_mediabrowser", "0|0|0|0|0|0")
        metadata_ps3 = check_setting_str(self.config_obj, "General", "metadata_ps3", "0|0|0|0|0|0")
        metadata_wdtv = check_setting_str(self.config_obj, "General", "metadata_wdtv", "0|0|0|0|0|0")
        metadata_tivo = check_setting_str(self.config_obj, "General", "metadata_tivo", "0|0|0|0|0|0")
        metadata_mede8er = check_setting_str(self.config_obj, "General", "metadata_mede8er", "0|0|0|0|0|0")

        use_banner = check_setting_bool(self.config_obj, "General", "use_banner")

        def _migrate_metadata(metadata, metadata_name, _use_banner):
            cur_metadata = metadata.split("|")
            # if target has the old number of values, do upgrade
            if len(cur_metadata) == 6:
                logger.info("Upgrading " + metadata_name + " metadata, old value: " + metadata)
                cur_metadata.insert(4, "0")
                cur_metadata.append("0")
                cur_metadata.append("0")
                cur_metadata.append("0")
                # swap show fanart, show poster
                cur_metadata[3], cur_metadata[2] = cur_metadata[2], cur_metadata[3]
                # if user was using _use_banner to override the poster, instead enable the banner option and deactivate poster
                if metadata_name == "XBMC" and _use_banner:
                    cur_metadata[4], cur_metadata[3] = cur_metadata[3], "0"
                # write new format
                metadata = "|".join(cur_metadata)
                logger.info("Upgrading " + metadata_name + " metadata, new value: " + metadata)

            elif len(cur_metadata) == 10:

                metadata = "|".join(cur_metadata)
                logger.info("Keeping " + metadata_name + " metadata, value: " + metadata)

            else:
                logger.error("Skipping " + metadata_name + " metadata: '" + metadata + "', incorrect format")
                metadata = "0|0|0|0|0|0|0|0|0|0"
                logger.info("Setting " + metadata_name + " metadata, new value: " + metadata)

            return metadata

        settings.METADATA_XBMC = _migrate_metadata(metadata_xbmc, "XBMC", use_banner)
        settings.METADATA_XBMC_12PLUS = _migrate_metadata(metadata_xbmc_12plus, "XBMC 12+", use_banner)
        settings.METADATA_MEDIABROWSER = _migrate_metadata(metadata_mediabrowser, "MediaBrowser", use_banner)
        settings.METADATA_PS3 = _migrate_metadata(metadata_ps3, "PS3", use_banner)
        settings.METADATA_WDTV = _migrate_metadata(metadata_wdtv, "WDTV", use_banner)
        settings.METADATA_TIVO = _migrate_metadata(metadata_tivo, "TIVO", use_banner)
        settings.METADATA_MEDE8ER = _migrate_metadata(metadata_mede8er, "Mede8er", use_banner)

    # Migration v6: Convert from XBMC to KODI variables
    def _migrate_v6(self):
        settings.USE_KODI = check_setting_bool(self.config_obj, "XBMC", "use_xbmc")
        settings.KODI_ALWAYS_ON = check_setting_bool(self.config_obj, "XBMC", "xbmc_always_on", True)
        settings.KODI_NOTIFY_ONSNATCH = check_setting_bool(self.config_obj, "XBMC", "xbmc_notify_onsnatch")
        settings.KODI_NOTIFY_ONDOWNLOAD = check_setting_bool(self.config_obj, "XBMC", "xbmc_notify_ondownload")
        settings.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(self.config_obj, "XBMC", "xbmc_notify_onsubtitledownload")
        settings.KODI_UPDATE_LIBRARY = check_setting_bool(self.config_obj, "XBMC", "xbmc_update_library")
        settings.KODI_UPDATE_FULL = check_setting_bool(self.config_obj, "XBMC", "xbmc_update_full")
        settings.KODI_UPDATE_ONLYFIRST = check_setting_bool(self.config_obj, "XBMC", "xbmc_update_onlyfirst")
        settings.KODI_HOST = check_setting_str(self.config_obj, "XBMC", "xbmc_host")
        settings.KODI_USERNAME = check_setting_str(self.config_obj, "XBMC", "xbmc_username", censor_log=True)
        settings.KODI_PASSWORD = check_setting_str(self.config_obj, "XBMC", "xbmc_password", censor_log=True)
        settings.METADATA_KODI = check_setting_str(self.config_obj, "General", "metadata_xbmc", "0|0|0|0|0|0|0|0|0|0")
        settings.METADATA_KODI_12PLUS = check_setting_str(self.config_obj, "General", "metadata_xbmc_12plus", "0|0|0|0|0|0|0|0|0|0")

    # Migration v7: Use version 2 for password encryption
    @staticmethod
    def _migrate_v7():
        settings.ENCRYPTION_VERSION = 2

    # Migration v8: Rename plex settings
    def _migrate_v8(self):
        settings.PLEX_CLIENT_HOST = check_setting_str(self.config_obj, "Plex", "plex_host")
        settings.PLEX_SERVER_USERNAME = check_setting_str(self.config_obj, "Plex", "plex_username", censor_log=True)
        settings.PLEX_SERVER_PASSWORD = check_setting_str(self.config_obj, "Plex", "plex_password", censor_log=True)
        settings.USE_PLEX_SERVER = check_setting_bool(self.config_obj, "Plex", "use_plex")

    # Migration v9: Rename autopostprocesser (typo) to autopostprocessor
    def _migrate_v9(self):
        settings.AUTOPOSTPROCESSOR_FREQUENCY = check_setting_str(self.config_obj, "General", "autopostprocesser_frequency")

    # Migration v10: Change flatten_folders_default to season_folders_default (inverted)
    def _migrate_v10(self):
        settings.SEASON_FOLDERS_DEFAULT = not check_setting_str(self.config_obj, "General", "flatten_folders_default")

    # Migration v11: Remove old kodi and only use Kodi 12+
    def _migrate_v11(self):
        settings.METADATA_KODI = check_setting_str(settings.CFG, "General", "metadata_kodi_12plus", "0|0|0|0|0|0|0|0|0|0")

    # Migration v12: Fix selected provider, since there is only one qbittorrent and one rtorrent provider
    def _migrate_v12(self):
        settings.TORRENT_METHOD = re.sub(r"^new_|9$", "", check_setting_str(settings.CFG, "General", "torrent_method", "blackhole"))
