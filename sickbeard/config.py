# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
#
# This file is part of SickRage.
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

from __future__ import print_function, unicode_literals

import datetime
import os.path
import platform
import re

import rarfile
import sickbeard
import six
from sickbeard import db, helpers, logger, naming
from sickrage.helper.common import try_int
from sickrage.helper.encoding import ek
# noinspection PyUnresolvedReferences
from six.moves.urllib import parse

# Address poor support for scgi over unix domain sockets
# this is not nicely handled by python currently
# http://bugs.python.org/issue23636
parse.uses_netloc.append('scgi')

naming_ep_type = ("%(seasonnumber)dx%(episodenumber)02d",
                  "s%(seasonnumber)02de%(episodenumber)02d",
                  "S%(seasonnumber)02dE%(episodenumber)02d",
                  "%(seasonnumber)02dx%(episodenumber)02d")

sports_ep_type = ("%(seasonnumber)dx%(episodenumber)02d",
                  "s%(seasonnumber)02de%(episodenumber)02d",
                  "S%(seasonnumber)02dE%(episodenumber)02d",
                  "%(seasonnumber)02dx%(episodenumber)02d")

naming_ep_type_text = ("1x02", "s01e02", "S01E02", "01x02")

naming_multi_ep_type = {0: ["-%(episodenumber)02d"] * len(naming_ep_type),
                        1: [" - " + x for x in naming_ep_type],
                        2: [x + "%(episodenumber)02d" for x in ("x", "e", "E", "x")]}
naming_multi_ep_type_text = ("extend", "duplicate", "repeat")

naming_sep_type = (" - ", " ")
naming_sep_type_text = (" - ", "space")


def change_https_cert(https_cert):
    """
    Replace HTTPS Certificate file path

    :param https_cert: path to the new certificate file
    :return: True on success, False on failure
    """
    if https_cert == '':
        sickbeard.HTTPS_CERT = ''
        return True

    if ek(os.path.normpath, sickbeard.HTTPS_CERT) != ek(os.path.normpath, https_cert):
        if helpers.makeDir(ek(os.path.dirname, ek(os.path.abspath, https_cert))):
            sickbeard.HTTPS_CERT = ek(os.path.normpath, https_cert)
            logger.log("Changed https cert path to " + https_cert)
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
        sickbeard.HTTPS_KEY = ''
        return True

    if ek(os.path.normpath, sickbeard.HTTPS_KEY) != ek(os.path.normpath, https_key):
        if helpers.makeDir(ek(os.path.dirname, ek(os.path.abspath, https_key))):
            sickbeard.HTTPS_KEY = ek(os.path.normpath, https_key)
            logger.log("Changed https key path to " + https_key)
        else:
            return False

    return True


def change_unrar_tool(unrar_tool, alt_unrar_tool):

    # Check for failed unrar attempt, and remove it
    # Must be done before unrar is ever called or the self-extractor opens and locks startup
    bad_unrar = os.path.join(sickbeard.DATA_DIR, 'unrar.exe')
    if os.path.exists(bad_unrar) and os.path.getsize(bad_unrar) == 447440:
        try:
            os.remove(bad_unrar)
        except OSError as e:
            logger.log("Unable to delete bad unrar.exe file {0}: {1}. You should delete it manually".format(bad_unrar, e.strerror), logger.WARNING)

    try:
        rarfile.custom_check(unrar_tool)
    except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
        # Let's just return right now if the defaults work
        try:
            # noinspection PyProtectedMember
            test = rarfile._check_unrar_tool()
            if test:
                # These must always be set to something before returning
                sickbeard.UNRAR_TOOL = rarfile.UNRAR_TOOL
                sickbeard.ALT_UNRAR_TOOL = rarfile.ALT_TOOL
                return True
        except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
            pass

        if platform.system() == 'Windows':
            # Look for WinRAR installations
            found = False
            winrar_path = 'WinRAR\\UnRAR.exe'
            # Make a set of unique paths to check from existing environment variables
            check_locations = {
                os.path.join(location, winrar_path) for location in (
                    os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles(x86)"),
                    os.environ.get("ProgramFiles"), re.sub(r'\s?\(x86\)', '', os.environ["ProgramFiles"])
                ) if location
            }
            check_locations.add(os.path.join(sickbeard.PROG_DIR, 'unrar\\unrar.exe'))

            for check in check_locations:
                if ek(os.path.isfile, check):
                    # Can use it?
                    try:
                        rarfile.custom_check(check)
                        unrar_tool = check
                        found = True
                        break
                    except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
                        found = False

            # Download
            if not found:
                logger.log('Trying to download unrar.exe and set the path')
                unrar_store = ek(os.path.join, sickbeard.PROG_DIR, 'unrar')  # ./unrar (folder)
                unrar_zip = ek(os.path.join, sickbeard.PROG_DIR, 'unrar_win.zip')  # file download

                if (helpers.download_file(
                    "http://sickrage.github.io/unrar/unrar_win.zip", filename=unrar_zip, session=helpers.make_session()
                ) and helpers.extractZip(archive=unrar_zip, targetDir=unrar_store)):
                    try:
                        ek(os.remove, unrar_zip)
                    except OSError as e:
                        logger.log("Unable to delete downloaded file {0}: {1}. You may delete it manually".format(unrar_zip, e.strerror))

                    check = os.path.join(unrar_store, "unrar.exe")
                    try:
                        rarfile.custom_check(check)
                        unrar_tool = check
                        logger.log('Successfully downloaded unrar.exe and set as unrar tool', )
                    except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
                        logger.log('Sorry, unrar was not set up correctly. Try installing WinRAR and make sure it is on the system PATH')
                else:
                    logger.log('Unable to download unrar.exe')

    # These must always be set to something before returning
    sickbeard.UNRAR_TOOL = rarfile.UNRAR_TOOL = rarfile.ORIG_UNRAR_TOOL = unrar_tool
    sickbeard.ALT_UNRAR_TOOL = rarfile.ALT_TOOL = alt_unrar_tool

    try:
        # noinspection PyProtectedMember
        test = rarfile._check_unrar_tool()
    except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
        if sickbeard.UNPACK == 1:
            logger.log('Disabling UNPACK setting because no unrar is installed.')
            sickbeard.UNPACK = 0
        test = False

    return test


def change_sickrage_background(background):
    """
    Replace background image file path

    :param background: path to the new background image
    :return: True on success, False on failure
    """
    if not background:
        sickbeard.SICKRAGE_BACKGROUND_PATH = ''
        return True

    background = ek(os.path.normpath, background)
    if not ek(os.path.exists, background):
        logger.log("Background image does not exist: {0}".format(background))
        return False

    sickbeard.SICKRAGE_BACKGROUND_PATH = background

    return True


def change_custom_css(new_css):
    """
    Replace custom css file path

    :param new_css: path to the new css file
    :return: True on success, False on failure
    """
    if not new_css:
        sickbeard.CUSTOM_CSS_PATH = ''
        return True

    new_css = ek(os.path.normpath, new_css)
    if not ek(os.path.isfile, new_css):
        logger.log("Custom css file does not exist: {0}".format(new_css))
        return False
    if not new_css.endswith('css'):
        logger.log("Custom css file should have the .css extension: {0}".format(new_css))
        return False

    sickbeard.CUSTOM_CSS_PATH = new_css
    return True


def change_log_dir(log_dir, web_log):
    """
    Change logging directory for application and webserver

    :param log_dir: Path to new logging directory
    :param web_log: Enable/disable web logging
    :return: True on success, False on failure
    """
    abs_log_dir = ek(os.path.normpath, ek(os.path.join, sickbeard.DATA_DIR, log_dir))
    sickbeard.WEB_LOG = checkbox_to_value(web_log)

    if ek(os.path.normpath, sickbeard.LOG_DIR) != abs_log_dir:
        if not helpers.makeDir(abs_log_dir):
            return False

        sickbeard.ACTUAL_LOG_DIR = ek(os.path.normpath, log_dir)
        sickbeard.LOG_DIR = abs_log_dir

        logger.init_logging()
        logger.log("Initialized new log file in " + sickbeard.LOG_DIR)

    return True


def change_nzb_dir(nzb_dir):
    """
    Change NZB Folder

    :param nzb_dir: New NZB Folder location
    :return: True on success, False on failure
    """
    if nzb_dir == '':
        sickbeard.NZB_DIR = ''
        return True

    if ek(os.path.normpath, sickbeard.NZB_DIR) != ek(os.path.normpath, nzb_dir):
        if helpers.makeDir(nzb_dir):
            sickbeard.NZB_DIR = ek(os.path.normpath, nzb_dir)
            logger.log("Changed NZB folder to " + nzb_dir)
        else:
            return False

    return True


def change_torrent_dir(torrent_dir):
    """
    Change torrent directory

    :param torrent_dir: New torrent directory
    :return: True on success, False on failure
    """
    if torrent_dir == '':
        sickbeard.TORRENT_DIR = ''
        return True

    if ek(os.path.normpath, sickbeard.TORRENT_DIR) != ek(os.path.normpath, torrent_dir):
        if helpers.makeDir(torrent_dir):
            sickbeard.TORRENT_DIR = ek(os.path.normpath, torrent_dir)
            logger.log("Changed torrent folder to " + torrent_dir)
        else:
            return False

    return True


def change_tv_download_dir(tv_download_dir):
    """
    Change TV_DOWNLOAD directory (used by postprocessor)

    :param tv_download_dir: New tv download directory
    :return: True on success, False on failure
    """
    if tv_download_dir == '':
        sickbeard.TV_DOWNLOAD_DIR = ''
        return True

    if ek(os.path.normpath, sickbeard.TV_DOWNLOAD_DIR) != ek(os.path.normpath, tv_download_dir):
        if helpers.makeDir(tv_download_dir):
            sickbeard.TV_DOWNLOAD_DIR = ek(os.path.normpath, tv_download_dir)
            logger.log("Changed TV download folder to " + tv_download_dir)
        else:
            return False

    return True


def change_unpack_dir(unpack_dir):
    """
    Change UNPACK directory (used by postprocessor)

    :param unpack_dir: New unpack directory
    :return: True on success, False on failure
    """
    if unpack_dir == '':
        sickbeard.UNPACK_DIR = ''
        return True

    if ek(os.path.normpath, sickbeard.UNPACK_DIR) != ek(os.path.normpath, unpack_dir):
        if bool(sickbeard.ROOT_DIRS) and \
                any(map(lambda rd: helpers.is_subdirectory(unpack_dir, rd), sickbeard.ROOT_DIRS.split('|')[1:])):
            # don't change if it's in any of the TV root directories
            logger.log("Unable to change unpack directory to a sub-directory of a TV root dir")
            return False

        if helpers.makeDir(unpack_dir):
            sickbeard.UNPACK_DIR = ek(os.path.normpath, unpack_dir)
            logger.log("Changed unpack directory to " + unpack_dir)
        else:
            logger.log("Unable to create unpack directory " + ek(os.path.normpath, unpack_dir) + ", dir not changed.")
            return False

    return True


def change_postprocessor_frequency(freq):
    """
    Change frequency of automatic postprocessing thread

    :param freq: New frequency
    """
    sickbeard.AUTOPOSTPROCESSOR_FREQUENCY = try_int(freq, sickbeard.DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY)

    if sickbeard.AUTOPOSTPROCESSOR_FREQUENCY < sickbeard.MIN_AUTOPOSTPROCESSOR_FREQUENCY:
        sickbeard.AUTOPOSTPROCESSOR_FREQUENCY = sickbeard.MIN_AUTOPOSTPROCESSOR_FREQUENCY

    sickbeard.autoPostProcessorScheduler.cycleTime = datetime.timedelta(minutes=sickbeard.AUTOPOSTPROCESSOR_FREQUENCY)
    return True


def change_daily_search_frequency(freq):
    """
    Change frequency of daily search thread

    :param freq: New frequency
    """
    sickbeard.DAILYSEARCH_FREQUENCY = try_int(freq, sickbeard.DEFAULT_DAILYSEARCH_FREQUENCY)

    if sickbeard.DAILYSEARCH_FREQUENCY < sickbeard.MIN_DAILYSEARCH_FREQUENCY:
        sickbeard.DAILYSEARCH_FREQUENCY = sickbeard.MIN_DAILYSEARCH_FREQUENCY

    sickbeard.dailySearchScheduler.cycleTime = datetime.timedelta(minutes=sickbeard.DAILYSEARCH_FREQUENCY)
    return True


def change_backlog_frequency(freq):
    """
    Change frequency of backlog thread

    :param freq: New frequency
    """
    sickbeard.BACKLOG_FREQUENCY = try_int(freq, sickbeard.DEFAULT_BACKLOG_FREQUENCY)

    sickbeard.MIN_BACKLOG_FREQUENCY = sickbeard.get_backlog_cycle_time()
    if sickbeard.BACKLOG_FREQUENCY < sickbeard.MIN_BACKLOG_FREQUENCY:
        sickbeard.BACKLOG_FREQUENCY = sickbeard.MIN_BACKLOG_FREQUENCY

    sickbeard.backlogSearchScheduler.cycleTime = datetime.timedelta(minutes=sickbeard.BACKLOG_FREQUENCY)
    return True


def change_update_frequency(freq):
    """
    Change frequency of daily updater thread

    :param freq: New frequency
    """
    sickbeard.UPDATE_FREQUENCY = try_int(freq, sickbeard.DEFAULT_UPDATE_FREQUENCY)

    if sickbeard.UPDATE_FREQUENCY < sickbeard.MIN_UPDATE_FREQUENCY:
        sickbeard.UPDATE_FREQUENCY = sickbeard.MIN_UPDATE_FREQUENCY

    sickbeard.versionCheckScheduler.cycleTime = datetime.timedelta(hours=sickbeard.UPDATE_FREQUENCY)
    return True


def change_showupdate_hour(freq):
    """
    Change frequency of show updater thread

    :param freq: New frequency
    """
    sickbeard.SHOWUPDATE_HOUR = try_int(freq, sickbeard.DEFAULT_SHOWUPDATE_HOUR)

    if sickbeard.SHOWUPDATE_HOUR > 23:
        sickbeard.SHOWUPDATE_HOUR = 0
    elif sickbeard.SHOWUPDATE_HOUR < 0:
        sickbeard.SHOWUPDATE_HOUR = 0

    sickbeard.showUpdateScheduler.start_time = datetime.time(hour=sickbeard.SHOWUPDATE_HOUR)
    return True

def change_subtitle_finder_frequency(subtitles_finder_frequency):
    """
    Change frequency of subtitle thread

    :param subtitles_finder_frequency: New frequency
    """
    if subtitles_finder_frequency == '' or subtitles_finder_frequency is None:
        subtitles_finder_frequency = 1

    sickbeard.SUBTITLES_FINDER_FREQUENCY = try_int(subtitles_finder_frequency, 1)
    return True


def change_version_notify(version_notify):
    """
    Enable/Disable versioncheck thread

    :param version_notify: New desired state
    """
    version_notify = checkbox_to_value(version_notify)

    if sickbeard.VERSION_NOTIFY == version_notify:
        return True

    sickbeard.VERSION_NOTIFY = version_notify
    if sickbeard.VERSION_NOTIFY:
        if not sickbeard.versionCheckScheduler.enable:
            logger.log("Starting VERSIONCHECK thread", logger.INFO)
            sickbeard.versionCheckScheduler.silent = False
            sickbeard.versionCheckScheduler.enable = True
            sickbeard.versionCheckScheduler.forceRun()
    else:
        sickbeard.versionCheckScheduler.enable = False
        sickbeard.versionCheckScheduler.silent = True
        logger.log("Stopping VERSIONCHECK thread", logger.INFO)

    return True


def change_download_propers(download_propers):
    """
    Enable/Disable proper download thread

    :param download_propers: New desired state
    """
    download_propers = checkbox_to_value(download_propers)

    if sickbeard.DOWNLOAD_PROPERS == download_propers:
        return True

    sickbeard.DOWNLOAD_PROPERS = download_propers
    if sickbeard.DOWNLOAD_PROPERS:
        if not sickbeard.properFinderScheduler.enable:
            logger.log("Starting PROPERFINDER thread", logger.INFO)
            sickbeard.properFinderScheduler.silent = False
            sickbeard.properFinderScheduler.enable = True
    else:
        sickbeard.properFinderScheduler.enable = False
        sickbeard.properFinderScheduler.silent = True
        logger.log("Stopping PROPERFINDER thread", logger.INFO)

    return True


def change_use_trakt(use_trakt):
    """
    Enable/disable trakt thread

    :param use_trakt: New desired state
    """
    use_trakt = checkbox_to_value(use_trakt)

    if sickbeard.USE_TRAKT == use_trakt:
        return True

    sickbeard.USE_TRAKT = use_trakt
    if sickbeard.USE_TRAKT:
        if not sickbeard.traktCheckerScheduler.enable:
            logger.log("Starting TRAKTCHECKER thread", logger.INFO)
            sickbeard.traktCheckerScheduler.silent = False
            sickbeard.traktCheckerScheduler.enable = True
    else:
        sickbeard.traktCheckerScheduler.enable = False
        sickbeard.traktCheckerScheduler.silent = True
        logger.log("Stopping TRAKTCHECKER thread", logger.INFO)

    return True


def change_use_subtitles(use_subtitles):
    """
    Enable/Disable subtitle searcher

    :param use_subtitles: New desired state
    """
    use_subtitles = checkbox_to_value(use_subtitles)

    if sickbeard.USE_SUBTITLES == use_subtitles:
        return True

    sickbeard.USE_SUBTITLES = use_subtitles
    if sickbeard.USE_SUBTITLES:
        if not sickbeard.subtitlesFinderScheduler.enable:
            logger.log("Starting SUBTITLESFINDER thread", logger.INFO)
            sickbeard.subtitlesFinderScheduler.silent = False
            sickbeard.subtitlesFinderScheduler.enable = True
    else:
        sickbeard.subtitlesFinderScheduler.enable = False
        sickbeard.subtitlesFinderScheduler.silent = True
        logger.log("Stopping SUBTITLESFINDER thread", logger.DEBUG)

    return True


def change_process_automatically(process_automatically):
    """
    Enable/Disable postprocessor thread

    :param process_automatically: New desired state
    """
    process_automatically = checkbox_to_value(process_automatically)

    if sickbeard.PROCESS_AUTOMATICALLY == process_automatically:
        return True

    sickbeard.PROCESS_AUTOMATICALLY = process_automatically
    if sickbeard.PROCESS_AUTOMATICALLY:
        if not sickbeard.autoPostProcessorScheduler.enable:
            logger.log("Starting POSTPROCESSOR thread", logger.INFO)
            sickbeard.autoPostProcessorScheduler.silent = False
            sickbeard.autoPostProcessorScheduler.enable = True
    else:
        logger.log("Stopping POSTPROCESSOR thread", logger.INFO)
        sickbeard.autoPostProcessorScheduler.enable = False
        sickbeard.autoPostProcessorScheduler.silent = True

    return True


def check_section(cfg, sec):
    """ Check if INI section exists, if not create it """

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
    if isinstance(option, six.string_types):
        option = six.text_type(option).strip().lower()

    if option in (True, 'on', 'true', value_on) or try_int(option) > 0:
        return value_on

    return value_off


def clean_host(host, default_port=None):
    """
    Returns host or host:port or empty string from a given url or host
    If no port is found and default_port is given use host:default_port
    """

    host = host.strip()

    if host:

        match_host_port = re.search(r'(?:http.*://)?(?P<host>[^:/]+).?(?P<port>[0-9]*).*', host)

        cleaned_host = match_host_port.group('host')
        cleaned_port = match_host_port.group('port')

        if cleaned_host:

            if cleaned_port:
                host = cleaned_host + ':' + cleaned_port

            elif default_port:
                host = cleaned_host + ':' + six.text_type(default_port)

            else:
                host = cleaned_host

        else:
            host = ''

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

    cleaned_hosts = ",".join(cleaned_hosts) if cleaned_hosts else ''

    return cleaned_hosts


def clean_url(url):
    """
    Returns an cleaned url starting with a scheme and folder with trailing /
    or an empty string
    """

    if url and url.strip():

        url = url.strip()

        if '://' not in url:
            url = '//' + url

        scheme, netloc, path, query, fragment = parse.urlsplit(url, 'http')

        if not path:
            path += '/'

        cleaned_url = parse.urlunsplit((scheme, netloc, path, query, fragment))

    else:
        cleaned_url = ''

    return cleaned_url


################################################################################
# min_max                                                                      #
################################################################################
def min_max(val, default, low, high):
    """ Return value forced within range """

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
        logger.log(
            "{dom}:{key} default value is not the correct type. Expected {t}, got {dt}".format(
                dom=cfg_name, key=item_name, t='int', dt=type(def_val)), logger.ERROR)

    if not (min_val is None or isinstance(min_val, int)):
        logger.log(
            "{dom}:{key} min_val value is not the correct type. Expected {t}, got {dt}".format(
                dom=cfg_name, key=item_name, t='int', dt=type(min_val)), logger.ERROR)

    if not (max_val is None or isinstance(max_val, int)):
        logger.log(
            "{dom}:{key} max_val value is not the correct type. Expected {t}, got {dt}".format(
                dom=cfg_name, key=item_name, t='int', dt=type(max_val)), logger.ERROR)

    try:
        if not (check_section(config, cfg_name) and check_section(config[cfg_name], item_name)):
            raise ValueError

        my_val = config[cfg_name][item_name]

        if six.text_type(my_val).lower() == "true":
            my_val = 1
        elif six.text_type(my_val).lower() == "false":
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
        logger.log(item_name + " -> " + six.text_type(my_val), logger.DEBUG)

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
        logger.log(
            "{dom}:{key} default value is not the correct type. Expected {t}, got {dt}".format(
                dom=cfg_name, key=item_name, t='float', dt=type(def_val)), logger.ERROR)

    if not (min_val is None or isinstance(min_val, float)):
        logger.log(
            "{dom}:{key} min_val value is not the correct type. Expected {t}, got {dt}".format(
                dom=cfg_name, key=item_name, t='float', dt=type(min_val)), logger.ERROR)

    if not (max_val is None or isinstance(max_val, float)):
        logger.log(
            "{dom}:{key} max_val value is not the correct type. Expected {t}, got {dt}".format(
                dom=cfg_name, key=item_name, t='float', dt=type(max_val)), logger.ERROR)

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
        logger.log(item_name + " -> " + six.text_type(my_val), logger.DEBUG)

    return my_val


################################################################################
# check_setting_str                                                            #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val=six.text_type(''), silent=True, censor_log=False):
    """
    Checks config setting of string types

    :param config: config object
    :type config: ConfigObj()
    :param cfg_name: section name of config
    :param item_name: item name of section
    :param def_val: default value to return in case a value can't be retrieved from config
                    or if couldn't be converted (default: empty six.text_type)
    :param silent: don't log result to debug log (default: True)
    :param censor_log: overrides and adds this setting to logger censored items (default: False)

    :return: decrypted value of `config[cfg_name][item_name]`
             or `def_val` (see cases of def_val)
    :rtype: six.text_type
    """
    if not isinstance(def_val, six.string_types):
        logger.log(
            "{dom}:{key} default value is not the correct type. Expected {t}, got {dt}".format(
                dom=cfg_name, key=item_name, t='string', dt=type(def_val)), logger.ERROR)

    # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
    encryption_version = (0, sickbeard.ENCRYPTION_VERSION)['password' in item_name]

    try:
        if not (check_section(config, cfg_name) and item_name in config[cfg_name]):
            raise ValueError

        my_val = helpers.decrypt(config[cfg_name][item_name], encryption_version)
        if six.text_type(my_val) == six.text_type(None) or not six.text_type(my_val):
            raise ValueError
    except (ValueError, IndexError, KeyError):
        my_val = def_val

        if cfg_name not in config:
            config[cfg_name] = {}

        config[cfg_name][item_name] = helpers.encrypt(my_val, encryption_version)

    if (censor_log or (cfg_name, item_name) in six.iteritems(logger.censored_items)) and not item_name.endswith('custom_url'):
        logger.censored_items[cfg_name, item_name] = my_val

    if not silent:
        logger.log(item_name + " -> " + my_val, logger.DEBUG)

    return six.text_type(my_val)


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
            logger.log(
                "{dom}:{key} default value is not the correct type. Expected {t}, got {dt}".format(
                    dom=cfg_name, key=item_name, t='bool', dt=type(def_val)), logger.ERROR)

        if not (check_section(config, cfg_name) and item_name in config[cfg_name]):
            raise ValueError

        my_val = config[cfg_name][item_name]
        my_val = six.text_type(my_val)
        if my_val == six.text_type(None) or not my_val:
            raise ValueError

        my_val = checkbox_to_value(my_val)
    except (KeyError, IndexError, ValueError):
        my_val = bool(def_val)

        if cfg_name not in config:
            config[cfg_name] = {}

        config[cfg_name][item_name] = my_val

    if not silent:
        logger.log(item_name + " -> " + six.text_type(my_val), logger.DEBUG)

    return my_val


class ConfigMigrator(object):
    def __init__(self, config_obj):
        """
        Initializes a config migrator that can take the config from the version indicated in the config
        file up to the version required by SB
        """

        self.config_obj = config_obj

        # check the version of the config
        self.config_version = check_setting_int(config_obj, 'General', 'config_version', sickbeard.CONFIG_VERSION)
        self.expected_config_version = sickbeard.CONFIG_VERSION
        self.migration_names = {
            1: 'Custom naming',
            2: 'Sync backup number with version number',
            3: 'Rename omgwtfnzb variables',
            4: 'Add newznab catIDs',
            5: 'Metadata update',
            6: 'Convert from XBMC to new KODI variables',
            7: 'Use version 2 for password encryption',
            8: 'Convert Plex setting keys',
            9: 'Rename autopostprocesser (typo) to autopostprocessor',
            10: 'Refactor flatten_folders_default to season_folders_default'
        }

    def migrate_config(self):
        """
        Calls each successive migration until the config is the same version as SB expects
        """

        if self.config_version > self.expected_config_version:
            logger.log_error_and_exit(
                """Your config version ({0:d}) has been incremented past what this version of SickRage supports ({1:d}).
                If you have used other forks or a newer version of SickRage, your config file may be unusable due to their modifications.""".format(
                    self.config_version, self.expected_config_version
                )
            )

        sickbeard.CONFIG_VERSION = self.config_version

        while self.config_version < self.expected_config_version:
            next_version = self.config_version + 1

            if next_version in self.migration_names:
                migration_name = ': ' + self.migration_names[next_version]
            else:
                migration_name = ''

            logger.log("Backing up config before upgrade")
            if not helpers.backupVersionedFile(sickbeard.CONFIG_FILE, self.config_version):
                logger.log_error_and_exit("Config backup failed, abort upgrading config")
            else:
                logger.log("Proceeding with upgrade")

            # do the migration, expect a method named _migrate_v<num>
            logger.log("Migrating config up to version " + six.text_type(next_version) + migration_name)
            getattr(self, '_migrate_v' + six.text_type(next_version))()
            self.config_version = next_version

            # save new config after migration
            sickbeard.CONFIG_VERSION = self.config_version
            logger.log("Saving config file to disk")
            sickbeard.save_config()

    # Migration v1: Custom naming
    def _migrate_v1(self):
        """
        Reads in the old naming settings from your config and generates a new config template from them.
        """

        sickbeard.NAMING_PATTERN = self._name_to_pattern()
        logger.log("Based on your old settings I'm setting your new naming pattern to: " + sickbeard.NAMING_PATTERN)

        sickbeard.NAMING_CUSTOM_ABD = check_setting_bool(self.config_obj, 'General', 'naming_dates')

        if sickbeard.NAMING_CUSTOM_ABD:
            sickbeard.NAMING_ABD_PATTERN = self._name_to_pattern(True)
            logger.log("Adding a custom air-by-date naming pattern to your config: " + sickbeard.NAMING_ABD_PATTERN)
        else:
            sickbeard.NAMING_ABD_PATTERN = naming.name_abd_presets[0]

        sickbeard.NAMING_MULTI_EP = int(check_setting_int(self.config_obj, 'General', 'naming_multi_ep_type', 1))

        # see if any of their shows used season folders
        main_db_con = db.DBConnection()
        season_folder_shows = main_db_con.select("SELECT indexer_id FROM tv_shows WHERE flatten_folders = 0 LIMIT 1")

        # if any shows had season folders on then prepend season folder to the pattern
        if season_folder_shows:

            old_season_format = check_setting_str(self.config_obj, 'General', 'season_folders_format', 'Season %02d')

            if old_season_format:
                try:
                    new_season_format = old_season_format % 9
                    new_season_format = six.text_type(new_season_format).replace('09', '%0S')
                    new_season_format = new_season_format.replace('9', '%S')

                    logger.log(
                        "Changed season folder format from " + old_season_format + " to " + new_season_format + ", prepending it to your naming config")
                    sickbeard.NAMING_PATTERN = new_season_format + os.sep + sickbeard.NAMING_PATTERN

                except (TypeError, ValueError):
                    logger.log("Can't change " + old_season_format + " to new season format", logger.ERROR)

        # if no shows had it on then don't flatten any shows and don't put season folders in the config
        else:

            logger.log("No shows were using season folders before so I'm disabling flattening on all shows")

            # don't flatten any shows at all
            main_db_con.action("UPDATE tv_shows SET flatten_folders = 0")

        sickbeard.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()

    def _name_to_pattern(self, abd=False):

        # get the old settings from the file
        use_periods = check_setting_bool(self.config_obj, 'General', 'naming_use_periods')
        ep_type = check_setting_int(self.config_obj, 'General', 'naming_ep_type')
        sep_type = check_setting_int(self.config_obj, 'General', 'naming_sep_type')
        use_quality = check_setting_bool(self.config_obj, 'General', 'naming_quality')

        use_show_name = check_setting_bool(self.config_obj, 'General', 'naming_show_name', True)
        use_ep_name = check_setting_bool(self.config_obj, 'General', 'naming_ep_name', True)

        # make the presets into templates
        _naming_ep_type = (
            "%Sx%0E",
            "s%0Se%0E",
            "S%0SE%0E",
            "%0Sx%0E"
        )

        # set up our data to use
        if use_periods:
            show_name = '%S.N'
            ep_name = '%E.N'
            ep_quality = '%Q.N'
            abd_string = '%A.D'
        else:
            show_name = '%SN'
            ep_name = '%EN'
            ep_quality = '%QN'
            abd_string = '%A-D'

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
        sickbeard.OMGWTFNZBS_USERNAME = check_setting_str(self.config_obj, 'omgwtfnzbs', 'omgwtfnzbs_uid')
        sickbeard.OMGWTFNZBS_APIKEY = check_setting_str(self.config_obj, 'omgwtfnzbs', 'omgwtfnzbs_key')

    # Migration v4: Add default newznab catIDs
    def _migrate_v4(self):
        """ Update newznab providers so that the category IDs can be set independently via the config """

        new_newznab_data = []
        old_newznab_data = check_setting_str(self.config_obj, 'Newznab', 'newznab_data')

        if old_newznab_data:
            old_newznab_data_list = old_newznab_data.split("!!!")

            for cur_provider_data in old_newznab_data_list:
                try:
                    name, url, key, enabled = cur_provider_data.split("|")
                except ValueError:
                    logger.log("Skipping Newznab provider string: '" + cur_provider_data + "', incorrect format",
                               logger.ERROR)
                    continue

                if name == 'Sick Beard Index':
                    key = '0'

                if name == 'NZBs.org':
                    catIDs = '5030,5040,5060,5070,5090'
                else:
                    catIDs = '5030,5040,5060'

                cur_provider_data_list = [name, url, key, catIDs, enabled]
                new_newznab_data.append("|".join(cur_provider_data_list))

            sickbeard.NEWZNAB_DATA = "!!!".join(new_newznab_data)

    # Migration v5: Metadata upgrade
    def _migrate_v5(self):
        """ Updates metadata values to the new format """

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

        metadata_xbmc = check_setting_str(self.config_obj, 'General', 'metadata_xbmc', '0|0|0|0|0|0')
        metadata_xbmc_12plus = check_setting_str(self.config_obj, 'General', 'metadata_xbmc_12plus', '0|0|0|0|0|0')
        metadata_mediabrowser = check_setting_str(self.config_obj, 'General', 'metadata_mediabrowser', '0|0|0|0|0|0')
        metadata_ps3 = check_setting_str(self.config_obj, 'General', 'metadata_ps3', '0|0|0|0|0|0')
        metadata_wdtv = check_setting_str(self.config_obj, 'General', 'metadata_wdtv', '0|0|0|0|0|0')
        metadata_tivo = check_setting_str(self.config_obj, 'General', 'metadata_tivo', '0|0|0|0|0|0')
        metadata_mede8er = check_setting_str(self.config_obj, 'General', 'metadata_mede8er', '0|0|0|0|0|0')

        use_banner = check_setting_bool(self.config_obj, 'General', 'use_banner')

        def _migrate_metadata(metadata, metadata_name, _use_banner):
            cur_metadata = metadata.split('|')
            # if target has the old number of values, do upgrade
            if len(cur_metadata) == 6:
                logger.log("Upgrading " + metadata_name + " metadata, old value: " + metadata)
                cur_metadata.insert(4, '0')
                cur_metadata.append('0')
                cur_metadata.append('0')
                cur_metadata.append('0')
                # swap show fanart, show poster
                cur_metadata[3], cur_metadata[2] = cur_metadata[2], cur_metadata[3]
                # if user was using _use_banner to override the poster, instead enable the banner option and deactivate poster
                if metadata_name == 'XBMC' and _use_banner:
                    cur_metadata[4], cur_metadata[3] = cur_metadata[3], '0'
                # write new format
                metadata = '|'.join(cur_metadata)
                logger.log("Upgrading " + metadata_name + " metadata, new value: " + metadata)

            elif len(cur_metadata) == 10:

                metadata = '|'.join(cur_metadata)
                logger.log("Keeping " + metadata_name + " metadata, value: " + metadata)

            else:
                logger.log("Skipping " + metadata_name + " metadata: '" + metadata + "', incorrect format",
                           logger.ERROR)
                metadata = '0|0|0|0|0|0|0|0|0|0'
                logger.log("Setting " + metadata_name + " metadata, new value: " + metadata)

            return metadata

        sickbeard.METADATA_XBMC = _migrate_metadata(metadata_xbmc, 'XBMC', use_banner)
        sickbeard.METADATA_XBMC_12PLUS = _migrate_metadata(metadata_xbmc_12plus, 'XBMC 12+', use_banner)
        sickbeard.METADATA_MEDIABROWSER = _migrate_metadata(metadata_mediabrowser, 'MediaBrowser', use_banner)
        sickbeard.METADATA_PS3 = _migrate_metadata(metadata_ps3, 'PS3', use_banner)
        sickbeard.METADATA_WDTV = _migrate_metadata(metadata_wdtv, 'WDTV', use_banner)
        sickbeard.METADATA_TIVO = _migrate_metadata(metadata_tivo, 'TIVO', use_banner)
        sickbeard.METADATA_MEDE8ER = _migrate_metadata(metadata_mede8er, 'Mede8er', use_banner)

    # Migration v6: Convert from XBMC to KODI variables
    def _migrate_v6(self):
        sickbeard.USE_KODI = check_setting_bool(self.config_obj, 'XBMC', 'use_xbmc')
        sickbeard.KODI_ALWAYS_ON = check_setting_bool(self.config_obj, 'XBMC', 'xbmc_always_on', True)
        sickbeard.KODI_NOTIFY_ONSNATCH = check_setting_bool(self.config_obj, 'XBMC', 'xbmc_notify_onsnatch')
        sickbeard.KODI_NOTIFY_ONDOWNLOAD = check_setting_bool(self.config_obj, 'XBMC', 'xbmc_notify_ondownload')
        sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(self.config_obj, 'XBMC', 'xbmc_notify_onsubtitledownload')
        sickbeard.KODI_UPDATE_LIBRARY = check_setting_bool(self.config_obj, 'XBMC', 'xbmc_update_library')
        sickbeard.KODI_UPDATE_FULL = check_setting_bool(self.config_obj, 'XBMC', 'xbmc_update_full')
        sickbeard.KODI_UPDATE_ONLYFIRST = check_setting_bool(self.config_obj, 'XBMC', 'xbmc_update_onlyfirst')
        sickbeard.KODI_HOST = check_setting_str(self.config_obj, 'XBMC', 'xbmc_host')
        sickbeard.KODI_USERNAME = check_setting_str(self.config_obj, 'XBMC', 'xbmc_username', censor_log=True)
        sickbeard.KODI_PASSWORD = check_setting_str(self.config_obj, 'XBMC', 'xbmc_password', censor_log=True)
        sickbeard.METADATA_KODI = check_setting_str(self.config_obj, 'General', 'metadata_xbmc', '0|0|0|0|0|0|0|0|0|0')
        sickbeard.METADATA_KODI_12PLUS = check_setting_str(self.config_obj, 'General', 'metadata_xbmc_12plus', '0|0|0|0|0|0|0|0|0|0')

    # Migration v7: Use version 2 for password encryption
    @staticmethod
    def _migrate_v7():
        sickbeard.ENCRYPTION_VERSION = 2

    # Migration v8: Rename plex settings
    def _migrate_v8(self):
        sickbeard.PLEX_CLIENT_HOST = check_setting_str(self.config_obj, 'Plex', 'plex_host')
        sickbeard.PLEX_SERVER_USERNAME = check_setting_str(self.config_obj, 'Plex', 'plex_username', censor_log=True)
        sickbeard.PLEX_SERVER_PASSWORD = check_setting_str(self.config_obj, 'Plex', 'plex_password', censor_log=True)
        sickbeard.USE_PLEX_SERVER = check_setting_bool(self.config_obj, 'Plex', 'use_plex')

    # Migration v9: Rename autopostprocesser (typo) to autopostprocessor
    def _migrate_v9(self):
        sickbeard.AUTOPOSTPROCESSOR_FREQUENCY = check_setting_str(self.config_obj, 'General', 'autopostprocesser_frequency')

    # Migration v10: Change flatten_folders_default to season_folders_default (inverted)
    def _migrate_v10(self):
        sickbeard.SEASON_FOLDERS_DEFAULT = not check_setting_str(self.config_obj, 'General', 'flatten_folders_default')
