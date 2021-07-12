import base64
import ctypes
import datetime
import hashlib
import ipaddress
import os
import platform
import random
import re
import shutil
import socket
import ssl
import stat
import time
import traceback
import urllib.request
import uuid
import zipfile
from contextlib import closing
from itertools import cycle
from urllib.parse import urljoin
from xml.etree import ElementTree

import certifi
import cloudscraper
import ifaddr
import rarfile
import requests
import urllib3.exceptions
from cachecontrol import CacheControl
from cloudscraper.exceptions import CloudflareException
from tornado._locale_data import LOCALE_NAMES
from unidecode import unidecode
from urllib3 import disable_warnings

import sickchill
from sickchill import adba, logger, settings
from sickchill.helper import episode_num, MEDIA_EXTENSIONS, pretty_file_size, SUBTITLE_EXTENSIONS
from sickchill.helper.common import replace_extension
from sickchill.oldbeard.common import USER_AGENT
from sickchill.show.Show import Show

from . import db

# Add some missing languages
LOCALE_NAMES.update(
    {
        "ar_SA": {"name_en": "Arabic (Saudi Arabia)", "name": "(العربية (المملكة العربية السعودية"},
        "no_NO": {"name_en": "Norwegian", "name": "Norsk"},
    }
)


_context = None


def make_context(verify: bool):
    global _context
    if not _context or (_context and _context.check_hostname != verify):
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.options |= ssl.OP_NO_SSLv2
        context.verify_mode = ssl.CERT_REQUIRED if verify else ssl.CERT_NONE
        context.check_hostname = verify
        context.load_verify_locations(certifi.where(), None)
        _context = context
    return _context


def set_opener(verify: bool):
    disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        from urllib.request import HTTPSHandler

        https_handler = HTTPSHandler(context=make_context(verify), check_hostname=True)
        opener = urllib.request.build_opener(https_handler)
    except ImportError:
        opener = urllib.request.build_opener()

    opener.addheaders = [("User-agent", sickchill.oldbeard.common.USER_AGENT)]
    urllib.request.install_opener(opener)


set_opener(settings.SSL_VERIFY)

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
        r"\[rartv\]$": "searchre",
        r"\[rarbg\]$": "searchre",
        r"\.\[eztv\]$": "searchre",
        r"\[eztv\]$": "searchre",
        r"\[ettv\]$": "searchre",
        r"\[cttv\]$": "searchre",
        r"\.\[vtv\]$": "searchre",
        r"\[vtv\]$": "searchre",
        r"\[EtHD\]$": "searchre",
        r"\[GloDLS\]$": "searchre",
        r"\[silv4\]$": "searchre",
        r"\[Seedbox\]$": "searchre",
        r"\[PublicHD\]$": "searchre",
        r"\.\[PublicHD\]$": "searchre",
        r"\.\[NO.RAR\]$": "searchre",
        r"\[NO.RAR\]$": "searchre",
        r"-\=\{SPARROW\}\=-$": "searchre",
        r"\=\{SPARR$": "searchre",
        r"\.\[720P\]\[HEVC\]$": "searchre",
        r"\[AndroidTwoU\]$": "searchre",
        r"\[brassetv\]$": "searchre",
        r"\[Talamasca32\]$": "searchre",
        r"\(musicbolt\.com\)$": "searchre",
        r"\.\(NLsub\)$": "searchre",
        r"\(NLsub\)$": "searchre",
        r"\.\[BT\]$": "searchre",
        r" \[1044\]$": "searchre",
        r"\.RiPSaLoT$": "searchre",
        r"\.GiuseppeTnT$": "searchre",
        r"\.Renc$": "searchre",
        r"\.gz$": "searchre",
        r"\.English$": "searchre",
        r"\.German$": "searchre",
        r"\.\.Italian$": "searchre",
        r"\.Italian$": "searchre",
        r"(?<![57])\.1$": "searchre",
        r"-NZBGEEK$": "searchre",
        r"-Siklopentan$": "searchre",
        r"-Chamele0n$": "searchre",
        r"-Obfuscated$": "searchre",
        r"-Pre$": "searchre",
        r"-postbot$": "searchre",
        r"-BUYMORE$": "searchre",
        r"-\[SpastikusTV\]$": "searchre",
        r"-RP$": "searchre",
        r"-20-40$": "searchre",
        r"\.\[www\.usabit\.com\]$": "searchre",
        r"^\[www\.Cpasbien\.pe\] ": "searchre",
        r"^\[www\.Cpasbien\.com\] ": "searchre",
        r"^\[ www\.Cpasbien\.pw \] ": "searchre",
        r"^\.www\.Cpasbien\.pw": "searchre",
        r"^\[www\.newpct1\.com\]": "searchre",
        r"^\[ www\.Cpasbien\.com \] ": "searchre",
        r"- \{ www\.SceneTime\.com \}$": "searchre",
        r"^\{ www\.SceneTime\.com \} - ": "searchre",
        r"^\]\.\[www\.tensiontorrent.com\] - ": "searchre",
        r"^\]\.\[ www\.tensiontorrent.com \] - ": "searchre",
        r"- \[ www\.torrentday\.com \]$": "searchre",
        r"^\[ www\.TorrentDay\.com \] - ": "searchre",
        r"\[NO-RAR\] - \[ www\.torrentday\.com \]$": "searchre",
        r"^www\.Torrenting\.com\.-\.": "searchre",
        r"-Scrambled$": "searchre",
        r"^Torrent9\.PH ---> ": "searchre",
        r"-xpost$": "searchre",
    }

    _name = name
    for remove_string, remove_type in removeWordsList.items():
        if remove_type == "search":
            _name = _name.replace(remove_string, "")
        elif remove_type == "searchre":
            _name = re.sub(r"(?i){}".format(remove_string), "", _name)

    return _name.strip()


def is_media_file(filename):
    """
    Check if named file may contain media

    :param filename: Filename to check
    :return: True if this is a known media file, False if not
    """

    # ignore samples
    try:
        assert isinstance(filename, str), type(filename)
        is_rar = is_rar_file(filename)
        filename = os.path.basename(filename)

        if re.search(r"(^|[\W_])(?<!shomin.)(sample\d*)[\W_]", filename, re.I):
            return False

        # ignore RARBG release intro
        if re.search(r"^RARBG\.(\w+\.)?(mp4|avi|txt)$", filename, re.I):
            return False

        # ignore Kodi tvshow trailers
        if filename == "tvshow-trailer.mp4":
            return False

        # ignore MAC OS's retarded "resource fork" files
        if filename.startswith("._"):
            return False

        filname_parts = filename.rpartition(".")

        if re.search("extras?$", filname_parts[0], re.I):
            return False

        return filname_parts[-1].lower() in MEDIA_EXTENSIONS or (settings.UNPACK == settings.UNPACK_PROCESS_INTACT and is_rar)
    except (TypeError, AssertionError) as error:  # Not a string
        logger.debug(_("Invalid filename. Filename must be a string. {0}").format(error))
        return False


def is_rar_file(filename):
    """
    Check if file is a RAR file, or part of a RAR set

    :param filename: Filename to check
    :return: True if this is RAR/Part file, False if not
    """
    archive_regex = r"(?P<file>^(?P<base>(?:(?!\.part\d+\.rar$).)*)\.(?:(?:part0*1\.)?rar)$)"
    ret = re.search(archive_regex, filename) is not None
    try:
        if ret and os.path.exists(filename) and os.path.isfile(filename):
            ret = rarfile.is_rarfile(filename)
    except (IOError, OSError):
        pass

    return ret


def remove_file_failed(failed_file):
    """
    Remove file from filesystem

    :param failed_file: File to remove
    """

    # noinspection PyBroadException
    try:
        os.remove(failed_file)
    except Exception:
        pass


def makeDir(path):
    """
    Make a directory on the filesystem

    :param path: directory to make
    :return: True if success, False if failure
    """

    if not os.path.isdir(path):
        try:
            os.makedirs(path)
            # do the library update for synoindex
            sickchill.oldbeard.notifiers.synoindex_notifier.addFolder(path)
        except OSError:
            return False
    return True


def list_media_files(path):
    """
    Get a list of files possibly containing media in a path

    :param path: Path to check for files
    :return: list of files
    """

    if not path or not os.path.isdir(path):
        return []

    files = []
    for entry in os.listdir(path):
        full_entry = os.path.join(path, entry)

        # if it's a folder do it recursively
        if os.path.isdir(full_entry) and not entry.startswith(".") and not entry == "Extras":
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
        shutil.copyfile(srcFile, destFile)
    except shutil.SameFileError:
        return
    except (shutil.SpecialFileError, shutil.Error) as error:
        logger.warning("{0}".format(error))
        raise error
    except Exception as error:
        logger.exception("{0}".format(error))
        raise error

    try:
        shutil.copymode(srcFile, destFile)
    except OSError:
        pass


def moveFile(srcFile, destFile):
    """
    Move a file from source to destination

    :param srcFile: Path of source file
    :param destFile: Path of destination file
    """
    try:
        shutil.move(srcFile, destFile)
    except OSError:
        copyFile(srcFile, destFile)
        os.unlink(srcFile)

    fixSetGroupID(destFile)


def hardlinkFile(srcFile, destFile):
    """
    Create a hard-link (inside filesystem link) between source and destination

    :param srcFile: Source file
    :param destFile: Destination file
    """

    try:
        os.link(srcFile, destFile)
    except Exception as error:
        logger.warning(_("Failed to create hardlink of {0} at {1}. Error: {2}. Copying instead").format(srcFile, destFile, error))
        copyFile(srcFile, destFile)

    fixSetGroupID(destFile)


def moveAndSymlinkFile(srcFile, destFile):
    """
    Move a file from source to destination, then create a symlink back from destination from source. If this fails, copy
    the file from source to destination

    :param srcFile: Source file
    :param destFile: Destination file
    """

    try:
        moveFile(srcFile, destFile)
        os.symlink(destFile, srcFile)
    except Exception as error:
        logger.warning(_("Failed to create symlink of {0} at {1}. Error: {2}. Copying instead").format(srcFile, destFile, error))
        copyFile(srcFile, destFile)


def make_dirs(path):
    """
    Creates any folders that are missing and assigns them the permissions of their
    parents
    """

    logger.debug(_("Checking if the path {0} already exists").format(path))

    if not os.path.isdir(path):
        # Windows, create all missing folders
        if platform.system() == "Windows":
            try:
                logger.debug(_("Folder {0} didn't exist, creating it").format(path))
                os.makedirs(path)
            except (OSError, IOError) as error:
                logger.exception(_("Failed creating {0} : {1}").format(path, error))
                return False

        # not Windows, create all missing folders and set permissions
        else:
            sofar = ""
            folder_list = path.split(os.path.sep)

            # look through each subfolder and make sure they all exist
            for cur_folder in folder_list:
                sofar += cur_folder + os.path.sep

                # if it exists then just keep walking down the line
                if os.path.isdir(sofar):
                    continue

                try:
                    logger.debug(_("Folder {0} didn't exist, creating it").format(sofar))
                    os.mkdir(sofar)
                    # use normpath to remove end separator, otherwise checks permissions against itself
                    chmodAsParent(os.path.normpath(sofar))
                    # do the library update for synoindex
                    sickchill.oldbeard.notifiers.synoindex_notifier.addFolder(sofar)
                except (OSError, IOError) as error:
                    logger.exception(_("Failed creating {0} : {1}").format(sofar, error))
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

    # new_dest_dir, new_dest_name = os.path.split(new_path)

    if old_path_length == 0 or old_path_length > len(cur_path):
        # approach from the right
        cur_filename, cur_file_ext = os.path.splitext(cur_path)
    else:
        # approach from the left
        cur_file_ext = cur_path[old_path_length:]
        cur_filename = cur_path[:old_path_length]

    if cur_file_ext[1:] in SUBTITLE_EXTENSIONS:
        # Extract subtitle language from filename
        sublang = os.path.splitext(cur_filename)[1][1:]

        # Check if the language extracted from filename is a valid language
        if sublang in sickchill.oldbeard.subtitles.subtitle_code_filter():
            cur_file_ext = "." + sublang + cur_file_ext

    # put the extension on the incoming file
    new_path += cur_file_ext

    make_dirs(os.path.dirname(new_path))

    # move the file
    try:
        logger.info(_("Renaming file from {0} to {1}").format(cur_path, new_path))
        shutil.move(cur_path, new_path)
    except (OSError, IOError) as error:
        logger.exception(_("Failed renaming {0} to {1} : {2}").format(cur_path, new_path, error))
        return False

    # clean up any old folders that are empty
    delete_empty_folders(os.path.dirname(cur_path))

    return True


def delete_empty_folders(check_empty_dir, keep_dir=None):
    """
    Walks backwards up the path and deletes any empty folders found.

    :param check_empty_dir: The path to clean (absolute path to a folder)
    :param keep_dir: Clean until this path is reached
    """

    # treat check_empty_dir as empty when it only contains these items
    ignore_items = []

    logger.info(_("Trying to clean any empty folders under ") + check_empty_dir)

    # as long as the folder exists and doesn't contain any files, delete it
    while os.path.isdir(check_empty_dir) and check_empty_dir != keep_dir:
        check_files = os.listdir(check_empty_dir)

        if not check_files or (len(check_files) <= len(ignore_items) and all(check_file in ignore_items for check_file in check_files)):
            # directory is empty or contains only ignore_items
            try:
                logger.info(_("Deleting empty folder: ") + check_empty_dir)
                # need shutil.rmtree when ignore_items is really implemented
                os.rmdir(check_empty_dir)
                # do the library update for synoindex
                sickchill.oldbeard.notifiers.synoindex_notifier.deleteFolder(check_empty_dir)
            except OSError as error:
                logger.warning(_("Unable to delete {0}. Error: {1}").format(check_empty_dir, error))
                break
            check_empty_dir = os.path.dirname(check_empty_dir)
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

    if platform.system() == "Windows":
        return

    parentPath = os.path.dirname(childPath)

    if not parentPath:
        logger.debug(_("No parent path provided in {location} unable to get permissions from it").format(location=childPath))
        return

    childPath = os.path.join(parentPath, os.path.basename(childPath))

    parentPathStat = os.stat(parentPath)
    parentMode = stat.S_IMODE(parentPathStat[stat.ST_MODE])

    childPathStat = os.stat(childPath)
    childPath_mode = stat.S_IMODE(childPathStat[stat.ST_MODE])

    if os.path.isfile(childPath):
        childMode = fileBitFilter(parentMode)
    else:
        childMode = parentMode

    if childPath_mode == childMode:
        return

    childPath_owner = childPathStat.st_uid
    user_id = os.geteuid()  # @UndefinedVariable - only available on UNIX

    if user_id not in (childPath_owner, 0):
        logger.debug(_("Not running as root or owner of {location}, not trying to set permissions").format(location=childPath))
        return

    try:
        os.chmod(childPath, childMode)
    except OSError:
        logger.debug(_("Failed to set permission for {0} to {1:o}, parent directory has {2:o}").format(childPath, childMode, parentMode))


def fixSetGroupID(childPath):
    """
    Inherid SGID from parent
    (does not work on Windows hosts)

    :param childPath: Path to inherit SGID permissions from parent
    """

    if platform.system() == "Windows":
        return

    try:
        parentPath = os.path.dirname(childPath)
        parentStat = os.stat(parentPath)
        parentMode = stat.S_IMODE(parentStat[stat.ST_MODE])

        childPath = os.path.join(parentPath, os.path.basename(childPath))

        if parentMode & stat.S_ISGID:
            parentGID = parentStat[stat.ST_GID]
            childStat = os.stat(childPath)
            childGID = childStat[stat.ST_GID]

            if childGID == parentGID:
                return

            childPath_owner = childStat.st_uid
            user_id = os.geteuid()

            if user_id not in (childPath_owner, 0):
                logger.debug(_("Not running as root or owner of {}, not trying to set the set-group-ID").format(childPath))
                return

            try:
                os.chown(childPath, -1, parentGID)
                logger.debug(_("Respecting the set-group-ID bit on the parent directory for {0}").format(childPath))
            except (OSError, PermissionError):
                logger.debug("Failed to respect the set-group-ID bit on the parent directory for {0} (setting group ID {1})".format(childPath, parentGID))
    except Exception as error:
        logger.debug(f"Error setting set-group-id on the parent directory. {error}")


def is_anime_in_show_list():
    """
    Check if any shows in list contain anime

    :return: True if global showlist contains Anime, False if not
    """

    for show in settings.showList:
        if show.is_anime:
            return True
    return False


def update_anime_support():
    """Check if we need to support anime, and if we do, enable the feature"""

    settings.ANIMESUPPORT = is_anime_in_show_list()


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
            logger.debug(
                _("Found absolute number {absolute} for show {show} {ep}").format(absolute=absolute_number, show=show.name, ep=episode_num(season, episode))
            )
        else:
            logger.debug(_("No entries for absolute number for show {show} {ep}").format(show=show.name, ep=episode_num(season, episode)))

    return absolute_number


def get_all_episodes_from_absolute_number(show, absolute_numbers, indexer_id=None):
    episodes = []
    season = None

    if absolute_numbers:
        if indexer_id and not show:
            show = Show.find(settings.showList, indexer_id)

        for absolute_number in absolute_numbers if show else []:
            ep = show.getEpisode(None, None, absolute_number=absolute_number)
            if ep:
                episodes.append(ep.episode)
                season = ep.season  # this will always take the last found season so eps that cross the season border are not handeled well

    return season, episodes


def sanitizeSceneName(name, anime=False):
    """
    Takes a show name and returns the "scenified" version of it.
    :param name: The name to sanitize
    :param anime: Some show have a ' in their name(Kuroko's Basketball) and is needed for search.
    :return: A string containing the scene version of the show name given.
    """

    if not name:
        return ""

    bad_chars = ",:()!?\u2019"
    if not anime:
        bad_chars += "'’`"

    # strip out any bad chars
    for x in bad_chars:
        name = name.replace(x, "")

    # tidy up stuff that doesn't belong in scene names
    name = name.replace("&", "and")
    name = re.sub(r"[-/\s]+", ".", name)
    name = re.sub(r"[.]+", ".", name)

    if name.endswith("."):
        name = name[:-1]

    return name


def create_https_certificates(ssl_cert, ssl_key):
    """
    Create self-signed HTTPS certificares and store in paths 'ssl_cert' and 'ssl_key'

    :param ssl_cert: Path of SSL certificate file to write
    :param ssl_key: Path of SSL keyfile to write
    :return: True on success, False on failure
    """

    # assert isinstance(ssl_key, unicode)
    # assert isinstance(ssl_cert, unicode)

    # noinspection PyBroadException
    try:
        from OpenSSL import crypto

        from sickchill.certgen import createCertificate, createCertRequest, createKeyPair, TYPE_RSA
    except Exception:
        logger.info(traceback.format_exc())
        logger.warning(_("pyopenssl module missing, please install for https access"))
        return False

    cakey = createKeyPair(TYPE_RSA, 4096)
    careq = createCertRequest(cakey, CN="Certificate Authority")
    params = {
        "req": careq,
        "issuerCert": careq,
        "issuerKey": cakey,
        "serial": int(time.time()),
        "notBefore": 0,
        "notAfter": 60 * 60 * 24 * 365 * 10,  # ten years
        "digest": "sha256",
    }
    # Create the CA Certificate
    params["issuerCert"] = createCertificate(**params)

    pkey = createKeyPair(TYPE_RSA, 4096)
    params["req"] = createCertRequest(pkey, CN="SickChill")
    cert = createCertificate(**params)

    # Save the key and certificate to disk
    # noinspection PyBroadException
    try:
        # Module has no member
        open(ssl_key, "wb").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        open(ssl_cert, "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except Exception as error:
        logger.info(traceback.format_exc())
        logger.warning(_("Error creating SSL key and certificate {error}").format(error))
        return False

    logger.info(_("Created https key: {ssl_key}").format(ssl_key=ssl_key))
    logger.info(_("Created https cert: {ssl_cert}").format(ssl_cert=ssl_cert))
    return True


def backupVersionedFile(old_file, version):
    """
    Back up an old version of a file

    :param old_file: Original file, to take a backup from
    :param version: Version of file to store in backup
    :return: True if success, False if failure
    """

    numTries = 0

    new_file = old_file + "." + "v" + str(version)

    while not os.path.isfile(new_file):
        if not os.path.isfile(old_file):
            logger.debug(_("Not creating backup, {0} doesn't exist").format(old_file))
            break

        try:
            logger.debug(_("Trying to back up {0} to {1}").format(old_file, new_file))
            shutil.copy(old_file, new_file)
            logger.debug(_("Backup done"))
            break
        except Exception as error:
            logger.warning(_("Error while trying to back up {0} to {1} : {2}").format(old_file, new_file, error))
            numTries += 1
            time.sleep(1)
            logger.debug(_("Trying again."))

        if numTries >= 10:
            logger.exception(_("Unable to back up {0} to {1} please do it manually.").format(old_file, new_file))
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

    new_file, ext_ = os.path.splitext(backup_file)
    restore_file = new_file + "." + "v" + str(version)

    if not os.path.isfile(new_file):
        logger.debug(_("Not restoring, {0} doesn't exist").format(new_file))
        return False

    try:
        logger.debug(_("Trying to backup {0} to {1}.r{2} before restoring backup").format(new_file, new_file, version))

        shutil.move(new_file, new_file + "." + "r" + str(version))
    except Exception as error:
        logger.warning(_("Error while trying to backup DB file {0} before proceeding with restore: {1}").format(restore_file, error))
        return False

    while not os.path.isfile(new_file):
        if not os.path.isfile(restore_file):
            logger.debug(_("Not restoring, {0} doesn't exist").format(restore_file))
            break

        try:
            logger.debug(_("Trying to restore file {0} to {1}").format(restore_file, new_file))
            shutil.copy(restore_file, new_file)
            logger.debug(_("Restore done"))
            break
        except Exception as error:
            logger.warning(_("Error while trying to restore file {0}. Error: {1}").format(restore_file, error))
            numTries += 1
            time.sleep(1)
            logger.debug(_("Trying again. Attempt #: {0}").format(numTries))

        if numTries >= 10:
            logger.warning(_("Unable to restore file {0} to {1}").format(restore_file, new_file))
            return False

    return True


def get_lan_ip():
    """Returns IP of system"""

    # noinspection PyBroadException
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
        # noinspection PyTypeChecker
        handle_requests_exception(error)
        return False
    return True


def anon_url(*url):
    """
    Return a URL string consisting of the Anonymous redirect URL and an arbitrary number of values appended.
    """
    return "" if None in url else f"{settings.ANON_REDIRECT}{''.join(str(s) for s in url)}"


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
def encrypt(data: str, encryption_version=0, _decrypt=False):
    if not data:
        return ""

    if isinstance(data, str):
        data = data.encode()

    result = data
    secret_cycle = cycle((unique_key1, settings.ENCRYPTION_SECRET)[encryption_version > 1].encode())
    if encryption_version in (1, 2):
        if _decrypt:
            result = "".join(chr(x ^ y) for (x, y) in zip(base64.decodebytes(data), secret_cycle))
        else:
            result = base64.encodebytes("".join(chr(x ^ y) for (x, y) in zip(data, secret_cycle)).encode()).decode().strip()

    if isinstance(result, bytes):
        result = result.decode()

    return result


def decrypt(data, encryption_version=0):
    return encrypt(data, encryption_version, _decrypt=True)


def full_sanitizeSceneName(name):
    return re.sub("[. -]", " ", sanitizeSceneName(name)).lower().strip()


def _check_against_names(nameInQuestion, show, season=-1):
    showNames = []
    if season in [-1, 1]:
        showNames = [show.name]

    showNames.extend(sickchill.oldbeard.scene_exceptions.get_scene_exceptions(show.indexerid, season=season))

    for showName in showNames:
        nameFromList = full_sanitizeSceneName(showName)
        if nameFromList == nameInQuestion:
            return True

    return False


def get_show(name, tryIndexers=False):
    if not settings.showList:
        return

    showObj = None
    fromCache = False

    if not name:
        return showObj

    try:
        # check cache for show
        cache = sickchill.oldbeard.name_cache.get_id_from_name(name)
        if cache:
            fromCache = True
            showObj = Show.find(settings.showList, int(cache))
        else:
            check_names = [full_sanitizeSceneName(name), name]
            show_matches = [
                show
                for show in settings.showList
                if (show.show_name and full_sanitizeSceneName(show.show_name) in check_names)
                or (show.custom_name and full_sanitizeSceneName(show.custom_name) in check_names)
            ]

            if len(show_matches) == 1:
                showObj = show_matches[0]

        # try indexers
        if not showObj and tryIndexers:
            showObj = Show.find(settings.showList, sickchill.indexer.search_indexers_for_series_id(name=full_sanitizeSceneName(name))[1].id)

        # try scene exceptions
        if not showObj:
            scene_exceptions = sickchill.oldbeard.scene_exceptions.get_scene_exception_by_name_multiple(name)
            for scene_exception in scene_exceptions:
                if scene_exception[0]:
                    showObj = Show.find(settings.showList, scene_exception[0])
                    if showObj:
                        break

        # add show to cache
        if showObj and not fromCache:
            sickchill.oldbeard.name_cache.add_name(name, showObj.indexerid)
    except Exception as error:
        logger.debug(_("Error when attempting to find show: {0} in SickChill. Error: {1} ").format(name, error))
        logger.debug(traceback.format_exc())

    return showObj


def is_hidden_folder(folder):
    """
    Returns True if folder is hidden.
    On Linux based systems hidden folders start with . (dot)
    :param folder: Full path of folder to check
    """

    def is_hidden(filepath):
        name = os.path.basename(os.path.abspath(filepath))
        return name == "@eaDir" or name.startswith(".") or has_hidden_attribute(filepath)

    def has_hidden_attribute(filepath):
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(ctypes.c_wchar_p(str(filepath)))
            assert attrs != -1
            result = bool(attrs & 2)
        except (AttributeError, AssertionError, OSError, IOError):
            result = False
        return result

    if os.path.isdir(folder) and is_hidden(folder):
        return True

    return False


def real_path(path):
    """
    Returns: the canonicalized absolute pathname. The resulting path will have no symbolic link, '/./' or '/../' components.
    """
    return os.path.normpath(os.path.normcase(os.path.realpath(path)))


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


def set_up_anidb_connection():
    """Connect to anidb"""

    if not settings.USE_ANIDB:
        logger.debug(_("Usage of anidb disabled. Skiping"))
        return False

    if not settings.ANIDB_USERNAME and not settings.ANIDB_PASSWORD:
        logger.debug(_("anidb username and/or password are not set. Aborting anidb lookup."))
        return False

    if not settings.ADBA_CONNECTION:

        def anidb_logger(msg):
            return logger.debug(_("anidb: {0} ").format(msg))

        try:
            settings.ADBA_CONNECTION = adba.Connection(keep_alive=True, log=anidb_logger)
        except Exception as error:
            logger.warning(_("anidb exception msg: {0} ").format(error))
            return False

    try:
        if not settings.ADBA_CONNECTION.authed():
            settings.ADBA_CONNECTION.auth(settings.ANIDB_USERNAME, settings.ANIDB_PASSWORD)
        else:
            return True
    except Exception as error:
        logger.warning(_("anidb exception msg: {0} ").format(error))
        return False

    return settings.ADBA_CONNECTION.authed()


def makeZip(fileList, archive):
    """
    Create a ZIP of files

    :param fileList: A list of file names - full path each name
    :param archive: File name for the archive with a full path
    """

    try:
        a = zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
        for f in fileList:
            a.write(f)
        a.close()
        return True
    except Exception as error:
        logger.exception(_("Zip creation error: {0} ").format(error))
        return False


def extractZip(archive, targetDir):
    """
    Unzip a file to a directory

    :param archive: The file name of the archive to extract with a full path
    :param targetDir: The full path to the extraction target directory
    """

    try:
        if not os.path.exists(targetDir):
            os.mkdir(targetDir)

        zip_file = zipfile.ZipFile(archive, "r", allowZip64=True)
        for member in zip_file.namelist():
            filename = os.path.basename(member)
            # skip directories
            if not filename:
                continue

            # copy file (taken from zipfile's extract)
            source = zip_file.open(member)
            target = open(os.path.join(targetDir, filename), "wb")
            shutil.copyfileobj(source, target)
            source.close()
            target.close()
        zip_file.close()
        return True
    except Exception as error:
        logger.exception(_("Zip extraction error: {0} ").format(error))
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
        a = zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED)
        for f in fileList:
            a.write(f, os.path.relpath(f, arcname))
        a.close()
        return True
    except Exception as error:
        logger.warning(_("Zip creation error: {0} ").format(error))
        return False


def restore_config_zip(archive, targetDir):
    """
    Restores a Config ZIP file back in place

    :param archive: ZIP filename
    :param targetDir: Directory to restore to
    :return: True on success, False on failure
    """

    try:
        if not os.path.exists(targetDir):
            os.mkdir(targetDir)
        else:

            def path_leaf(path):
                head, tail = os.path.split(path)
                return tail or os.path.basename(head)

            bakFilename = "{0}-{1}".format(path_leaf(targetDir), datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
            shutil.move(targetDir, os.path.join(os.path.dirname(targetDir), bakFilename))

        zip_file = zipfile.ZipFile(archive, "r", allowZip64=True)
        for member in zip_file.namelist():
            zip_file.extract(member, targetDir)
        zip_file.close()
        return True
    except Exception as error:
        logger.exception(_("Zip extraction error: {0}").format(error))
        shutil.rmtree(targetDir)
        return False


def touchFile(fname, atime=None):
    """
    Touch a file (change modification date)

    :param fname: Filename to touch
    :param atime: Specific access time (defaults to None)
    :return: True on success, False on failure
    """

    if atime and fname and os.path.isfile(fname):
        os.utime(fname, (atime, atime))
        return True

    return False


def make_indexer_session():
    session = make_session()
    session.verify = (False, certifi.where())[settings.SSL_VERIFY]
    if settings.PROXY_SETTING and settings.PROXY_INDEXERS:
        logger.debug(_("Using global proxy for indexers: {}").format(settings.PROXY_SETTING))
        session.proxies = {"http": settings.PROXY_SETTING, "https": settings.PROXY_SETTING}
    return session


def make_session():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip,deflate"})
    session = cloudscraper.create_scraper(sess=session, delay=6)
    return CacheControl(sess=session, cache_etags=True)


def request_defaults(kwargs):
    verify = certifi.where() if all([settings.SSL_VERIFY, kwargs.pop("verify", True)]) else False

    # request session proxies
    if kwargs.pop("allow_proxy", True) and settings.PROXY_SETTING:
        logger.debug(_("Using global proxy: {}").format(settings.PROXY_SETTING))
        proxies = {"http": settings.PROXY_SETTING, "https": settings.PROXY_SETTING}
    else:
        proxies = None

    return kwargs.pop("hooks", None), kwargs.pop("cookies", None), verify, proxies


def getURL(
    url,
    post_data=None,
    params=None,
    headers=None,  # pylint:disable=too-many-arguments, too-many-return-statements, too-many-branches, too-many-locals
    timeout=30,
    session=None,
    **kwargs,
):
    """
    Returns data retrieved from the url provider.
    """
    try:
        response_type = kwargs.pop("returns", "text")
        stream = kwargs.pop("stream", False)
        allow_redirects = kwargs.pop("allow_redirects", True)

        hooks, cookies, verify, proxies = request_defaults(kwargs)

        resp = session.request(
            "POST" if post_data else "GET",
            url,
            data=post_data or {},
            params=params or {},
            timeout=timeout,
            allow_redirects=allow_redirects,
            hooks=hooks,
            stream=stream,
            headers=headers,
            cookies=cookies,
            proxies=proxies,
            verify=verify,
        )
        resp.raise_for_status()
    except Exception as error:
        # noinspection PyTypeChecker
        handle_requests_exception(error)
        return None

    try:
        return resp if response_type == "response" or response_type is None else resp.json() if response_type == "json" else getattr(resp, response_type, resp)
    except ValueError:
        logger.debug(_("Requested a json response but response was not json, check the url: {0}").format(url))
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

    return_filename = kwargs.get("return_filename", False)

    try:
        hooks, cookies, verify, proxies = request_defaults(kwargs)

        with closing(
            session.get(url, allow_redirects=True, stream=True, verify=verify, headers=headers, cookies=cookies, hooks=hooks, proxies=proxies)
        ) as resp:

            resp.raise_for_status()

            # Workaround for jackett.
            if filename.endswith("nzb") and resp.headers.get("content-type") == "application/x-bittorrent":
                filename = replace_extension(filename, "torrent")

            try:
                with open(filename, "wb") as fp:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            fp.write(chunk)
                            fp.flush()

                chmodAsParent(filename)
            except Exception as error:
                logger.warning(_("Problem downloading file, setting permissions or writing file to {0} - ERROR: {1}").format(filename, error))

    except Exception as error:
        # noinspection PyTypeChecker
        handle_requests_exception(error)
        return False if not return_filename else ""

    return True if not return_filename else filename


def handle_requests_exception(requests_exception):
    def get_level(exception):
        return (logger.ERROR, logger.WARNING)[exception and "s,t,o,p,b,r,e,a,k,i,n,g,f" in str(exception)]

    default = _("Request failed: {0} ({1})")
    try:
        raise requests_exception
    except requests.exceptions.SSLError as error:
        if ssl.OPENSSL_VERSION_INFO < (1, 0, 1, 5):
            logger.info(_("SSL Error requesting url: '{0}' You have {1}, try upgrading OpenSSL to 1.0.1e+").format(error.request.url, ssl.OPENSSL_VERSION))
        if settings.SSL_VERIFY:
            logger.info(_("SSL Error requesting url: '{0}' Try disabling Cert Verification on the advanced tab of /config/general").format(error.request.url))
        logger.debug(default.format(error, type(error.__class__.__name__)))
        logger.debug(traceback.format_exc())
    except requests.exceptions.ContentDecodingError as error:
        logger.info(default.format(error, type(error.__class__.__name__)))
        logger.debug(traceback.format_exc())
    except urllib3.exceptions.ProxySchemeUnknown as error:
        logger.info(default.format("You must prefix your proxy setting with a scheme (http/https/etc)", error))
    except CloudflareException as error:
        logger.info(default.format(error, type(error.__class__.__name__)))
    except requests.exceptions.RequestException as error:
        if not (
            hasattr(error, "response")
            and error.response
            and hasattr(error.response, "status_code")
            and error.response.status_code == 404
            and hasattr(error.response, "headers")
            and error.response.headers.get("X-Content-Type-Options") == "nosniff"
        ):
            logger.info(default.format(error, type(error.__class__.__name__)))
    except (TypeError, ValueError) as error:
        level = get_level(error)
        logger.log(level, default.format(error, type(error.__class__.__name__)))
        if requests_exception.request:
            logger.info(_("url is {0}").format(repr(requests_exception.request.url)))
            logger.info("headers are {0}".format(repr(requests_exception.request.headers)))
            logger.info("params are {0}".format(repr(requests_exception.request.params)))
            logger.info("post_data is {0}".format(repr(requests_exception.request.data)))
        if level == logger.WARNING:
            logger.debug(traceback.format_exc())
    except Exception as error:
        logger.log(get_level(error), default.format(error, type(error.__class__.__name__)))
        logger.debug(traceback.format_exc())


def get_size(start_path="."):
    """
    Find the total dir and filesize of a path

    :param start_path: Path to recursively count size
    :return: total filesize
    """

    if not os.path.isdir(start_path):
        return -1

    total_size = 0
    for dirpath, dirnames_, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.islink(fp) and not os.path.isfile(fp):
                log = logger.debug if settings.IGNORE_BROKEN_SYMLINKS else logger.warning
                log(_("Unable to get size for file {0} because the link to the file is not valid").format(fp))
                continue
            try:
                total_size += os.path.getsize(fp)
            except OSError as error:
                logger.exception(_("Unable to get size for file {0} Error: {1}").format(fp, error))
                logger.debug(traceback.format_exc())
    return total_size


def generateApiKey():
    """ Return a new randomized API_KEY"""
    logger.info(_("Generating New API key"))
    secure_hash = hashlib.sha512(str(time.time()).encode())
    secure_hash.update(str(random.SystemRandom().getrandbits(4096)).encode())
    return secure_hash.hexdigest()[:32]


def remove_article(text=""):
    """Remove the english articles from a text string"""

    return re.sub(r"(?i)^(?:(?:A(?!\s+to)n?)|The)\s(\w)", r"\1", text)


def generateCookieSecret():
    """Generate a new cookie secret"""

    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).decode()


def disk_usage(path):
    if platform.system() == "Windows":
        free = ctypes.c_ulonglong(0)
        if ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(str(path)), None, None, ctypes.pointer(free)) == 0:
            raise ctypes.WinError()
        return free.value

    elif hasattr(os, "statvfs"):  # POSIX
        if platform.system() == "Darwin":
            try:
                import subprocess

                call = subprocess.Popen(["df", "-k", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                output = call.communicate()[0]
                return int(output.split("\n")[1].split()[3]) * 1024
            except Exception:
                pass

        st = os.statvfs(path)
        return st.f_bavail * st.f_frsize

    else:
        raise Exception("Unable to determine free space on your OS")


def verify_freespace(src, dest, oldfile=None, method="copy"):
    """
    Checks if the target system has enough free space to copy or move a file.

    :param src: Source filename
    :param dest: Destination path (show dir in current usage)
    :param oldfile: File to be replaced (defaults to None)
    :param method: The post processing method
    :return: True if there is enough space for the file, False if there isn't. Also returns True if the OS doesn't support this option
    """

    if not isinstance(oldfile, list):
        oldfile = [oldfile] if oldfile else []

    logger.debug(_("Trying to determine free space on the destination drive"))

    if not os.path.isfile(src):
        logger.warning(_("A path to a file is required for the source. {0} is not a file.").format(src))
        return True

    if not (os.path.isdir(dest) or (settings.CREATE_MISSING_SHOW_DIRS and os.path.isdir(os.path.dirname(dest)))):
        logger.warning(
            _("A path is required for the destination. Check that the root dir and show locations are correct for {0} (I got '{1}')").format(
                oldfile[0].name, dest
            )
        )
        return False

    dest = (os.path.dirname(dest), dest)[os.path.isdir(dest)]

    # shortcut: if we are moving the file and the destination == src dir,
    # then by definition there is enough space
    if method == "move" and os.stat(src).st_dev == os.stat(dest).st_dev:  # pylint:
        # disable=no-member
        logger.info(_("Process method is 'move' and src and destination are on the same device, skipping free space check"))
        return True

    try:
        disk_free = disk_usage(dest)
    except Exception as error:
        logger.warning(_("Unable to determine free space, so I will assume there is enough."))
        logger.debug(_("Error: {error}").format(error=error))
        logger.debug(traceback.format_exc())
        return True

    # Lets also do this for symlink and hardlink
    if "link" in method and disk_free > 1024 ** 2:
        return True

    needed_space = os.path.getsize(src)

    if oldfile:
        for f in oldfile:
            if os.path.isfile(f.location):
                disk_free += os.path.getsize(f.location)

    if disk_free > needed_space:
        return True
    else:
        logger.warning(
            _("Not enough free space: Needed: {0} bytes ( {1} ), found: {2} bytes ( {3} )").format(
                needed_space, pretty_file_size(needed_space), disk_free, pretty_file_size(disk_free)
            )
        )
        return False


def disk_usage_hr(diskPath=None):
    """
    returns the free space in human readable bytes for a given path or False if no path given
    :param diskPath: the filesystem path being checked
    """
    if diskPath and os.path.exists(diskPath):
        try:
            free = disk_usage(diskPath)
        except Exception as error:
            logger.warning(_("Unable to determine free space"))
            logger.debug(_("Error: {error}").format(error=error))
            logger.debug(traceback.format_exc())
        else:
            return pretty_file_size(free)

    return False


# https://gist.github.com/thatalextaylor/7408395
def pretty_time_delta(seconds):
    sign_string = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    time_delta = sign_string

    if days > 0:
        time_delta += "{0}d".format(days)
    if hours > 0:
        time_delta += "{0}h".format(hours)
    if minutes > 0:
        time_delta += "{0}m".format(minutes)
    if seconds > 0:
        time_delta += "{0}s".format(seconds)

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

    checkfile = os.path.abspath(checkfile)

    if not os.path.exists(checkfile):
        return True
    try:
        f = open(checkfile, "rb")
        f.close()
    except IOError:
        return True

    if write_check:
        lockFile = checkfile + ".lckchk"
        if os.path.exists(lockFile):
            os.remove(lockFile)
        try:
            os.rename(checkfile, lockFile)
            time.sleep(1)
            os.rename(lockFile, checkfile)
        except (OSError, IOError):
            return True

    return False


def tvdbid_from_remote_id(indexer_id, indexer):  # pylint:disable=too-many-return-statements

    session = make_session()
    tvdb_id = ""
    if indexer == "IMDB":
        url = "http://www.thetvdb.com/api/GetSeriesByRemoteID.php?imdbid={0}".format(indexer_id)
        data = getURL(url, session=session, returns="content")
        if data is None:
            return tvdb_id
        try:
            tree = ElementTree.fromstring(data)
            for show in tree.iter("Series"):
                tvdb_id = show.findtext("seriesid")

        except SyntaxError:
            pass

        return tvdb_id
    elif indexer == "ZAP2IT":
        url = "http://www.thetvdb.com/api/GetSeriesByRemoteID.php?zap2it={0}".format(indexer_id)
        data = getURL(url, session=session, returns="content")
        if data is None:
            return tvdb_id
        try:
            tree = ElementTree.fromstring(data)
            for show in tree.iter("Series"):
                tvdb_id = show.findtext("seriesid")

        except SyntaxError:
            pass

        return tvdb_id
    elif indexer == "TVMAZE":
        url = "http://api.tvmaze.com/shows/{0}".format(indexer_id)
        data = getURL(url, session=session, returns="json")
        if data is None:
            return tvdb_id
        tvdb_id = data["externals"]["thetvdb"]
        return tvdb_id
    else:
        return tvdb_id


def is_ip_local(ip):
    request_ip = ipaddress.ip_address(ip)
    if request_ip.is_private:
        return True

    for adapter in ifaddr.get_adapters():
        for aip in adapter.ips:
            if isinstance(aip.ip, tuple):
                network = ipaddress.IPv6Network("%s/%s" % (aip.ip[0], aip.network_prefix), strict=False)
            else:
                network = ipaddress.IPv4Network("%s/%s" % (aip.ip, aip.network_prefix), strict=False)

            if request_ip in network:
                return True
    return False


MESSAGE_COUNTER = 0


def add_site_message(message, tag=None, level="danger"):
    with settings.MESSAGES_LOCK:
        to_add = dict(level=level, tag=tag, message=message)

        if tag:  # prevent duplicate messages of the same type
            # http://www.goodmami.org/2013/01/30/Getting-only-the-first-match-in-a-list-comprehension.html
            existing = next((x for x, msg in settings.SITE_MESSAGES.items() if msg.get("tag") == tag), None)
            if existing:
                settings.SITE_MESSAGES[existing] = to_add
                return

        global MESSAGE_COUNTER
        MESSAGE_COUNTER += 1
        settings.SITE_MESSAGES[MESSAGE_COUNTER] = to_add


def remove_site_message(key=None, tag=None):
    with settings.MESSAGES_LOCK:
        if key is not None and int(key) in settings.SITE_MESSAGES:
            del settings.SITE_MESSAGES[int(key)]
        elif tag is not None:
            found = [idx for idx, msg in settings.SITE_MESSAGES.items() if msg.get("tag") == tag]
            for key in found:
                del settings.SITE_MESSAGES[key]


def sortable_name(name):
    if not settings.SORT_ARTICLE:
        name = re.sub(r"(?:The|A|An)\s", "", name, flags=re.I)
    return unidecode(name.lower())


def manage_torrents_url(reset=False):
    if not reset:
        return settings.CLIENT_WEB_URLS.get("torrent", "")

    if (
        not settings.USE_TORRENTS
        or not settings.TORRENT_HOST.lower().startswith("http")
        or settings.TORRENT_METHOD == "blackhole"
        or settings.ENABLE_HTTPS
        and not settings.TORRENT_HOST.lower().startswith("https")
    ):
        settings.CLIENT_WEB_URLS["torrent"] = ""
        return settings.CLIENT_WEB_URLS.get("torrent")

    torrent_ui_url = re.sub("localhost|127.0.0.1", settings.LOCALHOST_IP or get_lan_ip(), settings.TORRENT_HOST or "", re.I)

    def test_exists(url):
        try:
            h = requests.head(url)
            return h.status_code != 404
        except requests.exceptions.RequestException:
            return False

    if settings.TORRENT_METHOD == "utorrent":
        torrent_ui_url = "/".join(s.strip("/") for s in (torrent_ui_url, "gui/"))
    elif settings.TORRENT_METHOD == "download_station":
        if test_exists(urljoin(torrent_ui_url, "download/")):
            torrent_ui_url = urljoin(torrent_ui_url, "download/")

    settings.CLIENT_WEB_URLS["torrent"] = ("", torrent_ui_url)[test_exists(torrent_ui_url)]

    return settings.CLIENT_WEB_URLS.get("torrent")


def is_docker():
    path = "/proc/self/cgroup"
    return os.path.exists("/.dockerenv") or os.path.isfile(path) and any("docker" in line for line in open(path))
