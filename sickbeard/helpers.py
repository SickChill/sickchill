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

import os
import io
import ctypes
import random
import re
import socket
import stat
import tempfile
import time
import traceback
import urllib
import urllib2
import hashlib
import httplib
import urlparse
import uuid
import base64
import zipfile
import datetime
import errno
import ast
import operator
import platform
import sickbeard
import adba
import requests
import certifi
from contextlib import closing
from socket import timeout as SocketTimeout

from sickbeard import logger, classes
from sickbeard.common import USER_AGENT
from sickbeard import db
from sickbeard.notifiers import synoindex_notifier
from sickrage.helper.common import http_code_description, media_extensions, pretty_file_size, subtitle_extensions
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex
from sickrage.show.Show import Show
from itertools import izip, cycle

import shutil
import shutil_custom

import xml.etree.ElementTree as ET
import json

shutil.copyfile = shutil_custom.copyfile_custom

# pylint: disable=protected-access
# Access to a protected member of a client class
urllib._urlopener = classes.SickBeardURLopener()


def fixGlob(path):
    path = re.sub(r'\[', '[[]', path)
    return re.sub(r'(?<!\[)\]', '[]]', path)


def indentXML(elem, level=0):
    """
    Does our pretty printing, makes Matt very happy
    """
    i = "\n" + level * "  "
    if len(elem):
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
        r'\[eztv\]$': 'searchre',
        r'\[ettv\]$': 'searchre',
        r'\[cttv\]$': 'searchre',
        r'\[vtv\]$': 'searchre',
        r'\[EtHD\]$': 'searchre',
        r'\[GloDLS\]$': 'searchre',
        r'\[silv4\]$': 'searchre',
        r'\[Seedbox\]$': 'searchre',
        r'\[PublicHD\]$': 'searchre',
        r'\[AndroidTwoU\]$': 'searchre',
        r'\[brassetv]\]$': 'searchre',
        r'\.\[BT\]$': 'searchre',
        r' \[1044\]$': 'searchre',
        r'\.RiPSaLoT$': 'searchre',
        r'\.GiuseppeTnT$': 'searchre',
        r'\.Renc$': 'searchre',
        r'\.gz$': 'searchre',
        r'(?<![57])\.1$': 'searchre',
        r'-NZBGEEK$': 'searchre',
        r'-Siklopentan$': 'searchre',
        r'-Chamele0n$': 'searchre',
        r'-Obfuscated$': 'searchre',
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
    }

    _name = name
    for remove_string, remove_type in removeWordsList.iteritems():
        if remove_type == 'search':
            _name = _name.replace(remove_string, '')
        elif remove_type == 'searchre':
            _name = re.sub(r'(?i)' + remove_string, '', _name)

    return _name


def isMediaFile(filename):
    """
    Check if named file may contain media

    :param filename: Filename to check
    :return: True if this is a known media file, False if not
    """

    # ignore samples
    try:
        if re.search(r'(^|[\W_])(?<!shomin.)(sample\d*)[\W_]', filename, re.I):
            return False

        # ignore RARBG release intro
        if re.search(r'^RARBG\.\w+\.(mp4|avi|txt)$', filename, re.I):
            return False

        # ignore MAC OS's retarded "resource fork" files
        if filename.startswith('._'):
            return False

        sepFile = filename.rpartition(".")

        if re.search('extras?$', sepFile[0], re.I):
            return False

        if sepFile[2].lower() in media_extensions:
            return True
        else:
            return False
    except TypeError as error:  # Not a string
        logger.log('Invalid filename. Filename must be a string. %s' % error, logger.DEBUG)  # pylint: disable=no-member
        return False


def isRarFile(filename):
    """
    Check if file is a RAR file, or part of a RAR set

    :param filename: Filename to check
    :return: True if this is RAR/Part file, False if not
    """

    archive_regex = r'(?P<file>^(?P<base>(?:(?!\.part\d+\.rar$).)*)\.(?:(?:part0*1\.)?rar)$)'

    if re.search(archive_regex, filename):
        return True

    return False


def isBeingWritten(filepath):
    """
    Check if file has been written in last 60 seconds

    :param filepath: Filename to check
    :return: True if file has been written recently, False if none
    """

    # Return True if file was modified within 60 seconds. it might still be being written to.
    ctime = max(ek(os.path.getctime, filepath), ek(os.path.getmtime, filepath))
    if ctime > time.time() - 60:
        return True

    return False


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
            synoindex_notifier.addFolder(path)
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
            logger.log(u"Trying to find " + name + " on " + sickbeard.indexerApi(i).name, logger.DEBUG)

            try:
                search = t[indexer_id] if indexer_id else t[name]
            except Exception:
                continue

            try:
                seriesname = search[0]['seriesname']
            except Exception:
                seriesname = None

            try:
                series_id = search[0]['id']
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


def listMediaFiles(path):
    """
    Get a list of files possibly containing media in a path

    :param path: Path to check for files
    :return: list of files
    """

    if not dir or not ek(os.path.isdir, path):
        return []

    files = []
    for curFile in ek(os.listdir, path):
        fullCurFile = ek(os.path.join, path, curFile)

        # if it's a folder do it recursively
        if ek(os.path.isdir, fullCurFile) and not curFile.startswith('.') and not curFile == 'Extras':
            files += listMediaFiles(fullCurFile)

        elif isMediaFile(curFile):
            files.append(fullCurFile)

    return files


def copyFile(srcFile, destFile):
    """
    Copy a file from source to destination

    :param srcFile: Path of source file
    :param destFile: Path of destination file
    """

    ek(shutil.copyfile, srcFile, destFile)
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
    TODO: Make this unicode proof

    :param src: Source file
    :param dst: Destination file
    """

    if os.name == 'nt':
        if ctypes.windll.kernel32.CreateHardLinkW(unicode(dst), unicode(src), 0) == 0:
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
    except Exception as e:
        logger.log(u"Failed to create hardlink of %s at %s. Error: %r. Copying instead"
                   % (srcFile, destFile, ex(e)), logger.WARNING)
        copyFile(srcFile, destFile)


def symlink(src, dst):
    """
    Create a soft/symlink between source and destination

    :param src: Source file
    :param dst: Destination file
    """

    if os.name == 'nt':
        if ctypes.windll.kernel32.CreateSymbolicLinkW(unicode(dst), unicode(src), 1 if ek(os.path.isdir, src) else 0) in [0, 1280]:
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
        ek(shutil.move, srcFile, destFile)
        fixSetGroupID(destFile)
        ek(symlink, destFile, srcFile)
    except Exception as e:
        logger.log(u"Failed to create symlink of %s at %s. Error: %r. Copying instead"
                   % (srcFile, destFile, ex(e)), logger.WARNING)
        copyFile(srcFile, destFile)


def make_dirs(path):
    """
    Creates any folders that are missing and assigns them the permissions of their
    parents
    """

    logger.log(u"Checking if the path %s already exists" % path, logger.DEBUG)

    if not ek(os.path.isdir, path):
        # Windows, create all missing folders
        if os.name == 'nt' or os.name == 'ce':
            try:
                logger.log(u"Folder %s didn't exist, creating it" % path, logger.DEBUG)
                ek(os.makedirs, path)
            except (OSError, IOError) as e:
                logger.log(u"Failed creating %s : %r" % (path, ex(e)), logger.ERROR)
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
                    logger.log(u"Folder %s didn't exist, creating it" % sofar, logger.DEBUG)
                    ek(os.mkdir, sofar)
                    # use normpath to remove end separator, otherwise checks permissions against itself
                    chmodAsParent(ek(os.path.normpath, sofar))
                    # do the library update for synoindex
                    synoindex_notifier.addFolder(sofar)
                except (OSError, IOError) as e:
                    logger.log(u"Failed creating %s : %r" % (sofar, ex(e)), logger.ERROR)
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

    if cur_file_ext[1:] in subtitle_extensions:
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
        logger.log(u"Renaming file from %s to %s" % (cur_path, new_path))
        ek(shutil.move, cur_path, new_path)
    except (OSError, IOError) as e:
        logger.log(u"Failed renaming %s to %s : %r" % (cur_path, new_path, ex(e)), logger.ERROR)
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

    logger.log(u"Trying to clean any empty folders under " + check_empty_dir)

    # as long as the folder exists and doesn't contain any files, delete it
    while ek(os.path.isdir, check_empty_dir) and check_empty_dir != keep_dir:
        check_files = ek(os.listdir, check_empty_dir)

        if not check_files or (len(check_files) <= len(ignore_items) and all(
                [check_file in ignore_items for check_file in check_files])):
            # directory is empty or contains only ignore_items
            try:
                logger.log(u"Deleting empty folder: " + check_empty_dir)
                # need shutil.rmtree when ignore_items is really implemented
                ek(os.rmdir, check_empty_dir)
                # do the library update for synoindex
                synoindex_notifier.deleteFolder(check_empty_dir)
            except OSError as e:
                logger.log(u"Unable to delete %s. Error: %r" % (check_empty_dir, repr(e)), logger.WARNING)
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

    if os.name == 'nt' or os.name == 'ce':
        return

    parentPath = ek(os.path.dirname, childPath)

    if not parentPath:
        logger.log(u"No parent path provided in " + childPath + ", unable to get permissions from it", logger.DEBUG)
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

    childPath_owner = childPathStat.st_uid
    user_id = os.geteuid()  # @UndefinedVariable - only available on UNIX

    if user_id != 0 and user_id != childPath_owner:
        logger.log(u"Not running as root or owner of " + childPath + ", not trying to set permissions", logger.DEBUG)
        return

    try:
        ek(os.chmod, childPath, childMode)
        logger.log(u"Setting permissions for %s to %o as parent directory has %o" % (childPath, childMode, parentMode),
                   logger.DEBUG)
    except OSError:
        logger.log(u"Failed to set permission for %s to %o" % (childPath, childMode), logger.DEBUG)


def fixSetGroupID(childPath):
    """
    Inherid SGID from parent
    (does not work on Windows hosts)

    :param childPath: Path to inherit SGID permissions from parent
    """

    if os.name == 'nt' or os.name == 'ce':
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

        childPath_owner = childStat.st_uid
        user_id = os.geteuid()  # @UndefinedVariable - only available on UNIX

        if user_id != 0 and user_id != childPath_owner:
            logger.log(u"Not running as root or owner of " + childPath + ", not trying to set the set-group-ID",
                       logger.DEBUG)
            return

        try:
            ek(os.chown, childPath, -1, parentGID)  # @UndefinedVariable - only available on UNIX
            logger.log(u"Respecting the set-group-ID bit on the parent directory for %s" % childPath, logger.DEBUG)
        except OSError:
            logger.log(
                u"Failed to respect the set-group-ID bit on the parent directory for %s (setting group ID %i)" % (
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
            absolute_number = int(sql_results[0]["absolute_number"])
            logger.log(u"Found absolute number %s for show %s S%02dE%02d" % (absolute_number, show.name, season, episode), logger.DEBUG)
        else:
            logger.log(u"No entries for absolute number for show %s S%02dE%02d" % (show.name, season, episode), logger.DEBUG)

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

    if not name:
        return ''

    bad_chars = u',:()!?\u2019'
    if not anime:
        bad_chars += u"'"

    # strip out any bad chars
    for x in bad_chars:
        name = name.replace(x, "")

    # tidy up stuff that doesn't belong in scene names
    name = name.replace("- ", ".").replace(" ", ".").replace("&", "and").replace('/', '.')
    name = re.sub(r"\.\.*", ".", name)

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
            raise Exception('Unsupported type {}'.format(node))

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
        from OpenSSL import crypto  # @UnresolvedImport
        from certgen import createKeyPair, createCertRequest, createCertificate, TYPE_RSA, \
            serial  # @UnresolvedImport
    except Exception:
        logger.log(u"pyopenssl module missing, please install for https access", logger.WARNING)
        return False

    # Create the CA Certificate
    cakey = createKeyPair(TYPE_RSA, 1024)
    careq = createCertRequest(cakey, CN='Certificate Authority')
    cacert = createCertificate(careq, (careq, cakey), serial, (0, 60 * 60 * 24 * 365 * 10))  # ten years

    cname = 'SickRage'
    pkey = createKeyPair(TYPE_RSA, 1024)
    req = createCertRequest(pkey, CN=cname)
    cert = createCertificate(req, (cacert, cakey), serial, (0, 60 * 60 * 24 * 365 * 10))  # ten years

    # Save the key and certificate to disk
    try:
        # pylint: disable=no-member
        # Module has no member
        io.open(ssl_key, 'wb').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        io.open(ssl_cert, 'wb').write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except Exception:
        logger.log(u"Error creating SSL key and certificate", logger.ERROR)
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
            logger.log(u"Not creating backup, %s doesn't exist" % old_file, logger.DEBUG)
            break

        try:
            logger.log(u"Trying to back up %s to %s" % (old_file, new_file), logger.DEBUG)
            shutil.copy(old_file, new_file)
            logger.log(u"Backup done", logger.DEBUG)
            break
        except Exception as e:
            logger.log(u"Error while trying to back up %s to %s : %r" % (old_file, new_file, ex(e)), logger.WARNING)
            numTries += 1
            time.sleep(1)
            logger.log(u"Trying again.", logger.DEBUG)

        if numTries >= 10:
            logger.log(u"Unable to back up %s to %s please do it manually." % (old_file, new_file), logger.ERROR)
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

    new_file, _ = ek(os.path.splitext, backup_file)
    restore_file = new_file + '.' + 'v' + str(version)

    if not ek(os.path.isfile, new_file):
        logger.log(u"Not restoring, %s doesn't exist" % new_file, logger.DEBUG)
        return False

    try:
        logger.log(u"Trying to backup %s to %s.r%s before restoring backup"
                   % (new_file, new_file, version), logger.DEBUG)

        shutil.move(new_file, new_file + '.' + 'r' + str(version))
    except Exception as e:
        logger.log(u"Error while trying to backup DB file %s before proceeding with restore: %r"
                   % (restore_file, ex(e)), logger.WARNING)
        return False

    while not ek(os.path.isfile, new_file):
        if not ek(os.path.isfile, restore_file):
            logger.log(u"Not restoring, %s doesn't exist" % restore_file, logger.DEBUG)
            break

        try:
            logger.log(u"Trying to restore file %s to %s" % (restore_file, new_file), logger.DEBUG)
            shutil.copy(restore_file, new_file)
            logger.log(u"Restore done", logger.DEBUG)
            break
        except Exception as e:
            logger.log(u"Error while trying to restore file %s. Error: %r" % (restore_file, ex(e)), logger.WARNING)
            numTries += 1
            time.sleep(1)
            logger.log(u"Trying again. Attempt #: %s" % numTries, logger.DEBUG)

        if numTries >= 10:
            logger.log(u"Unable to restore file %s to %s" % (restore_file, new_file), logger.WARNING)
            return False

    return True


# generates a md5 hash of a file
def md5_for_file(filename, block_size=2 ** 16):
    """
    Generate an md5 hash for a file
    :param filename: File to generate md5 hash for
    :param block_size: Block size to use (defaults to 2^16)
    :return MD5 hexdigest on success, or None on failure
    """

    # assert isinstance(filename, unicode)

    try:
        with io.open(filename, 'rb') as f:
            md5 = hashlib.md5()
            while True:
                data = f.read(block_size)
                if not data:
                    break
                md5.update(data)
            f.close()
            return md5.hexdigest()
    except Exception:
        return None


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
    # see also http://stackoverflow.com/questions/2924422
    # http://stackoverflow.com/questions/1140661
    good_codes = [httplib.OK, httplib.FOUND, httplib.MOVED_PERMANENTLY]

    host, path = urlparse.urlparse(url)[1:3]  # elems [1] and [2]
    try:
        conn = httplib.HTTPConnection(host)
        conn.request('HEAD', path)
        return conn.getresponse().status in good_codes
    except StandardError:
        return None


def anon_url(*url):
    """
    Return a URL string consisting of the Anonymous redirect URL and an arbitrary number of values appended.
    """
    return '' if None in url else '%s%s' % (sickbeard.ANON_REDIRECT, ''.join(str(s) for s in url))


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
    return re.sub('[. -]', ' ', sanitizeSceneName(name)).lower().lstrip()


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
    except Exception as e:
        logger.log(u"Error when attempting to find show: %s in SickRage. Error: %r " % (name, repr(e)), logger.DEBUG)

    return showObj


def is_hidden_folder(folder):
    """
    Returns True if folder is hidden.
    On Linux based systems hidden folders start with . (dot)
    :param folder: Full path of folder to check
    """
    def is_hidden(filepath):
        name = ek(os.path.basename, ek(os.path.abspath, filepath))
        return name.startswith('.') or has_hidden_attribute(filepath)

    def has_hidden_attribute(filepath):
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(filepath))
            assert attrs != -1
            result = bool(attrs & 2)
        except (AttributeError, AssertionError):
            result = False
        return result

    if ek(os.path.isdir, folder):
        if is_hidden(folder):
            return True

    return False


def real_path(path):
    """
    Returns: the canonicalized absolute pathname. The resulting path will have no symbolic link, '/./' or '/../' components.
    """
    return ek(os.path.normpath, ek(os.path.normcase, ek(os.path.realpath, path)))


def validateShow(show, season=None, episode=None):
    indexer_lang = show.lang

    try:
        lINDEXER_API_PARMS = sickbeard.indexerApi(show.indexer).api_params.copy()

        if indexer_lang and not indexer_lang == sickbeard.INDEXER_DEFAULT_LANGUAGE:
            lINDEXER_API_PARMS['language'] = indexer_lang

        if show.dvdorder != 0:
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
        logger.log(u"Usage of anidb disabled. Skiping", logger.DEBUG)
        return False

    if not sickbeard.ANIDB_USERNAME and not sickbeard.ANIDB_PASSWORD:
        logger.log(u"anidb username and/or password are not set. Aborting anidb lookup.", logger.DEBUG)
        return False

    if not sickbeard.ADBA_CONNECTION:
        def anidb_logger(msg):
            return logger.log(u"anidb: %s " % msg, logger.DEBUG)

        try:
            sickbeard.ADBA_CONNECTION = adba.Connection(keepAlive=True, log=anidb_logger)
        except Exception as e:
            logger.log(u"anidb exception msg: %r " % repr(e), logger.WARNING)
            return False

    try:
        if not sickbeard.ADBA_CONNECTION.authed():
            sickbeard.ADBA_CONNECTION.auth(sickbeard.ANIDB_USERNAME, sickbeard.ANIDB_PASSWORD)
        else:
            return True
    except Exception as e:
        logger.log(u"anidb exception msg: %r " % repr(e), logger.WARNING)
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
    except Exception as e:
        logger.log(u"Zip creation error: %r " % repr(e), logger.ERROR)
        return False


def extractZip(archive, targetDir):
    """
    Unzip a file to a directory

    :param fileList: A list of file names - full path each name
    :param archive: The file name for the archive with a full path
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
            target = file(ek(os.path.join, targetDir, filename), "wb")
            shutil.copyfileobj(source, target)
            source.close()
            target.close()
        zip_file.close()
        return True
    except Exception as e:
        logger.log(u"Zip extraction error: %r " % repr(e), logger.ERROR)
        return False


def backupConfigZip(fileList, archive, arcname=None):
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
    except Exception as e:
        logger.log(u"Zip creation error: %r " % repr(e), logger.ERROR)
        return False


def restoreConfigZip(archive, targetDir):
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
    except Exception as e:
        logger.log(u"Zip extraction error: %r" % ex(e), logger.ERROR)
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
            logger.log(u"Found indexer mapping in cache for show: " + showObj.name, logger.DEBUG)
            mapped[int(curResult['mindexer'])] = int(curResult['mindexer_id'])
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
                logger.log(u"Unable to map " + sickbeard.indexerApi(showObj.indexer).name + "->" + sickbeard.indexerApi(
                    indexer).name + " for show: " + showObj.name + ", skipping it", logger.DEBUG)
                continue

            if mapped_show and len(mapped_show) == 1:
                logger.log(u"Mapping " + sickbeard.indexerApi(showObj.indexer).name + "->" + sickbeard.indexerApi(
                    indexer).name + " for show: " + showObj.name, logger.DEBUG)

                mapped[indexer] = int(mapped_show[0]['id'])

                logger.log(u"Adding indexer mapping to DB for show: " + showObj.name, logger.DEBUG)

                sql_l.append([
                    "INSERT OR IGNORE INTO indexer_mapping (indexer_id, indexer, mindexer_id, mindexer) VALUES (?,?,?,?)",
                    [showObj.indexerid, showObj.indexer, int(mapped_show[0]['id']), indexer]])

        if len(sql_l) > 0:
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

    if atime is not None:
        try:
            with file(fname, 'a'):
                os.utime(fname, (atime, atime))
                return True
        except Exception as e:
            if e.errno == errno.ENOSYS:
                logger.log(u"File air date stamping not available on your OS. Please disable setting", logger.DEBUG)
            elif e.errno == errno.EACCES:
                logger.log(u"File air date stamping failed(Permission denied). Check permissions for file: %s" % fname, logger.ERROR)
            else:
                logger.log(u"File air date stamping failed. The error is: %r" % ex(e), logger.ERROR)

    return False


def _getTempDir():
    """
    Returns the [system temp dir]/tvdb_api-u501 (or
    tvdb_api-myuser)
    """

    import getpass

    if hasattr(os, 'getuid'):
        uid = "u%d" % (os.getuid())
    else:
        # For Windows
        try:
            uid = getpass.getuser()
        except ImportError:
            return ek(os.path.join, tempfile.gettempdir(), "sickrage")

    return ek(os.path.join, tempfile.gettempdir(), "sickrage-%s" % uid)


def _setUpSession(session, headers):
    """
    Returns a session initialized with default cache and parameter settings

    :param session: session object to (re)use
    :param headers: Headers to pass to session
    :return: session object
    """

    # request session
    # Lets try without caching sessions to disk for awhile
    # cache_dir = sickbeard.CACHE_DIR or _getTempDir()
    # session = CacheControl(sess=session, cache=caches.FileCache(ek(os.path.join, cache_dir, 'sessions'), use_dir_lock=True), cache_etags=False)

    # request session clear residual referer
    # pylint: disable=superfluous-parens
    # These extra parens are necessary!
    if 'Referer' in session.headers and 'Referer' not in (headers or {}):
        session.headers.pop('Referer')

    # request session headers
    session.headers.update({'User-Agent': USER_AGENT, 'Accept-Encoding': 'gzip,deflate'})
    if headers:
        session.headers.update(headers)

    # request session ssl verify
    session.verify = certifi.old_where() if sickbeard.SSL_VERIFY else False

    # request session proxies
    if 'Referer' not in session.headers and sickbeard.PROXY_SETTING:
        logger.log(u"Using global proxy: " + sickbeard.PROXY_SETTING, logger.DEBUG)
        scheme, address = urllib2.splittype(sickbeard.PROXY_SETTING)
        address = sickbeard.PROXY_SETTING if scheme else 'http://' + sickbeard.PROXY_SETTING
        session.proxies = {
            "http": address,
            "https": address,
        }
        session.headers.update({'Referer': address})

    if 'Content-Type' in session.headers:
        session.headers.pop('Content-Type')

    return session


def getURL(url, post_data=None, params=None, headers=None, timeout=30, session=None, json=False, need_bytes=False):
    """
    Returns a byte-string retrieved from the url provider.
    """

    session = _setUpSession(session, headers)

    if params and isinstance(params, (list, dict)):
        for param in params:
            if isinstance(params[param], unicode):
                params[param] = params[param].encode('utf-8')

    session.params = params

    try:
        # decide if we get or post data to server
        if post_data:
            if isinstance(post_data, (list, dict)):
                for param in post_data:
                    if isinstance(post_data[param], unicode):
                        post_data[param] = post_data[param].encode('utf-8')

            session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
            resp = session.post(url, data=post_data, timeout=timeout, allow_redirects=True, verify=session.verify)
        else:
            resp = session.get(url, timeout=timeout, allow_redirects=True, verify=session.verify)

        if not resp.ok:
            logger.log(u"Requested getURL %s returned status code is %s: %s"
                       % (url, resp.status_code, http_code_description(resp.status_code)), logger.DEBUG)
            return None

    except (SocketTimeout, TypeError) as e:
        logger.log(u"Connection timed out (sockets) accessing getURL %s Error: %r" % (url, ex(e)), logger.WARNING)
        return None
    except requests.exceptions.HTTPError as e:
        logger.log(u"HTTP error in getURL %s Error: %r" % (url, ex(e)), logger.WARNING)
        return None
    except requests.exceptions.ConnectionError as e:
        logger.log(u"Connection error to getURL %s Error: %r" % (url, ex(e)), logger.WARNING)
        return None
    except requests.exceptions.Timeout as e:
        logger.log(u"Connection timed out accessing getURL %s Error: %r" % (url, ex(e)), logger.WARNING)
        return None
    except requests.exceptions.ContentDecodingError:
        logger.log(u"Content-Encoding was gzip, but content was not compressed. getURL: %s" % url, logger.DEBUG)
        logger.log(traceback.format_exc(), logger.DEBUG)
        return None
    except Exception as e:
        logger.log(u"Unknown exception in getURL %s Error: %r" % (url, ex(e)), logger.WARNING)
        logger.log(traceback.format_exc(), logger.WARNING)
        return None

    return (resp.text, resp.content)[need_bytes] if not json else resp.json()


def download_file(url, filename, session=None, headers=None):
    """
    Downloads a file specified

    :param url: Source URL
    :param filename: Target file on filesystem
    :param session: request session to use
    :param headers: override existing headers in request session
    :return: True on success, False on failure
    """

    session = _setUpSession(session, headers)
    session.stream = True

    try:
        with closing(session.get(url, allow_redirects=True, verify=session.verify)) as resp:
            if not resp.ok:
                logger.log(u"Requested download url %s returned status code is %s: %s"
                           % (url, resp.status_code, http_code_description(resp.status_code)), logger.DEBUG)
                return False

            try:
                with io.open(filename, 'wb') as fp:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            fp.write(chunk)
                            fp.flush()

                chmodAsParent(filename)
            except Exception:
                logger.log(u"Problem setting permissions or writing file to: %s" % filename, logger.WARNING)

    except (SocketTimeout, TypeError) as e:
        remove_file_failed(filename)
        logger.log(u"Connection timed out (sockets) while loading download URL %s Error: %r" % (url, ex(e)), logger.WARNING)
        return None
    except requests.exceptions.HTTPError as e:
        remove_file_failed(filename)
        logger.log(u"HTTP error %r while loading download URL %s " % (ex(e), url), logger.WARNING)
        return False
    except requests.exceptions.ConnectionError as e:
        remove_file_failed(filename)
        logger.log(u"Connection error %r while loading download URL %s " % (ex(e), url), logger.WARNING)
        return False
    except requests.exceptions.Timeout as e:
        remove_file_failed(filename)
        logger.log(u"Connection timed out %r while loading download URL %s " % (ex(e), url), logger.WARNING)
        return False
    except EnvironmentError as e:
        remove_file_failed(filename)
        logger.log(u"Unable to save the file: %r " % ex(e), logger.WARNING)
        return False
    except Exception:
        remove_file_failed(filename)
        logger.log(u"Unknown exception while loading download URL %s : %r" % (url, traceback.format_exc()), logger.WARNING)
        return False

    return True


def get_size(start_path='.'):
    """
    Find the total dir and filesize of a path

    :param start_path: Path to recursively count size
    :return: total filesize
    """

    if not ek(os.path.isdir, start_path):
        return -1

    total_size = 0
    for dirpath, _, filenames in ek(os.walk, start_path):
        for f in filenames:
            fp = ek(os.path.join, dirpath, f)
            try:
                total_size += ek(os.path.getsize, fp)
            except OSError as e:
                logger.log(u"Unable to get size for file %s Error: %r" % (fp, ex(e)), logger.ERROR)
                logger.log(traceback.format_exc(), logger.DEBUG)
    return total_size


def generateApiKey():
    """ Return a new randomized API_KEY"""

    try:
        from hashlib import md5
    except ImportError:
        from md5 import md5

    # Create some values to seed md5
    t = str(time.time())
    r = str(random.random())

    # Create the md5 instance and give it the current time
    m = md5(t)

    # Update the md5 instance with the random variable
    m.update(r)

    # Return a hex digest of the md5, eg 49f68a5c8493ec2c0bf489821c21fc3b
    logger.log(u"New API generated")
    return m.hexdigest()


def remove_article(text=''):
    """Remove the english articles from a text string"""

    return re.sub(r'(?i)^(?:(?:A(?!\s+to)n?)|The)\s(\w)', r'\1', text)


def generateCookieSecret():
    """Generate a new cookie secret"""

    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)


def verify_freespace(src, dest, oldfile=None):
    """
    Checks if the target system has enough free space to copy or move a file.

    :param src: Source filename
    :param dest: Destination path
    :param oldfile: File to be replaced (defaults to None)
    :return: True if there is enough space for the file, False if there isn't. Also returns True if the OS doesn't support this option
    """

    if not isinstance(oldfile, list):
        oldfile = [oldfile]

    logger.log(u"Trying to determine free space on destination drive", logger.DEBUG)

    if hasattr(os, 'statvfs'):  # POSIX
        def disk_usage(path):
            st = ek(os.statvfs, path)
            free = st.f_bavail * st.f_frsize
            return free

    elif os.name == 'nt':       # Windows
        import sys

        def disk_usage(path):
            _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
            if sys.version_info >= (3,) or isinstance(path, unicode):
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
            else:
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
            ret = fun(path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
            if ret == 0:
                logger.log(u"Unable to determine free space, something went wrong", logger.WARNING)
                raise ctypes.WinError()
            return free.value
    else:
        logger.log(u"Unable to determine free space on your OS")
        return True

    if not ek(os.path.isfile, src):
        logger.log(u"A path to a file is required for the source. " + src + " is not a file.", logger.WARNING)
        return True

    try:
        diskfree = disk_usage(dest)
    except Exception:
        logger.log(u"Unable to determine free space, so I will assume there is enough.", logger.WARNING)
        return True

    neededspace = ek(os.path.getsize, src)

    if oldfile:
        for f in oldfile:
            if ek(os.path.isfile, f.location):
                diskfree += ek(os.path.getsize, f.location)

    if diskfree > neededspace:
        return True
    else:
        logger.log(u"Not enough free space: Needed: %s bytes ( %s ), found: %s bytes ( %s )"
                   % (neededspace, pretty_file_size(neededspace), diskfree, pretty_file_size(diskfree)), logger.WARNING)
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
        time_delta += ' %dd' % days
    if hours > 0:
        time_delta += ' %dh' % hours
    if minutes > 0:
        time_delta += ' %dm' % minutes
    if seconds > 0:
        time_delta += ' %ds' % seconds

    return time_delta


def isFileLocked(checkfile, writeLockCheck=False):
    """
    Checks to see if a file is locked. Performs three checks
        1. Checks if the file even exists
        2. Attempts to open the file for reading. This will determine if the file has a write lock.
            Write locks occur when the file is being edited or copied to, e.g. a file copy destination
        3. If the readLockCheck parameter is True, attempts to rename the file. If this fails the
            file is open by some other process for reading. The file can be read, but not written to
            or deleted.
    :param file: the file being checked
    :param writeLockCheck: when true will check if the file is locked for writing (prevents move operations)
    """

    checkfile = ek(os.path.abspath, checkfile)

    if not ek(os.path.exists, checkfile):
        return True
    try:
        f = io.open(checkfile, 'rb')
        f.close()
    except IOError:
        return True

    if writeLockCheck:
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


def getDiskSpaceUsage(diskPath=None):
    """
    returns the free space in human readable bytes for a given path or False if no path given
    :param diskPath: the filesystem path being checked
    """
    if diskPath and ek(os.path.exists, diskPath):
        if platform.system() == 'Windows':
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(diskPath), None, None, ctypes.pointer(free_bytes))
            return pretty_file_size(free_bytes.value)
        else:
            st = ek(os.statvfs, diskPath)
            return pretty_file_size(st.f_bavail * st.f_frsize)
    else:
        return False


def getTVDBFromID(indexer_id, indexer):

    session = requests.Session()
    tvdb_id = ''
    if indexer == 'IMDB':
        url = "http://www.thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%s" % indexer_id
        data = getURL(url, session=session, need_bytes=True)
        if data is None:
            return tvdb_id
        try:
            tree = ET.fromstring(data)
            for show in tree.getiterator("Series"):
                tvdb_id = show.findtext("seriesid")

        except SyntaxError:
            pass

        return tvdb_id
    elif indexer == 'ZAP2IT':
        url = "http://www.thetvdb.com/api/GetSeriesByRemoteID.php?zap2it=%s" % indexer_id
        data = getURL(url, session=session, need_bytes=True)
        if data is None:
            return tvdb_id
        try:
            tree = ET.fromstring(data)
            for show in tree.getiterator("Series"):
                tvdb_id = show.findtext("seriesid")

        except SyntaxError:
            pass

        return tvdb_id
    elif indexer == 'TVMAZE':
        url = "http://api.tvmaze.com/shows/%s" % indexer_id
        data = getURL(url, session=session, json=True)
        if data is None:
            return tvdb_id
        tvdb_id = data['externals']['thetvdb']
        return tvdb_id
    else:
        return tvdb_id


def is_ip_private(ip):
    priv_lo = re.compile(r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_24 = re.compile(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_20 = re.compile(r"^192\.168\.\d{1,3}.\d{1,3}$")
    priv_16 = re.compile(r"^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")
    return priv_lo.match(ip) or priv_24.match(ip) or priv_20.match(ip) or priv_16.match(ip)
