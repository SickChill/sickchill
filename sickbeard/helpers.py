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
# but WITHOUT ANY WARRANTY; without even the implied warranty    of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.
# pylint:disable=too-many-lines

from __future__ import print_function, unicode_literals

import ast
import base64
import ctypes
import datetime
import hashlib
import io
import operator
import os
import platform
import random
import rarfile
import re
import shutil
import socket
import ssl
import stat
import time
import traceback
import uuid
import xml.etree.ElementTree as ElementTree
import zipfile
from contextlib import closing
from itertools import cycle, izip

import adba
import certifi
import cfscrape
import requests
from cachecontrol import CacheControl
from requests.utils import urlparse
from requests.compat import urljoin
import six

# noinspection PyUnresolvedReferences
from six.moves import urllib

import sickbeard
from sickbeard import classes, db, logger
from sickbeard.common import USER_AGENT
from sickrage.helper import MEDIA_EXTENSIONS, SUBTITLE_EXTENSIONS, episode_num, pretty_file_size
from sickrage.helper.encoding import ek
from sickrage.show.Show import Show


# pylint: disable=protected-access
# Access to a protected member of a client class
urllib._urlopener = classes.SickBeardURLopener()
orig_getaddrinfo = socket.getaddrinfo


# Patches getaddrinfo so that resolving domains like thetvdb do not return ip6 addresses that no longer work on thetvdb.
# This will not effect SickRage itself from being accessed through ip6
def getaddrinfo_wrapper(host, port, family=socket.AF_INET, socktype=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, family, socktype, proto, flags)


if socket.getaddrinfo.__module__ in ('socket', '_socket'):
    logger.log("Patching socket to IPv4 only", logger.DEBUG)
    socket.getaddrinfo = getaddrinfo_wrapper

# Override original shutil function to increase its speed by increasing its buffer to 10MB (optimal)
copyfileobj_orig = shutil.copyfileobj

def _copyfileobj(fsrc, fdst, length=10485760):
    """ Run shutil.copyfileobj with a bigger buffer """
    return copyfileobj_orig(fsrc, fdst, length)
shutil.copyfileobj = _copyfileobj


def indentXML(elem, level=0):
    """
    Does our pretty printing, makes Matt very happy
    """
    i = "\n" + level * "  "
    if elem:
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indentXML(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def remove_non_release_groups(name):
    """
    Remove non release groups from name
    """
    if not name:
        return name

    # Do not remove all [....] suffixes, or it will break anime releases ## Need to verify this is true now
    # Check your database for funky release_names and add them here, to improve failed handling, archiving, and history.
    # select release_name from tv_episodes WHERE LENGTH(release_name);
    # [eSc], [SSG], [GWC] are valid release groups for non-anime
    removeWordsList = {
        r'\[rartv\]$': 'searchre',
        r'\[rarbg\]$': 'searchre',
        r'\.\[eztv\]$': 'searchre',
        r'\[eztv\]$': 'searchre',
        r'\[ettv\]$': 'searchre',
        r'\[cttv\]$': 'searchre',
        r'\.\[vtv\]$': 'searchre',
        r'\[vtv\]$': 'searchre',
        r'\[EtHD\]$': 'searchre',
        r'\[GloDLS\]$': 'searchre',
        r'\[silv4\]$': 'searchre',
        r'\[Seedbox\]$': 'searchre',
        r'\[PublicHD\]$': 'searchre',
        r'\.\[PublicHD\]$': 'searchre',
        r'\.\[NO.RAR\]$': 'searchre',
        r'\[NO.RAR\]$': 'searchre',
        r'-\=\{SPARROW\}\=-$': 'searchre',
        r'\=\{SPARR$': 'searchre',
        r'\.\[720P\]\[HEVC\]$': 'searchre',
        r'\[AndroidTwoU\]$': 'searchre',
        r'\[brassetv\]$': 'searchre',
        r'\[Talamasca32\]$': 'searchre',
        r'\(musicbolt\.com\)$': 'searchre',
        r'\.\(NLsub\)$': 'searchre',
        r'\(NLsub\)$': 'searchre',
        r'\.\[BT\]$': 'searchre',
        r' \[1044\]$': 'searchre',
        r'\.RiPSaLoT$': 'searchre',
        r'\.GiuseppeTnT$': 'searchre',
        r'\.Renc$': 'searchre',
        r'\.gz$': 'searchre',
        r'\.English$': 'searchre',
        r'\.German$': 'searchre',
        r'\.\.Italian$': 'searchre',
        r'\.Italian$': 'searchre',
        r'(?<![57])\.1$': 'searchre',
        r'-NZBGEEK$': 'searchre',
        r'-Siklopentan$': 'searchre',
        r'-Chamele0n$': 'searchre',
        r'-Obfuscated$': 'searchre',
        r'-BUYMORE$': 'searchre',
        r'-\[SpastikusTV\]$': 'searchre',
        r'-RP$': 'searchre',
        r'-20-40$': 'searchre',
        r'\.\[www\.usabit\.com\]$': 'searchre',
        r'^\[www\.Cpasbien\.pe\] ': 'searchre',
        r'^\[www\.Cpasbien\.com\] ': 'searchre',
        r'^\[ www\.Cpasbien\.pw \] ': 'searchre',
        r'^\.www\.Cpasbien\.pw': 'searchre',
        r'^\[www\.newpct1\.com\]': 'searchre',
        r'^\[ www\.Cpasbien\.com \] ': 'searchre',
        r'- \{ www\.SceneTime\.com \}$': 'searchre',
        r'^\{ www\.SceneTime\.com \} - ': 'searchre',
        r'^\]\.\[www\.tensiontorrent.com\] - ': 'searchre',
        r'^\]\.\[ www\.tensiontorrent.com \] - ': 'searchre',
        r'- \[ www\.torrentday\.com \]$': 'searchre',
        r'^\[ www\.TorrentDay\.com \] - ': 'searchre',
        r'\[NO-RAR\] - \[ www\.torrentday\.com \]$': 'searchre',
        r'^www\.Torrenting\.com\.-\.': 'searchre',
        r'-Scrambled$': 'searchre'
    }

    _name = name
    for remove_string, remove_type in six.iteritems(removeWordsList):
        if remove_type == 'search':
            _name = _name.replace(remove_string, '')
        elif remove_type == 'searchre':
            _name = re.sub(r'(?i)' + remove_string, '', _name)

    return _name


def is_media_file(filename):
    """
    Check if named file may contain media

    :param filename: Filename to check
    :return: True if this is a known media file, False if not
    """

    # ignore samples
    try:
        assert isinstance(filename, six.string_types), type(filename)
        is_rar = is_rar_file(filename)
        filename = ek(os.path.basename, filename)

        if re.search(r'(^|[\W_])(?<!shomin.)(sample\d*)[\W_]', filename, re.I):
            return False

        # ignore RARBG release intro
        if re.search(r'^RARBG\.(\w+\.)?(mp4|avi|txt)$', filename, re.I):
            return False

        # ignore MAC OS's retarded "resource fork" files
        if filename.startswith('._'):
            return False

        filname_parts = filename.rpartition(".")

        if re.search('extras?$', filname_parts[0], re.I):
            return False

        return filname_parts[-1].lower() in MEDIA_EXTENSIONS or (sickbeard.UNPACK == 2 and is_rar)
    except (TypeError, AssertionError) as error:  # Not a string
        logger.log('Invalid filename. Filename must be a string. {0}'.format(error), logger.DEBUG)  # pylint: disable=no-member
        return False


def is_rar_file(filename):
    """
    Check if file is a RAR file, or part of a RAR set

    :param filename: Filename to check
    :return: True if this is RAR/Part file, False if not
    """
    archive_regex = r'(?P<file>^(?P<base>(?:(?!\.part\d+\.rar$).)*)\.(?:(?:part0*1\.)?rar)$)'
    ret = re.search(archive_regex, filename) is not None
    try:
        if ret and ek(os.path.exists, filename) and ek(os.path.isfile, filename):
            ret = ek(rarfile.is_rarfile, filename)
    except (IOError, OSError):
        pass

    return ret


def remove_file_failed(failed_file):
    """
    Remove file from filesystem

    :param file: File to remove
    """

    try:
        ek(os.remove, failed_file)
    except Exception:
        pass


def makeDir(path):
    """
    Make a directory on the filesystem

    :param path: directory to make
    :return: True if success, False if failure
    """

    if not ek(os.path.isdir, path):
        try:
            ek(os.makedirs, path)
            # do the library update for synoindex
            sickbeard.notifiers.synoindex_notifier.addFolder(path)
        except OSError:
            return False
    return True


def searchIndexerForShowID(regShowName, indexer=None, indexer_id=None, ui=None):
    """
    Contacts indexer to check for information on shows by showid

    :param regShowName: Name of show
    :param indexer: Which indexer to use
    :param indexer_id: Which indexer ID to look for
    :param ui: Custom UI for indexer use
    :return:
    """

    showNames = [re.sub('[. -]', ' ', regShowName)]

    # Query Indexers for each search term and build the list of results
    for i in sickbeard.indexerApi().indexers if not indexer else int(indexer or []):
        # Query Indexers for each search term and build the list of results
        lINDEXER_API_PARMS = sickbeard.indexerApi(i).api_params.copy()
        if ui is not None:
            lINDEXER_API_PARMS['custom_ui'] = ui
        t = sickbeard.indexerApi(i).indexer(**lINDEXER_API_PARMS)

        for name in showNames:
            logger.log("Trying to find " + name + " on " + sickbeard.indexerApi(i).name, logger.DEBUG)

            try:
                search = t[indexer_id] if indexer_id else t[name]
            except Exception:
                continue

            try:
                seriesname = search[0][b'seriesname']
            except Exception:
                seriesname = None

            try:
                series_id = search[0][b'id']
            except Exception:
                series_id = None

            if not (seriesname and series_id):
                continue
            ShowObj = Show.find(sickbeard.showList, int(series_id))
            # Check if we can find the show in our list (if not, it's not the right show)
            if (indexer_id is None) and (ShowObj is not None) and (ShowObj.indexerid == int(series_id)):
                return seriesname, i, int(series_id)
            elif (indexer_id is not None) and (int(indexer_id) == int(series_id)):
                return seriesname, i, int(indexer_id)

        if indexer:
            break

    return None, None, None


def list_media_files(path):
    """
    Get a list of files possibly containing media in a path

    :param path: Path to check for files
    :return: list of files
    """

    if not dir or not ek(os.path.isdir, path):
        return []

    files = []
    for entry in ek(os.listdir, path):
        full_entry = ek(os.path.join, path, entry)

        # if it's a folder do it recursively
        if ek(os.path.isdir, full_entry) and not entry.startswith('.') and not entry == 'Extras':
            files += list_media_files(full_entry)

        elif is_media_file(entry):
            files.append(full_entry)

    return files


def copyFile(srcFile, destFile):
    """
    Copy a file from source to destination

    :param srcFile: Path of source file
    :param destFile: Path of destination file
    """

    try:
        from shutil import SpecialFileError, Error
    except ImportError:
        from shutil import Error
        SpecialFileError = Error

    try:
        ek(shutil.copyfile, srcFile, destFile)
    except (SpecialFileError, Error) as error:
        logger.log('{0}'.format(error), logger.WARNING)
    except Exception as error:
        logger.log('{0}'.format(error), logger.ERROR)
    else:
        try:
            ek(shutil.copymode, srcFile, destFile)
        except OSError:
            pass


def moveFile(srcFile, destFile):
    """
    Move a file from source to destination

    :param srcFile: Path of source file
    :param destFile: Path of destination file
    """

    try:
        ek(shutil.move, srcFile, destFile)
        fixSetGroupID(destFile)
    except OSError:
        copyFile(srcFile, destFile)
        ek(os.unlink, srcFile)


def link(src, dst):
    """
    Create a file link from source to destination.
    TODO: Make this six.text_type proof

    :param src: Source file
    :param dst: Destination file
    """

    if platform.system() == 'Windows':
        if ctypes.windll.kernel32.CreateHardLinkW(ctypes.c_wchar_p(six.text_type(dst)), ctypes.c_wchar_p(six.text_type(src)), None) == 0:
            raise ctypes.WinError()
    else:
        ek(os.link, src, dst)


def hardlinkFile(srcFile, destFile):
    """
    Create a hard-link (inside filesystem link) between source and destination

    :param srcFile: Source file
    :param destFile: Destination file
    """

    try:
        ek(link, srcFile, destFile)
        fixSetGroupID(destFile)
    except Exception as error:
        logger.log("Failed to create hardlink of {0} at {1}. Error: {2}. Copying instead".format
                   (srcFile, destFile, error), logger.WARNING)
        copyFile(srcFile, destFile)


def symlink(src, dst):
    """
    Create a soft/symlink between source and destination

    :param src: Source file
    :param dst: Destination file
    """

    if platform.system() == 'Windows':
        if ctypes.windll.kernel32.CreateSymbolicLinkW(ctypes.c_wchar_p(six.text_type(dst)), ctypes.c_wchar_p(six.text_type(src)), 1 if ek(os.path.isdir, src) else 0) in [0, 1280]:
            raise ctypes.WinError()
    else:
        ek(os.symlink, src, dst)


def moveAndSymlinkFile(srcFile, destFile):
    """
    Move a file from source to destination, then create a symlink back from destination from source. If this fails, copy
    the file from source to destination

    :param srcFile: Source file
    :param destFile: Destination file
    """

    try:
        moveFile(srcFile, destFile)
        symlink(destFile, srcFile)
    except Exception as error:
        logger.log("Failed to create symlink of {0} at {1}. Error: {2}. Copying instead".format
                   (srcFile, destFile, error), logger.WARNING)
        copyFile(srcFile, destFile)


def make_dirs(path):
    """
    Creates any folders that are missing and assigns them the permissions of their
    parents
    """

    logger.log("Checking if the path {0} already exists".format(path), logger.DEBUG)

    if not ek(os.path.isdir, path):
        # Windows, create all missing folders
        if platform.system() == 'Windows':
            try:
                logger.log("Folder {0} didn't exist, creating it".format(path), logger.DEBUG)
                ek(os.makedirs, path)
            except (OSError, IOError) as error:
                logger.log("Failed creating {0} : {1}".format(path, error), logger.ERROR)
                return False

        # not Windows, create all missing folders and set permissions
        else:
            sofar = ''
            folder_list = path.split(os.path.sep)

            # look through each subfolder and make sure they all exist
            for cur_folder in folder_list:
                sofar += cur_folder + os.path.sep

                # if it exists then just keep walking down the line
                if ek(os.path.isdir, sofar):
                    continue

                try:
                    logger.log("Folder {0} didn't exist, creating it".format(sofar), logger.DEBUG)
                    ek(os.mkdir, sofar)
                    # use normpath to remove end separator, otherwise checks permissions against itself
                    chmodAsParent(ek(os.path.normpath, sofar))
                    # do the library update for synoindex
                    sickbeard.notifiers.synoindex_notifier.addFolder(sofar)
                except (OSError, IOError) as error:
                    logger.log("Failed creating {0} : {1}".format(sofar, error), logger.ERROR)
                    return False

    return True


def rename_ep_file(cur_path, new_path, old_path_length=0):
    """
    Creates all folders needed to move a file to its new location, renames it, then cleans up any folders
    left that are now empty.

    :param  cur_path: The absolute path to the file you want to move/rename
    :param new_path: The absolute path to the destination for the file WITHOUT THE EXTENSION
    :param old_path_length: The length of media file path (old name) WITHOUT THE EXTENSION
    """

    # new_dest_dir, new_dest_name = ek(os.path.split, new_path)  # @UnusedVariable

    if old_path_length == 0 or old_path_length > len(cur_path):
        # approach from the right
        cur_file_name, cur_file_ext = ek(os.path.splitext, cur_path)  # @UnusedVariable
    else:
        # approach from the left
        cur_file_ext = cur_path[old_path_length:]
        cur_file_name = cur_path[:old_path_length]

    if cur_file_ext[1:] in SUBTITLE_EXTENSIONS:
        # Extract subtitle language from filename
        sublang = ek(os.path.splitext, cur_file_name)[1][1:]

        # Check if the language extracted from filename is a valid language
        if sublang in sickbeard.subtitles.subtitle_code_filter():
            cur_file_ext = '.' + sublang + cur_file_ext

    # put the extension on the incoming file
    new_path += cur_file_ext

    make_dirs(ek(os.path.dirname, new_path))

    # move the file
    try:
        logger.log("Renaming file from {0} to {1}".format(cur_path, new_path))
        ek(shutil.move, cur_path, new_path)
    except (OSError, IOError) as error:
        logger.log("Failed renaming {0} to {1} : {2}".format(cur_path, new_path, error), logger.ERROR)
        return False

    # clean up any old folders that are empty
    delete_empty_folders(ek(os.path.dirname, cur_path))

    return True


def delete_empty_folders(check_empty_dir, keep_dir=None):
    """
    Walks backwards up the path and deletes any empty folders found.

    :param check_empty_dir: The path to clean (absolute path to a folder)
    :param keep_dir: Clean until this path is reached
    """

    # treat check_empty_dir as empty when it only contains these items
    ignore_items = []

    logger.log("Trying to clean any empty folders under " + check_empty_dir)

    # as long as the folder exists and doesn't contain any files, delete it
    while ek(os.path.isdir, check_empty_dir) and check_empty_dir != keep_dir:
        check_files = ek(os.listdir, check_empty_dir)

        if not check_files or (len(check_files) <= len(ignore_items) and all(
                check_file in ignore_items for check_file in check_files)):
            # directory is empty or contains only ignore_items
            try:
                logger.log("Deleting empty folder: " + check_empty_dir)
                # need shutil.rmtree when ignore_items is really implemented
                ek(os.rmdir, check_empty_dir)
                # do the library update for synoindex
                sickbeard.notifiers.synoindex_notifier.deleteFolder(check_empty_dir)
            except OSError as error:
                logger.log("Unable to delete {0}. Error: {1}".format(check_empty_dir, error), logger.WARNING)
                break
            check_empty_dir = ek(os.path.dirname, check_empty_dir)
        else:
            break


def fileBitFilter(mode):
    """
    Strip special filesystem bits from file

    :param mode: mode to check and strip
    :return: required mode for media file
    """

    for bit in [stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH, stat.S_ISUID, stat.S_ISGID]:
        if mode & bit:
            mode -= bit

    return mode


def chmodAsParent(childPath):
    """
    Retain permissions of parent for childs
    (Does not work for Windows hosts)

    :param childPath: Child Path to change permissions to sync from parent
    """

    if platform.system() == 'Windows':
        return

    parentPath = ek(os.path.dirname, childPath)

    if not parentPath:
        logger.log("No parent path provided in " + childPath + ", unable to get permissions from it", logger.DEBUG)
        return

    childPath = ek(os.path.join, parentPath, ek(os.path.basename, childPath))

    parentPathStat = ek(os.stat, parentPath)
    parentMode = stat.S_IMODE(parentPathStat[stat.ST_MODE])

    childPathStat = ek(os.stat, childPath.encode(sickbeard.SYS_ENCODING))
    childPath_mode = stat.S_IMODE(childPathStat[stat.ST_MODE])

    if ek(os.path.isfile, childPath):
        childMode = fileBitFilter(parentMode)
    else:
        childMode = parentMode

    if childPath_mode == childMode:
        return

    childPath_owner = childPathStat.st_uid  # pylint: disable=no-member
    user_id = os.geteuid()  # @UndefinedVariable - only available on UNIX

    if user_id not in (childPath_owner, 0):
        logger.log("Not running as root or owner of " + childPath + ", not trying to set permissions", logger.DEBUG)
        return

    try:
        ek(os.chmod, childPath, childMode)
    except OSError:
        logger.log("Failed to set permission for {0} to {1:o}, parent directory has {2:o}".format(childPath, childMode, parentMode), logger.DEBUG)


def fixSetGroupID(childPath):
    """
    Inherid SGID from parent
    (does not work on Windows hosts)

    :param childPath: Path to inherit SGID permissions from parent
    """

    if platform.system() == 'Windows':
        return

    parentPath = ek(os.path.dirname, childPath)
    parentStat = ek(os.stat, parentPath)
    parentMode = stat.S_IMODE(parentStat[stat.ST_MODE])

    childPath = ek(os.path.join, parentPath, ek(os.path.basename, childPath))

    if parentMode & stat.S_ISGID:
        parentGID = parentStat[stat.ST_GID]
        childStat = ek(os.stat, childPath.encode(sickbeard.SYS_ENCODING))
        childGID = childStat[stat.ST_GID]

        if childGID == parentGID:
            return

        childPath_owner = childStat.st_uid  # pylint: disable=no-member
        user_id = os.geteuid()  # @UndefinedVariable - only available on UNIX

        if user_id not in (childPath_owner, 0):
            logger.log("Not running as root or owner of " + childPath + ", not trying to set the set-group-ID",
                       logger.DEBUG)
            return

        try:
            ek(os.chown, childPath, -1, parentGID)  # @UndefinedVariable - only available on UNIX
            logger.log("Respecting the set-group-ID bit on the parent directory for {0}".format(childPath), logger.DEBUG)
        except OSError:
            logger.log(
                "Failed to respect the set-group-ID bit on the parent directory for {0} (setting group ID {1})".format(
                    childPath, parentGID), logger.ERROR)


def is_anime_in_show_list():
    """
    Check if any shows in list contain anime

    :return: True if global showlist contains Anime, False if not
    """

    for show in sickbeard.showList:
        if show.is_anime:
            return True
    return False


def update_anime_support():
    """Check if we need to support anime, and if we do, enable the feature"""

    sickbeard.ANIMESUPPORT = is_anime_in_show_list()


def get_absolute_number_from_season_and_episode(show, season, episode):
    """
    Find the absolute number for a show episode

    :param show: Show object
    :param season: Season number
    :param episode: Episode number
    :return: The absolute number
    """

    absolute_number = None

    if season and episode:
        main_db_con = db.DBConnection()
        sql = "SELECT * FROM tv_episodes WHERE showid = ? and season = ? and episode = ?"
        sql_results = main_db_con.select(sql, [show.indexerid, season, episode])

        if len(sql_results) == 1:
            absolute_number = int(sql_results[0][b"absolute_number"])
            logger.log("Found absolute number {absolute} for show {show} {ep}".format
                       (absolute=absolute_number, show=show.name,
                        ep=episode_num(season, episode)), logger.DEBUG)
        else:
            logger.log("No entries for absolute number for show {show} {ep}".format
                       (show=show.name, ep=episode_num(season, episode)), logger.DEBUG)

    return absolute_number


def get_all_episodes_from_absolute_number(show, absolute_numbers, indexer_id=None):
    episodes = []
    season = None

    if len(absolute_numbers):
        if not show and indexer_id:
            show = Show.find(sickbeard.showList, indexer_id)

        for absolute_number in absolute_numbers if show else []:
            ep = show.getEpisode(None, None, absolute_number=absolute_number)
            if ep:
                episodes.append(ep.episode)
                season = ep.season  # this will always take the last found season so eps that cross the season border are not handeled well

    return season, episodes


def sanitizeSceneName(name, anime=False):
    """
    Takes a show name and returns the "scenified" version of it.

    :param anime: Some show have a ' in their name(Kuroko's Basketball) and is needed for search.
    :return: A string containing the scene version of the show name given.
    """

    # assert isinstance(name, unicode), name + ' is not unicode'

    if not name:
        return ''

    bad_chars = ',:()!?\u2019'
    if not anime:
        bad_chars += "'"

    # strip out any bad chars
    for x in bad_chars:
        name = name.replace(x, "")

    # tidy up stuff that doesn't belong in scene names
    name = name.replace("&", "and")
    name = re.sub(r"[- /]+", ".", name)
    name = re.sub(r"[.]+", ".", name)

    if name.endswith('.'):
        name = name[:-1]

    return name


_binOps = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.div,
    ast.Mod: operator.mod
}


def arithmeticEval(s):
    """
    A safe eval supporting basic arithmetic operations.

    :param s: expression to evaluate
    :return: value
    """
    node = ast.parse(s, mode='eval')

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return _binOps[type(node.op)](_eval(node.left), _eval(node.right))
        else:
            raise Exception('Unsupported type {0}'.format(node))

    return _eval(node.body)


def create_https_certificates(ssl_cert, ssl_key):
    """
    Create self-signed HTTPS certificares and store in paths 'ssl_cert' and 'ssl_key'

    :param ssl_cert: Path of SSL certificate file to write
    :param ssl_key: Path of SSL keyfile to write
    :return: True on success, False on failure
    """

    # assert isinstance(ssl_key, unicode)
    # assert isinstance(ssl_cert, unicode)

    try:
        from OpenSSL import crypto  # noinspection PyUnresolvedReferences
        from certgen import createKeyPair, createCertRequest, createCertificate, TYPE_RSA, \
            serial  # @UnresolvedImport
    except Exception:
        logger.log("pyopenssl module missing, please install for https access", logger.WARNING)
        return False

    # Create the CA Certificate
    cakey = createKeyPair(TYPE_RSA, 4096)
    careq = createCertRequest(cakey, CN='Certificate Authority')
    cacert = createCertificate(careq, (careq, cakey), serial, (0, 60 * 60 * 24 * 365 * 10))  # ten years

    cname = 'SickRage'
    pkey = createKeyPair(TYPE_RSA, 4096)
    req = createCertRequest(pkey, CN=cname)
    cert = createCertificate(req, (cacert, cakey), serial, (0, 60 * 60 * 24 * 365 * 10))  # ten years

    # Save the key and certificate to disk
    try:
        # pylint: disable=no-member
        # Module has no member
        io.open(ssl_key, 'wb').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        io.open(ssl_cert, 'wb').write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except Exception:
        logger.log("Error creating SSL key and certificate", logger.ERROR)
        return False

    return True


def backupVersionedFile(old_file, version):
    """
    Back up an old version of a file

    :param old_file: Original file, to take a backup from
    :param version: Version of file to store in backup
    :return: True if success, False if failure
    """

    numTries = 0

    new_file = old_file + '.' + 'v' + str(version)

    while not ek(os.path.isfile, new_file):
        if not ek(os.path.isfile, old_file):
            logger.log("Not creating backup, {0} doesn't exist".format(old_file), logger.DEBUG)
            break

        try:
            logger.log("Trying to back up {0} to {1}".format(old_file, new_file), logger.DEBUG)
            shutil.copy(old_file, new_file)
            logger.log("Backup done", logger.DEBUG)
            break
        except Exception as error:
            logger.log("Error while trying to back up {0} to {1} : {2}".format(old_file, new_file, error), logger.WARNING)
            numTries += 1
            time.sleep(1)
            logger.log("Trying again.", logger.DEBUG)

        if numTries >= 10:
            logger.log("Unable to back up {0} to {1} please do it manually.".format(old_file, new_file), logger.ERROR)
            return False

    return True


def restoreVersionedFile(backup_file, version):
    """
    Restore a file version to original state

    :param backup_file: File to restore
    :param version: Version of file to restore
    :return: True on success, False on failure
    """

    numTries = 0

    new_file, ext_ = ek(os.path.splitext, backup_file)
    restore_file = new_file + '.' + 'v' + str(version)

    if not ek(os.path.isfile, new_file):
        logger.log("Not restoring, {0} doesn't exist".format(new_file), logger.DEBUG)
        return False

    try:
        logger.log("Trying to backup {0} to {1}.r{2} before restoring backup".format
                   (new_file, new_file, version), logger.DEBUG)

        shutil.move(new_file, new_file + '.' + 'r' + str(version))
    except Exception as error:
        logger.log("Error while trying to backup DB file {0} before proceeding with restore: {1}".format
                   (restore_file, error), logger.WARNING)
        return False

    while not ek(os.path.isfile, new_file):
        if not ek(os.path.isfile, restore_file):
            logger.log("Not restoring, {0} doesn't exist".format(restore_file), logger.DEBUG)
            break

        try:
            logger.log("Trying to restore file {0} to {1}".format(restore_file, new_file), logger.DEBUG)
            shutil.copy(restore_file, new_file)
            logger.log("Restore done", logger.DEBUG)
            break
        except Exception as error:
            logger.log("Error while trying to restore file {0}. Error: {1}".format(restore_file, error), logger.WARNING)
            numTries += 1
            time.sleep(1)
            logger.log("Trying again. Attempt #: {0}".format(numTries), logger.DEBUG)

        if numTries >= 10:
            logger.log("Unable to restore file {0} to {1}".format(restore_file, new_file), logger.WARNING)
            return False

    return True


def get_lan_ip():
    """Returns IP of system"""

    try:
        return [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][0]
    except Exception:
        return socket.gethostname()


def check_url(url):
    """
    Check if a URL exists without downloading the whole file.
    We only check the URL header.
    """
    try:
        requests.head(url, verify=False).raise_for_status()
    except Exception as error:
        handle_requests_exception(error)
        return False
    return True


def anon_url(*url):
    """
    Return a URL string consisting of the Anonymous redirect URL and an arbitrary number of values appended.
    """
    return '' if None in url else '{0}{1}'.format(sickbeard.ANON_REDIRECT, ''.join(str(s) for s in url))


"""
Encryption
==========
By Pedro Jose Pereira Vieito <pvieito@gmail.com> (@pvieito)

* If encryption_version==0 then return data without encryption
* The keys should be unique for each device

To add a new encryption_version:
  1) Code your new encryption_version
  2) Update the last encryption_version available in webserve.py
  3) Remember to maintain old encryption versions and key generators for retrocompatibility
"""

# Key Generators
unique_key1 = hex(uuid.getnode() ** 2)  # Used in encryption v1


# Encryption Functions
def encrypt(data, encryption_version=0, _decrypt=False):
    # Version 1: Simple XOR encryption (this is not very secure, but works)
    if encryption_version == 1:
        if _decrypt:
            return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(base64.decodestring(data), cycle(unique_key1)))
        else:
            return base64.encodestring(
                ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(unique_key1)))).strip()
    # Version 2: Simple XOR encryption (this is not very secure, but works)
    elif encryption_version == 2:
        if _decrypt:
            return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(base64.decodestring(data), cycle(sickbeard.ENCRYPTION_SECRET)))
        else:
            return base64.encodestring(
                ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(sickbeard.ENCRYPTION_SECRET)))).strip()
    # Version 0: Plain text
    else:
        return data


def decrypt(data, encryption_version=0):
    return encrypt(data, encryption_version, _decrypt=True)


def full_sanitizeSceneName(name):
    return re.sub('[. -]', ' ', sanitizeSceneName(name)).lower().strip()


def _check_against_names(nameInQuestion, show, season=-1):
    showNames = []
    if season in [-1, 1]:
        showNames = [show.name]

    showNames.extend(sickbeard.scene_exceptions.get_scene_exceptions(show.indexerid, season=season))

    for showName in showNames:
        nameFromList = full_sanitizeSceneName(showName)
        if nameFromList == nameInQuestion:
            return True

    return False


def get_show(name, tryIndexers=False):
    if not sickbeard.showList:
        return

    showObj = None
    fromCache = False

    if not name:
        return showObj

    try:
        # check cache for show
        cache = sickbeard.name_cache.retrieveNameFromCache(name)
        if cache:
            fromCache = True
            showObj = Show.find(sickbeard.showList, int(cache))

        # try indexers
        if not showObj and tryIndexers:
            showObj = Show.find(
                sickbeard.showList, searchIndexerForShowID(full_sanitizeSceneName(name), ui=classes.ShowListUI)[2])

        # try scene exceptions
        if not showObj:
            ShowID = sickbeard.scene_exceptions.get_scene_exception_by_name(name)[0]
            if ShowID:
                showObj = Show.find(sickbeard.showList, int(ShowID))

        # add show to cache
        if showObj and not fromCache:
            sickbeard.name_cache.addNameToCache(name, showObj.indexerid)
    except Exception as error:
        logger.log("Error when attempting to find show: {0} in SickRage. Error: {1} ".format(name, error), logger.DEBUG)

    return showObj


def is_hidden_folder(folder):
    """
    Returns True if folder is hidden.
    On Linux based systems hidden folders start with . (dot)
    :param folder: Full path of folder to check
    """
    def is_hidden(filepath):
        name = ek(os.path.basename, ek(os.path.abspath, filepath))
        return name == '@eaDir' or name.startswith('.') or has_hidden_attribute(filepath)

    def has_hidden_attribute(filepath):
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(ctypes.c_wchar_p(six.text_type(filepath)))
            assert attrs != -1
            result = bool(attrs & 2)
        except (AttributeError, AssertionError, OSError, IOError):
            result = False
        return result

    if ek(os.path.isdir, folder) and is_hidden(folder):
        return True

    return False

def real_path(path):
    """
    Returns: the canonicalized absolute pathname. The resulting path will have no symbolic link, '/./' or '/../' components.
    """
    return ek(os.path.normpath, ek(os.path.normcase, ek(os.path.realpath, path)))

def is_subdirectory(subdir_path, topdir_path):
    """
    Returns true if a subdir_path is a subdirectory of topdir_path
    else otherwise.

    :param subdir_path: The full path to the sub-directory
    :param topdir_path: The full path to the top directory to check subdir_path against
    """
    topdir_path = real_path(topdir_path)
    subdir_path = real_path(subdir_path)

    # checks if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([subdir_path, topdir_path]) == topdir_path


def validateShow(show, season=None, episode=None):
    indexer_lang = show.lang

    try:
        lINDEXER_API_PARMS = sickbeard.indexerApi(show.indexer).api_params.copy()

        lINDEXER_API_PARMS['language'] = indexer_lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

        if show.dvdorder:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = sickbeard.indexerApi(show.indexer).indexer(**lINDEXER_API_PARMS)
        if season is None and episode is None:
            return t

        return t[show.indexerid][season][episode]
    except (sickbeard.indexer_episodenotfound, sickbeard.indexer_seasonnotfound):
        pass


def set_up_anidb_connection():
    """Connect to anidb"""

    if not sickbeard.USE_ANIDB:
        logger.log("Usage of anidb disabled. Skiping", logger.DEBUG)
        return False

    if not sickbeard.ANIDB_USERNAME and not sickbeard.ANIDB_PASSWORD:
        logger.log("anidb username and/or password are not set. Aborting anidb lookup.", logger.DEBUG)
        return False

    if not sickbeard.ADBA_CONNECTION:
        def anidb_logger(msg):
            return logger.log("anidb: {0} ".format(msg), logger.DEBUG)

        try:
            sickbeard.ADBA_CONNECTION = adba.Connection(keepAlive=True, log=anidb_logger)
        except Exception as error:
            logger.log("anidb exception msg: {0} ".format(error), logger.WARNING)
            return False

    try:
        if not sickbeard.ADBA_CONNECTION.authed():
            sickbeard.ADBA_CONNECTION.auth(sickbeard.ANIDB_USERNAME, sickbeard.ANIDB_PASSWORD)
        else:
            return True
    except Exception as error:
        logger.log("anidb exception msg: {0} ".format(error), logger.WARNING)
        return False

    return sickbeard.ADBA_CONNECTION.authed()


def makeZip(fileList, archive):
    """
    Create a ZIP of files

    :param fileList: A list of file names - full path each name
    :param archive: File name for the archive with a full path
    """

    try:
        a = zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
        for f in fileList:
            a.write(f)
        a.close()
        return True
    except Exception as error:
        logger.log("Zip creation error: {0} ".format(error), logger.ERROR)
        return False


def extractZip(archive, targetDir):
    """
    Unzip a file to a directory

    :param archive: The file name of the archive to extract with a full path
    :param targetDir: The full path to the extraction target directory
    """

    try:
        if not ek(os.path.exists, targetDir):
            ek(os.mkdir, targetDir)

        zip_file = zipfile.ZipFile(archive, 'r', allowZip64=True)
        for member in zip_file.namelist():
            filename = ek(os.path.basename, member)
            # skip directories
            if not filename:
                continue

            # copy file (taken from zipfile's extract)
            source = zip_file.open(member)
            target = open(ek(os.path.join, targetDir, filename), "wb")
            shutil.copyfileobj(source, target)
            source.close()
            target.close()
        zip_file.close()
        return True
    except Exception as error:
        logger.log("Zip extraction error: {0} ".format(error), logger.ERROR)
        return False


def backup_config_zip(fileList, archive, arcname=None):
    """
    Store the config file as a ZIP

    :param fileList: List of files to store
    :param archive: ZIP file name
    :param arcname: Archive path
    :return: True on success, False on failure
    """

    try:
        a = zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
        for f in fileList:
            a.write(f, ek(os.path.relpath, f, arcname))
        a.close()
        return True
    except Exception as error:
        logger.log("Zip creation error: {0} ".format(error), logger.ERROR)
        return False


def restore_config_zip(archive, targetDir):
    """
    Restores a Config ZIP file back in place

    :param archive: ZIP filename
    :param targetDir: Directory to restore to
    :return: True on success, False on failure
    """

    try:
        if not ek(os.path.exists, targetDir):
            ek(os.mkdir, targetDir)
        else:
            def path_leaf(path):
                head, tail = ek(os.path.split, path)
                return tail or ek(os.path.basename, head)
            bakFilename = '{0}-{1}'.format(path_leaf(targetDir), datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            shutil.move(targetDir, ek(os.path.join, ek(os.path.dirname, targetDir), bakFilename))

        zip_file = zipfile.ZipFile(archive, 'r', allowZip64=True)
        for member in zip_file.namelist():
            zip_file.extract(member, targetDir)
        zip_file.close()
        return True
    except Exception as error:
        logger.log("Zip extraction error: {0}".format(error), logger.ERROR)
        shutil.rmtree(targetDir)
        return False


def mapIndexersToShow(showObj):
    mapped = {}

    # init mapped indexers object
    for indexer in sickbeard.indexerApi().indexers:
        mapped[indexer] = showObj.indexerid if int(indexer) == int(showObj.indexer) else 0

    main_db_con = db.DBConnection()
    sql_results = main_db_con.select(
        "SELECT * FROM indexer_mapping WHERE indexer_id = ? AND indexer = ?",
        [showObj.indexerid, showObj.indexer])

    # for each mapped entry
    for curResult in sql_results:
        nlist = [i for i in curResult if i is not None]
        # Check if its mapped with both tvdb and tvrage.
        if len(nlist) >= 4:
            logger.log("Found indexer mapping in cache for show: " + showObj.name, logger.DEBUG)
            mapped[int(curResult[b'mindexer'])] = int(curResult[b'mindexer_id'])
            break
    else:
        sql_l = []
        for indexer in sickbeard.indexerApi().indexers:
            if indexer == showObj.indexer:
                mapped[indexer] = showObj.indexerid
                continue

            lINDEXER_API_PARMS = sickbeard.indexerApi(indexer).api_params.copy()
            lINDEXER_API_PARMS['custom_ui'] = classes.ShowListUI
            t = sickbeard.indexerApi(indexer).indexer(**lINDEXER_API_PARMS)

            try:
                mapped_show = t[showObj.name]
            except Exception:
                logger.log("Unable to map " + sickbeard.indexerApi(showObj.indexer).name + "->" + sickbeard.indexerApi(
                    indexer).name + " for show: " + showObj.name + ", skipping it", logger.DEBUG)
                continue

            if mapped_show and len(mapped_show) == 1:
                logger.log("Mapping " + sickbeard.indexerApi(showObj.indexer).name + "->" + sickbeard.indexerApi(
                    indexer).name + " for show: " + showObj.name, logger.DEBUG)

                mapped[indexer] = int(mapped_show[0][b'id'])

                logger.log("Adding indexer mapping to DB for show: " + showObj.name, logger.DEBUG)

                sql_l.append([
                    "INSERT OR IGNORE INTO indexer_mapping (indexer_id, indexer, mindexer_id, mindexer) VALUES (?,?,?,?)",
                    [showObj.indexerid, showObj.indexer, int(mapped_show[0][b'id']), indexer]])

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

    return mapped


def touchFile(fname, atime=None):
    """
    Touch a file (change modification date)

    :param fname: Filename to touch
    :param atime: Specific access time (defaults to None)
    :return: True on success, False on failure
    """

    if atime and fname and ek(os.path.isfile, fname):
        ek(os.utime, fname, (atime, atime))
        return True

    return False


def make_session():
    session = requests.Session()

    session.headers.update({'User-Agent': USER_AGENT, 'Accept-Encoding': 'gzip,deflate'})

    session = cfscrape.create_scraper(sess=session)

    return CacheControl(sess=session, cache_etags=True)


def request_defaults(kwargs):
    hooks = kwargs.pop('hooks', None)
    cookies = kwargs.pop('cookies', None)
    allow_proxy = kwargs.pop('allow_proxy', True)
    verify = certifi.old_where() if all([sickbeard.SSL_VERIFY, kwargs.pop('verify', True)]) else False

    # request session proxies
    if allow_proxy and sickbeard.PROXY_SETTING:
        logger.log("Using global proxy: " + sickbeard.PROXY_SETTING, logger.DEBUG)
        parsed_url = urlparse(sickbeard.PROXY_SETTING)
        address = sickbeard.PROXY_SETTING if parsed_url.scheme else 'http://' + sickbeard.PROXY_SETTING
        proxies = {
            "http": address,
            "https": address,
        }
    else:
        proxies = None

    return hooks, cookies, verify, proxies


def getURL(url, post_data=None, params=None, headers=None,  # pylint:disable=too-many-arguments, too-many-return-statements, too-many-branches, too-many-locals
           timeout=30, session=None, **kwargs):
    """
    Returns data retrieved from the url provider.
    """
    try:
        response_type = kwargs.pop('returns', 'text')
        stream = kwargs.pop('stream', False)

        hooks, cookies, verify, proxies = request_defaults(kwargs)

        # Dict, loop through and change all key,value pairs to bytes
        if isinstance(params, dict):
            for key, value in six.iteritems(params):
                if isinstance(key, six.text_type):
                    del params[key]
                    key = key.encode('utf-8')

                if isinstance(value, six.text_type):
                    value = value.encode('utf-8')
                params[key] = value

        if isinstance(post_data, dict):
            for key, value in six.iteritems(post_data):
                if isinstance(key, six.text_type):
                    del post_data[key]
                    key = key.encode('utf-8')

                if isinstance(value, six.text_type):
                    value = value.encode('utf-8')
                post_data[key] = value

        # List, loop through and change all indexes to bytes
        if isinstance(params, list):
            for index, value in enumerate(params):
                if isinstance(value, six.text_type):
                    params[index] = value.encode('utf-8')

        if isinstance(post_data, list):
            for index, value in enumerate(post_data):
                if isinstance(value, six.text_type):
                    post_data[index] = value.encode('utf-8')

        # Unicode, encode to bytes
        if isinstance(params, six.text_type):
            params = params.encode('utf-8')

        if isinstance(post_data, six.text_type):
            post_data = post_data.encode('utf-8')

        if isinstance(url, six.text_type):
            url = url.encode('utf-8')

        resp = session.request(
            'POST' if post_data else 'GET', url, data=post_data or {}, params=params or {},
            timeout=timeout, allow_redirects=True, hooks=hooks, stream=stream,
            headers=headers, cookies=cookies, proxies=proxies, verify=verify
        )
        resp.raise_for_status()
    except Exception as error:
        handle_requests_exception(error)
        return None

    try:
        return resp if response_type == 'response' or response_type is None else resp.json() if response_type == 'json' else getattr(resp, response_type, resp)
    except ValueError:
        logger.log('Requested a json response but response was not json, check the url: {0}'.format(url), logger.DEBUG)
        return None


def download_file(url, filename, session=None, headers=None, **kwargs):  # pylint:disable=too-many-return-statements
    """
    Downloads a file specified

    :param url: Source URL
    :param filename: Target file on filesystem
    :param session: request session to use
    :param headers: override existing headers in request session
    :return: True on success, False on failure
    """

    try:
        hooks, cookies, verify, proxies = request_defaults(kwargs)

        with closing(session.get(url, allow_redirects=True, stream=True,
                                 verify=verify, headers=headers, cookies=cookies,
                                 hooks=hooks, proxies=proxies)) as resp:

            resp.raise_for_status()

            try:
                with io.open(filename, 'wb') as fp:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            fp.write(chunk)
                            fp.flush()

                chmodAsParent(filename)
            except Exception as error:
                logger.log("Problem downloading file, setting permissions or writing file to \"{0}\" - ERROR: {1}".format(filename, error), logger.WARNING)

    except Exception as error:
        handle_requests_exception(error)
        return False

    return True


def handle_requests_exception(requests_exception):  # pylint: disable=too-many-branches, too-many-statements
    default = "Request failed: {0}"
    try:
        raise requests_exception
    except requests.exceptions.SSLError as error:
        if ssl.OPENSSL_VERSION_INFO < (1, 0, 1, 5):
            logger.log("SSL Error requesting url: '{0}' You have {1}, try upgrading OpenSSL to 1.0.1e+".format(error.request.url, ssl.OPENSSL_VERSION))
        if sickbeard.SSL_VERIFY:
            logger.log("SSL Error requesting url: '{0}' Try disabling Cert Verification on the advanced tab of /config/general")
        logger.log(default.format(error), logger.DEBUG)
        logger.log(traceback.format_exc(), logger.DEBUG)

    except requests.exceptions.HTTPError as error:
        if not (hasattr(error, 'response') and error.response and \
                hasattr(error.response, 'status_code') and error.response.status_code == 404 and \
                hasattr(error.response, 'headers') and error.response.headers.get('X-Content-Type-Options') == 'nosniff'):
            logger.log(default.format(error))
    except requests.exceptions.TooManyRedirects as error:
        logger.log(default.format(error))
    except requests.exceptions.ConnectTimeout as error:
        logger.log(default.format(error))
    except requests.exceptions.ReadTimeout as error:
        logger.log(default.format(error))
    except requests.exceptions.ProxyError as error:
        logger.log(default.format(error))
    except requests.exceptions.ConnectionError as error:
        logger.log(default.format(error))
    except requests.exceptions.ContentDecodingError as error:
        logger.log(default.format(error))
        logger.log(traceback.format_exc(), logger.DEBUG)
    except requests.exceptions.ChunkedEncodingError as error:
        logger.log(default.format(error))
    except requests.exceptions.InvalidURL as error:
        logger.log(default.format(error))
    except requests.exceptions.InvalidSchema as error:
        logger.log(default.format(error))
    except requests.exceptions.MissingSchema as error:
        logger.log(default.format(error))
    except requests.exceptions.RetryError as error:
        logger.log(default.format(error))
    except requests.exceptions.StreamConsumedError as error:
        logger.log(default.format(error))
    except requests.exceptions.URLRequired as error:
        logger.log(default.format(error))
    except TypeError as error:
        logger.log(default.format(error), logger.ERROR)
        logger.log('url is {0}'.format(repr(requests_exception.request.url)))
        logger.log('headers are {0}'.format(repr(requests_exception.request.headers)))
        logger.log('params are {0}'.format(repr(requests_exception.request.params)))
        logger.log('post_data is {0}'.format(repr(requests_exception.request.data)))
    except Exception as error:
        logger.log(default.format(error), logger.ERROR)
        logger.log(traceback.format_exc(), logger.DEBUG)


def get_size(start_path='.'):
    """
    Find the total dir and filesize of a path

    :param start_path: Path to recursively count size
    :return: total filesize
    """

    if not ek(os.path.isdir, start_path):
        return -1

    total_size = 0
    for dirpath, dirnames_, filenames in ek(os.walk, start_path):
        for f in filenames:
            fp = ek(os.path.join, dirpath, f)
            try:
                total_size += ek(os.path.getsize, fp)
            except OSError as error:
                logger.log("Unable to get size for file {0} Error: {1}".format(fp, error), logger.ERROR)
                logger.log(traceback.format_exc(), logger.DEBUG)
    return total_size


def generateApiKey():
    """ Return a new randomized API_KEY"""
    logger.log("Generating New API key")
    secure_hash = hashlib.sha512(str(time.time()))
    secure_hash.update(str(random.SystemRandom().getrandbits(4096)))
    return secure_hash.hexdigest()[:32]


def remove_article(text=''):
    """Remove the english articles from a text string"""

    return re.sub(r'(?i)^(?:(?:A(?!\s+to)n?)|The)\s(\w)', r'\1', text)


def generateCookieSecret():
    """Generate a new cookie secret"""

    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)


def disk_usage(path):
    if platform.system() == 'Windows':
        free = ctypes.c_ulonglong(0)
        if ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(six.text_type(path)), None, None, ctypes.pointer(free)) == 0:
            raise ctypes.WinError()
        return free.value

    elif hasattr(os, 'statvfs'):  # POSIX
        if platform.system() == 'Darwin':
            try:
                import subprocess
                call = subprocess.Popen(["df", "-k", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output = call.communicate()[0]
                return int(output.split("\n")[1].split()[3]) * 1024
            except Exception:
                pass

        st = ek(os.statvfs, path)
        return st.f_bavail * st.f_frsize  # pylint: disable=no-member

    else:
        raise Exception("Unable to determine free space on your OS")


def verify_freespace(src, dest, oldfile=None, method="copy"):
    """
    Checks if the target system has enough free space to copy or move a file.

    :param src: Source filename
    :param dest: Destination path (show dir in current usage)
    :param oldfile: File to be replaced (defaults to None)
    :return: True if there is enough space for the file, False if there isn't. Also returns True if the OS doesn't support this option
    """

    if not isinstance(oldfile, list):
        oldfile = [oldfile] if oldfile else []

    logger.log("Trying to determine free space on destination drive", logger.DEBUG)

    if not ek(os.path.isfile, src):
        logger.log("A path to a file is required for the source. {0} is not a file.".format(src), logger.WARNING)
        return True

    if not (ek(os.path.isdir, dest) or (sickbeard.CREATE_MISSING_SHOW_DIRS and ek(os.path.isdir, ek(os.path.dirname, dest)))):
        logger.log("A path is required for the destination. Check the root dir and show locations are correct for {0} (I got '{1}')".format(
            oldfile[0].name, dest), logger.WARNING)
        return False

    dest = (ek(os.path.dirname, dest), dest)[ek(os.path.isdir, dest)]

    # shortcut: if we are moving the file and the destination == src dir,
    # then by definition there is enough space
    if method == "move" and ek(os.stat, src).st_dev == ek(os.stat, dest).st_dev:  # pylint:
        # disable=no-member
        logger.log("Process method is 'move' and src and destination are on the same device, skipping free space check", logger.INFO)
        return True

    try:
        disk_free = disk_usage(dest)
    except Exception as error:
        logger.log("Unable to determine free space, so I will assume there is enough.", logger.WARNING)
        logger.log("Error: {error}".format(error=error), logger.DEBUG)
        logger.log(traceback.format_exc(), logger.DEBUG)
        return True

    # Lets also do this for symlink and hardlink
    if 'link' in method and disk_free > 1024**2:
        return True

    needed_space = ek(os.path.getsize, src)

    if oldfile:
        for f in oldfile:
            if ek(os.path.isfile, f.location):
                disk_free += ek(os.path.getsize, f.location)

    if disk_free > needed_space:
        return True
    else:
        logger.log("Not enough free space: Needed: {0} bytes ( {1} ), found: {2} bytes ( {3} )".format
                   (needed_space, pretty_file_size(needed_space), disk_free, pretty_file_size(disk_free)), logger.WARNING)
        return False


def disk_usage_hr(diskPath=None):
    """
    returns the free space in human readable bytes for a given path or False if no path given
    :param diskPath: the filesystem path being checked
    """
    if diskPath and ek(os.path.exists, diskPath):
        try:
            free = disk_usage(diskPath)
        except Exception as error:
            logger.log("Unable to determine free space", logger.WARNING)
            logger.log("Error: {error}".format(error=error), logger.DEBUG)
            logger.log(traceback.format_exc(), logger.DEBUG)
        else:
            return pretty_file_size(free)

    return False


# https://gist.github.com/thatalextaylor/7408395
def pretty_time_delta(seconds):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    time_delta = sign_string

    if days > 0:
        time_delta += '{0}d'.format(days)
    if hours > 0:
        time_delta += '{0}h'.format(hours)
    if minutes > 0:
        time_delta += '{0}m'.format(minutes)
    if seconds > 0:
        time_delta += '{0}s'.format(seconds)

    return time_delta


def is_file_locked(checkfile, write_check=False):
    """
    Checks to see if a file is locked. Performs three checks
        1. Checks if the file even exists
        2. Attempts to open the file for reading. This will determine if the file has a write lock.
            Write locks occur when the file is being edited or copied to, e.g. a file copy destination
        3. If the readLockCheck parameter is True, attempts to rename the file. If this fails the
            file is open by some other process for reading. The file can be read, but not written to
            or deleted.
    :param checkfile: the file being checked
    :param write_check: when true will check if the file is locked for writing (prevents move operations)
    """

    checkfile = ek(os.path.abspath, checkfile)

    if not ek(os.path.exists, checkfile):
        return True
    try:
        f = ek(io.open, checkfile, 'rb')
        f.close()  # pylint: disable=no-member
    except IOError:
        return True

    if write_check:
        lockFile = checkfile + ".lckchk"
        if ek(os.path.exists, lockFile):
            ek(os.remove, lockFile)
        try:
            ek(os.rename, checkfile, lockFile)
            time.sleep(1)
            ek(os.rename, lockFile, checkfile)
        except (OSError, IOError):
            return True

    return False


def tvdbid_from_remote_id(indexer_id, indexer):  # pylint:disable=too-many-return-statements

    session = make_session()
    tvdb_id = ''
    if indexer == 'IMDB':
        url = "http://www.thetvdb.com/api/GetSeriesByRemoteID.php?imdbid={0}".format(indexer_id)
        data = getURL(url, session=session, returns='content')
        if data is None:
            return tvdb_id
        try:
            tree = ElementTree.fromstring(data)
            for show in tree.getiterator("Series"):
                tvdb_id = show.findtext("seriesid")

        except SyntaxError:
            pass

        return tvdb_id
    elif indexer == 'ZAP2IT':
        url = "http://www.thetvdb.com/api/GetSeriesByRemoteID.php?zap2it={0}".format(indexer_id)
        data = getURL(url, session=session, returns='content')
        if data is None:
            return tvdb_id
        try:
            tree = ElementTree.fromstring(data)
            for show in tree.getiterator("Series"):
                tvdb_id = show.findtext("seriesid")

        except SyntaxError:
            pass

        return tvdb_id
    elif indexer == 'TVMAZE':
        url = "http://api.tvmaze.com/shows/{0}".format(indexer_id)
        data = getURL(url, session=session, returns='json')
        if data is None:
            return tvdb_id
        tvdb_id = data[b'externals'][b'thetvdb']
        return tvdb_id
    else:
        return tvdb_id


def get_showname_from_indexer(indexer, indexer_id, lang='en'):
    lINDEXER_API_PARMS = sickbeard.indexerApi(indexer).api_params.copy()
    lINDEXER_API_PARMS['language'] = lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

    logger.log('{0}: {1!r}'.format(sickbeard.indexerApi(indexer).name, lINDEXER_API_PARMS))

    t = sickbeard.indexerApi(indexer).indexer(**lINDEXER_API_PARMS)
    s = t[int(indexer_id)]

    if hasattr(s, 'data'):
        return s.data.get('seriesname')

    return None


def is_ip_private(ip):
    priv_lo = re.compile(r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_24 = re.compile(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_20 = re.compile(r"^192\.168\.\d{1,3}.\d{1,3}$")
    priv_16 = re.compile(r"^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")
    return priv_lo.match(ip) or priv_24.match(ip) or priv_20.match(ip) or priv_16.match(ip)


def recursive_listdir(path):
    for directory_path, directory_names, file_names in ek(os.walk, path, topdown=False):
        for filename in file_names:
            yield ek(os.path.join, directory_path, filename)


MESSAGE_COUNTER = 0


def add_site_message(message, level='danger'):
    with sickbeard.MESSAGES_LOCK:
        to_add = dict(level=level, message=message)

        basic_update_url = sickbeard.versionChecker.UpdateManager.get_update_url().split('?')[0]
        for index, existing in six.iteritems(sickbeard.SITE_MESSAGES):
            if basic_update_url in existing['message'] and basic_update_url in message:
                sickbeard.SITE_MESSAGES[index] = to_add
                return

            if message.endswith('Please use \'master\' unless specifically asked') and \
                    existing['message'].endswith('Please use \'master\' unless specifically asked'):
                sickbeard.SITE_MESSAGES[index] = to_add
                return

            if message.startswith('No NZB/Torrent providers found or enabled for') and \
                    existing['message'].startswith('No NZB/Torrent providers found or enabled for'):
                sickbeard.SITE_MESSAGES[index] = to_add
                return

        global MESSAGE_COUNTER
        MESSAGE_COUNTER += 1
        sickbeard.SITE_MESSAGES[MESSAGE_COUNTER] = to_add


def remove_site_message(begins='', ends='', contains='', key=None):
    with sickbeard.MESSAGES_LOCK:
        if key is not None and int(key) in sickbeard.SITE_MESSAGES:
            del sickbeard.SITE_MESSAGES[int(key)]

        for index, existing in six.iteritems(sickbeard.SITE_MESSAGES.copy()):
            checks = []
            if begins and isinstance(begins, six.string_types):
                checks.append(existing['message'].startswith(begins))
            if ends and isinstance(ends, six.string_types):
                checks.append(existing['message'].endsswith(ends))
            if contains and isinstance(ends, six.string_types):
                checks.append(contains in existing['message'])

            if all(checks):
                del sickbeard.SITE_MESSAGES[index]


def sortable_name(name):
    if not sickbeard.SORT_ARTICLE:
        name = re.sub(r'(?:The|A|An)\s', '', name, flags=re.I)
    return name.lower()


def manage_torrents_url(reset=False):
    if not reset:
        return sickbeard.CLIENT_WEB_URLS.get('torrent', '')

    if not sickbeard.USE_TORRENTS or not sickbeard.TORRENT_HOST.lower().startswith('http') or sickbeard.TORRENT_METHOD == 'blackhole' or \
            sickbeard.ENABLE_HTTPS and not sickbeard.TORRENT_HOST.lower().startswith('https'):
        sickbeard.CLIENT_WEB_URLS['torrent'] = ''
        return sickbeard.CLIENT_WEB_URLS.get('torrent')

    torrent_ui_url = re.sub('localhost|127.0.0.1', sickbeard.LOCALHOST_IP or get_lan_ip(), sickbeard.TORRENT_HOST or '', re.I)

    def test_exists(url):
        try:
            h = requests.head(url)
            return h.status_code != 404
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            return False

    if sickbeard.TORRENT_METHOD == 'utorrent':
        torrent_ui_url = '/'.join(s.strip('/') for s in (torrent_ui_url, 'gui/'))
    elif sickbeard.TORRENT_METHOD == 'download_station':
        if test_exists(urljoin(torrent_ui_url, 'download/')):
            torrent_ui_url = urljoin(torrent_ui_url, 'download/')

    sickbeard.CLIENT_WEB_URLS['torrent'] = ('', torrent_ui_url)[test_exists(torrent_ui_url)]

    return sickbeard.CLIENT_WEB_URLS.get('torrent')
