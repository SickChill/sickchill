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
from pathlib import Path
from typing import Union
from urllib.parse import urljoin
from urllib.request import HTTPSHandler
from xml.etree import ElementTree

import certifi
import ifaddr
import requests
import urllib3.exceptions
from cachecontrol import CacheControl
from tornado._locale_data import LOCALE_NAMES
from unidecode import unidecode
from urllib3 import disable_warnings

import sickchill
from sickchill import adba, logger, settings
from sickchill.helper import episode_num, pretty_file_size, SUBTITLE_EXTENSIONS
from sickchill.helper.common import is_media_file, replace_extension
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
        context = ssl.create_default_context(cafile=certifi.where())
        context.options &= ~ssl.OP_NO_SSLv3
        # context.options |= ssl.OP_NO_SSLv2
        context.check_hostname = verify or None
        context.verify_mode = (ssl.CERT_NONE, ssl.CERT_REQUIRED)[bool(verify)]
        _context = context
    return _context


def set_opener(verify: bool):
    disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    https_handler = HTTPSHandler(context=make_context(verify))
    opener = urllib.request.build_opener(https_handler)
    opener.addheaders = [("User-agent", sickchill.oldbeard.common.USER_AGENT)]
    urllib.request.install_opener(opener)


set_opener(settings.SSL_VERIFY)

# Override original shutil function to increase its speed by increasing it's buffer to 10MB (optimal)
copyfileobj_orig = shutil.copyfileobj


def _copyfileobj(fsrc, fdst, length=10485760):
    """Run shutil.copyfileobj with a bigger buffer"""
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
            _name = re.sub(rf"(?i){remove_string}", "", _name)

    return _name.strip()


def remove_file_failed(failed_file):
    """
    Remove file from filesystem

    Parameters:
        failed_file: File to remove
    """

    # noinspection PyBroadException
    try:
        os.remove(failed_file)
    except Exception:
        pass


def makeDir(path):
    """
    Make a directory on the filesystem

    Parameters:
        path: directory to make
    Returns:
         True if success, False if failure
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

    Parameters:
        path: Path to check for files
    Returns:
         list of files
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

    Parameters:
        srcFile: Path of source file
        destFile: Path of destination file
    """

    try:
        shutil.copyfile(srcFile, destFile)
    except shutil.SameFileError:
        return
    except (shutil.SpecialFileError, shutil.Error) as error:
        logger.warning(f"There was a problem copying a file from {srcFile} to {destFile}. Error: {error}")
        raise error
    except Exception as error:
        logger.exception(f"There was a problem copying a file from {srcFile} to {destFile}. Error: {error}")
        raise error

    try:
        shutil.copymode(srcFile, destFile)
    except OSError:
        pass


def moveFile(srcFile, destFile):
    """
    Move a file from source to destination

    Parameters:
        srcFile: Path of source file
        destFile: Path of destination file
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

    Parameters:
        srcFile: Source file
        destFile: Destination file
    """

    try:
        if os.path.lexists(destFile):
            try:
                os.unlink(destFile)
            except (OSError, IOError) as error:
                logger.log(
                    _(
                        "The destination file already exists, and we were unable to remove it, so hard linking might fail. Trying anyway. Location: {destFile}. Error: {error}"
                    ).format(destFile=destFile, error=error),
                )
        os.link(srcFile, destFile)
    except Exception as error:
        logger.warning(
            _("There was a problem creating a hardlink of {srcFile} at {destFile}. Copying instead. Error: {error}").format(
                srcFile=srcFile, destFile=destFile, error=error
            )
        )
        copyFile(srcFile, destFile)

    fixSetGroupID(destFile)


def moveAndSymlinkFile(srcFile, destFile):
    """
    Move a file from source to destination, then create a symlink back from destination from source. If this fails, copy
    the file from source to destination

    Parameters:
        srcFile: Source file
        destFile: Destination file
    """

    try:
        moveFile(srcFile, destFile)
        os.symlink(destFile, srcFile)
    except Exception as error:
        logger.warning(
            _("There was a problem creating a symlink of {srcFile} at {destFile}. Copying instead. Error: {error}").format(
                srcFile=srcFile, destFile=destFile, error=error
            )
        )
        copyFile(srcFile, destFile)


def make_dirs(path):
    """
    Creates any folders that are missing and assigns them the permissions of their
    parents
    """

    logger.debug(_("Checking if the path {path} already exists").format(path=path))

    if not os.path.isdir(path):
        # Windows, create all missing folders
        if platform.system() == "Windows":
            try:
                logger.debug(_("Folder {path} didn't exist, creating it").format(path=path))
                os.makedirs(path)
            except (OSError, IOError) as error:
                logger.exception(_("There was a problem creating {path}. Error: {error}").format(path=path, error=error))
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
                    logger.debug(_("Folder {sofar} didn't exist, creating it").format(sofar=sofar))
                    os.mkdir(sofar)
                    # use normpath to remove end separator, otherwise checks permissions against itself
                    chmodAsParent(os.path.normpath(sofar))
                    # do the library update for synoindex
                    sickchill.oldbeard.notifiers.synoindex_notifier.addFolder(sofar)
                except (OSError, IOError) as error:
                    logger.exception(_("There was a problem creating {sofar}. Error: {error}").format(sofar=sofar, error=error))
                    return False

    return True


def rename_ep_file(cur_path, new_path, old_path_length=0):
    """
    Creates all folders needed to move a file to its new location, renames it, then cleans up any folders
    left that are now empty.

    Parameters:
        cur_path: The absolute path to the file you want to move/rename
        new_path: The absolute path to the destination for the file WITHOUT THE EXTENSION
        old_path_length: The length of media file path (old name) WITHOUT THE EXTENSION
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
        logger.info(_("Renaming file from {cur_path} to {new_path}").format(cur_path=cur_path, new_path=new_path))
        shutil.move(cur_path, new_path)
    except (OSError, IOError) as error:
        logger.exception(_("There was a problem renaming {cur_path} to {new_path}. Error: {error}").format(cur_path=cur_path, new_path=new_path, error=error))
        return False

    # clean up any old folders that are empty
    delete_empty_folders(os.path.dirname(cur_path))

    return True


def delete_empty_folders(check_empty_dir, keep_dir=None):
    """
    Walks backwards up the path and deletes any empty folders found.

    Parameters:
        check_empty_dir: The path to clean (absolute path to a folder)
        keep_dir: Clean until this path is reached
    """

    # treat check_empty_dir as empty when it only contains these items
    ignore_items = []

    logger.info(_("Trying to clean any empty folders under {check_empty_dir}").format(check_empty_dir=check_empty_dir))

    # as long as the folder exists and doesn't contain any files, delete it
    while os.path.isdir(check_empty_dir) and check_empty_dir != keep_dir:
        check_files = os.listdir(check_empty_dir)

        if not check_files or (len(check_files) <= len(ignore_items) and all(check_file in ignore_items for check_file in check_files)):
            # directory is empty or contains only ignore_items
            try:
                logger.info(_("Deleting empty folder: {check_empty_dir}").format(check_empty_dir=check_empty_dir))
                # need shutil.rmtree when ignore_items is really implemented
                os.rmdir(check_empty_dir)
                # do the library update for synoindex
                sickchill.oldbeard.notifiers.synoindex_notifier.deleteFolder(check_empty_dir)
            except OSError as error:
                logger.warning(_("There was a problem trying to delete {check_empty_dir}. Error: {error}").format(check_empty_dir=check_empty_dir, error=error))
                break
            check_empty_dir = os.path.dirname(check_empty_dir)
        else:
            break


def fileBitFilter(mode):
    """
    Strip special filesystem bits from file

    Parameters:
        mode: mode to check and strip
    Returns:
         required mode for media file
    """

    for bit in [stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH, stat.S_ISUID, stat.S_ISGID]:
        if mode & bit:
            mode -= bit

    return mode


def chmodAsParent(childPath):
    """
    Retain permissions of parent for childs
    (Does not work for Windows hosts)

    Parameters:
        childPath: Child Path to change permissions to sync from parent
    """

    if platform.system() == "Windows":
        return

    parentPath = os.path.dirname(childPath)

    if not parentPath:
        logger.debug(_("No parent path provided in {childPath} unable to get permissions from it").format(childPath=childPath))
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
        logger.debug(_("Not running as root or owner of {childPath}, not trying to set permissions").format(childPath=childPath))
        return

    try:
        os.chmod(childPath, childMode)
    except OSError as error:
        logger.debug(
            _("There was a problem setting permissions of {childPath} to {childMode:o}, parent directory has {parentMode:o}. Error: {error}").format(
                childPath=childPath, childMode=childMode, parentMode=parentMode, error=error
            )
        )


def fixSetGroupID(childPath):
    """
    Inherid SGID from parent
    (does not work on Windows hosts)

    Parameters:
        childPath: Path to inherit SGID permissions from parent
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
                logger.debug(_("Not running as root or owner of {childPath}, not trying to set the set-group-ID").format(childPath=childPath))
                return

            try:
                os.chown(childPath, -1, parentGID)
                logger.debug(_("Respecting the set-group-ID bit on the parent directory of {childPath}").format(childPath=childPath))
            except (OSError, PermissionError) as error:
                logger.debug(
                    _(
                        "There was a problem respecting the set-group-ID bit on the parent directory of {childPath} (setting group ID {parentGID}). Error: {error}"
                    ).format(childPath=childPath, parentGID=parentGID, error=error)
                )
    except Exception as error:
        logger.debug(
            _("There was a problem setting set-group-id on the parent directory of {childPath}. Error: {error}").format(childPath=childPath, error=error)
        )


def is_anime_in_show_list():
    """
    Check if any shows in list contain anime

    Returns:
         True if global showlist contains Anime, False if not
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

    Parameters:
        show: Show object
        season: Season number
        episode: Episode number
    Returns:
         The absolute number
    """

    absolute_number = None

    if season and episode:
        main_db_con = db.DBConnection()
        sql = "SELECT * FROM tv_episodes WHERE showid = ? and season = ? and episode = ?"
        sql_results = main_db_con.select(sql, [show.indexerid, season, episode])
        season_episode = episode_num(season, episode)
        if len(sql_results) == 1:
            absolute_number = int(sql_results[0]["absolute_number"])
            logger.debug(
                _("Found absolute number {absolute_number} for show {show_name} {season_episode}").format(
                    absolute_number=absolute_number, show_name=show.name, season_episode=season_episode
                )
            )
        else:
            logger.debug(
                _("No entries found for the absolute number of {show_name} {season_episode}").format(show_name=show.name, season_episode=season_episode)
            )

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
    Parameters:
        name: The name to sanitize
        anime: Some show have a single quote in their name(Kuroko's Basketball) and is needed for search.
    Returns:
         A string containing the scene version of the show name given.
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
    name = re.sub(r"[-/…\s]+", ".", name)
    name = re.sub(r"[.]+", ".", name)

    if name.endswith("."):
        name = name[:-1]

    return name


def create_https_certificates(ssl_cert, ssl_key):
    """
    Create self-signed HTTPS certificares and store in paths 'ssl_cert' and 'ssl_key'

    Parameters:
        ssl_cert: Path of SSL certificate file to write
        ssl_key: Path of SSL keyfile to write
    Returns:
         True on success, False on failure
    """

    try:
        from OpenSSL import crypto

        from sickchill.certgen import createCertificate, createCertRequest, createKeyPair, TYPE_RSA
    except (ModuleNotFoundError):
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
        Path(ssl_key).write_bytes(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        Path(ssl_cert).write_bytes(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except Exception as error:
        logger.info(traceback.format_exc())
        logger.warning(_("There was a problem creating the SSL key and certificate. Error: {error}").format(error=error))
        return False

    logger.info(_("Created https key: {ssl_key}").format(ssl_key=ssl_key))
    logger.info(_("Created https cert: {ssl_cert}").format(ssl_cert=ssl_cert))
    return True


def backupVersionedFile(old_file, version):
    """
    Back up an old version of a file

    Parameters:
        old_file: Original file, to take a backup from
        version: Version of file to store in backup
    Returns:
         True if success, False if failure
    """

    numTries = 0

    if not isinstance(old_file, Path):
        old_file = Path(old_file)

    new_file = old_file.with_suffix(f"{old_file.suffix}.v{version}")
    while not os.path.isfile(new_file):
        if not os.path.isfile(old_file):
            logger.debug(_("Not creating backup, {old_file} doesn't exist").format(old_file=old_file))
            break

        try:
            logger.debug(_("Trying to back up {old_file} to {new_file}").format(old_file=old_file, new_file=new_file))
            shutil.copy(old_file, new_file)
            logger.debug(_("Backup done"))
            break
        except Exception as error:
            logger.warning(
                _("There was a problem while trying to back up {old_file} to {new_file}. Error: {error}").format(
                    old_file=old_file, new_file=new_file, error=error
                )
            )
            numTries += 1
            time.sleep(1)
            logger.debug(_("Trying again."))

        if numTries >= 10:
            logger.exception(_("Unable to back up {old_file} to {new_file} please do it manually.").format(old_file=old_file, new_file=new_file))
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
            result = sickchill.indexer.search_indexers_for_series_id(name=full_sanitizeSceneName(name))[1]
            if result:
                showObj = Show.find(settings.showList, result.id)

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
        logger.debug(_("There was a problem when attempting to find {name} in SickChill. Error: {error}").format(name=name, error=error))
        logger.debug(traceback.format_exc())

    return showObj


def is_hidden_folder(folder):
    """
    Returns True if folder is hidden.
    On Linux based systems hidden folders start with . (dot)
    Parameters:
        folder: Full path of folder to check
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
    Returns:
        the canonicalized absolute pathname. The resulting path will have no symbolic link, '/./' or '/../' components.
    """
    return os.path.normpath(os.path.normcase(os.path.realpath(path)))


def is_subdirectory(subdir_path, topdir_path):
    """
    Returns true if a subdir_path is a subdirectory of topdir_path
    else otherwise.

    Parameters:
        subdir_path: The full path to the subdirectory
        topdir_path: The full path to the top directory to check subdir_path against
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
            return logger.debug(_("{msg}").format(msg=msg))

        try:
            settings.ADBA_CONNECTION = adba.Connection(keep_alive=True, log=anidb_logger)
        except Exception as error:
            logger.warning(_("There was a problem attempting to connect to anidb. Error: {error}").format(error=error))
            return False

    try:
        if not settings.ADBA_CONNECTION.authed():
            settings.ADBA_CONNECTION.auth(settings.ANIDB_USERNAME, settings.ANIDB_PASSWORD)
        else:
            return True
    except Exception as error:
        logger.warning(_("There was a problem attempting to authenticate with anidb. Error: {error}").format(error=error))
        return False

    return settings.ADBA_CONNECTION.authed()


def makeZip(fileList, archive):
    """
    Create a ZIP of files

    Parameters:
        fileList: A list of file names - full path each name
        archive: File name for the archive with a full path
    """

    try:
        a = zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
        for f in fileList:
            a.write(f)
        a.close()
        return True
    except Exception as error:
        logger.exception(_("There was a problem creating the zip file. Error: {error}").format(error=error))
        return False


def extractZip(archive, targetDir):
    """
    Unzip a file to a directory

    Parameters:
        archive: The file name of the archive to extract with a full path
        targetDir: The full path to the extraction target directory
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
        logger.exception(_("There was a problem extracting the zip file {archive}. Error: {error}").format(archive=archive, error=error))
        return False


def backup_config_zip(fileList, archive, arcname=None):
    """
    Store the config file as a ZIP

    Parameters:
        fileList: List of files to store
        archive: ZIP file name
        arcname: Archive path
    Returns:
         True on success, False on failure
    """

    try:
        a = zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED)
        for f in fileList:
            a.write(f, os.path.relpath(f, arcname))
        a.close()
        return True
    except Exception as error:
        logger.warning(_("There was a problem creating the zip file. Error: {error}").format(error=error))
        return False


def restore_config_zip(archive, targetDir):
    """
    Restores a Config ZIP file back in place

    Parameters:
        archive: ZIP filename
        targetDir: Directory to restore to
    Returns:
         True on success, False on failure
    """

    try:
        if not os.path.exists(targetDir):
            os.mkdir(targetDir)
        else:

            def path_leaf(path):
                head, tail = os.path.split(path)
                return tail or os.path.basename(head)

            base_backup_name = path_leaf(targetDir)
            date_time_string = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{base_backup_name}-{date_time_string}"
            shutil.move(targetDir, os.path.join(os.path.dirname(targetDir), backup_filename))

        zip_file = zipfile.ZipFile(archive, "r", allowZip64=True)
        for member in zip_file.namelist():
            zip_file.extract(member, targetDir)
        zip_file.close()
        return True
    except Exception as error:
        logger.exception(_("There was a problem extracting zip file {archive}. Error: {error}").format(archive=archive, error=error))
        shutil.rmtree(targetDir)
        return False


def touchFile(fname, atime=None):
    """
    Touch a file (change modification date)

    Parameters:
        fname: Filename to touch
        atime: Specific access time (defaults to None)
    Returns:
         True on success, False on failure
    """

    if atime and fname and os.path.isfile(fname):
        os.utime(fname, (atime, atime))
        return True

    return False


def make_indexer_session():
    session = make_session()
    session.verify = (False, certifi.where())[settings.SSL_VERIFY]
    if settings.PROXY_SETTING and settings.PROXY_INDEXERS:
        logger.debug(_("Using global proxy for indexers: {proxy_settings}").format(proxy_settings=settings.PROXY_SETTING))
        session.proxies = {"http": settings.PROXY_SETTING, "https": settings.PROXY_SETTING}
    return session


def make_session():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip,deflate"})
    return CacheControl(sess=session, cache_etags=True)


def request_defaults(kwargs):
    verify = certifi.where() if all([settings.SSL_VERIFY, kwargs.pop("verify", True)]) else False

    # request session proxies
    if kwargs.pop("allow_proxy", True) and settings.PROXY_SETTING:
        logger.debug(_("Using global proxy: {proxy}").format(proxy=settings.PROXY_SETTING))
        proxies = {"http": settings.PROXY_SETTING, "https": settings.PROXY_SETTING}
    else:
        proxies = None

    return kwargs.pop("hooks", None), kwargs.pop("cookies", None), verify, proxies


def getURL(
    url,
    post_data=None,
    params=None,
    headers=None,
    timeout=30,
    session: requests.Session = None,
    **kwargs,
) -> Union[requests.Response, dict]:
    """
    Returns data retrieved from the url provider.
    """
    try:
        response_type = kwargs.pop("returns", "text")
        stream = kwargs.pop("stream", False)
        allow_redirects = kwargs.pop("allow_redirects", True)

        hooks, cookies, verify, proxies = request_defaults(kwargs)

        flaresolverr = kwargs.pop("flaresolverr", False)
        if flaresolverr and settings.FLARESOLVERR_URI:
            if params:
                url = f"{url}?{urllib.parse.urlencode(params)}"

            fs_json = {"cmd": "request.get", "url": url, "userAgent": "Windows NT 10.0; Win64; x64) AppleWebKit/5...", "maxTimeout": 60000}

            if post_data:
                fs_json.update(cmd="request.post", postData=post_data)

            if cookies:
                fs_json.update(cookies=cookies)

            if proxies:
                fs_json.update(proxy=proxies)

            response = session.post(
                settings.FLARESOLVERR_URI,
                json=fs_json,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
                hooks=hooks,
                verify=False,
            )

            json_result = response.json()
            response.raise_for_status()
            session.cookies = json_result["solution"]["cookies"]
            session.headers = json_result["solution"]["headers"]
            return json_result["response"]

        response = session.request(
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
        response.raise_for_status()
    except Exception as error:
        handle_requests_exception(error)
        return None

    try:
        return response if response_type in ("response", None) else response.json() if response_type == "json" else getattr(response, response_type, response)
    except ValueError:
        logger.debug(_("Requested a json response but response was not json, check the url: {url}").format(url=url))
        return None


def download_file(url, filename, session=None, headers=None, **kwargs):  # pylint:disable=too-many-return-statements
    """
    Downloads a file specified

    Parameters:
        url: Source URL
        filename: the target file on the filesystem
        session: request session to use
        headers: override existing headers in request session
    Returns:
         True on success, False on failure
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
                logger.warning(
                    _("There was a problem downloading, setting permissions, or writing to {filename}. Error: {error}").format(filename=filename, error=error)
                )

    except Exception as error:
        # noinspection PyTypeChecker
        handle_requests_exception(error)
        return False if not return_filename else ""

    return True if not return_filename else filename


def handle_requests_exception(
    requests_exception: Union[
        Exception,
        TypeError,
        ValueError,
        "requests.exceptions.BaseHTTPError",
        "requests.exceptions.ChunkedEncodingError",
        "requests.exceptions.ConnectTimeout",
        "requests.exceptions.ConnectionError",
        "requests.exceptions.ContentDecodingError",
        "requests.exceptions.FileModeWarning",
        "requests.exceptions.HTTPError",
        "requests.exceptions.InvalidHeader",
        "requests.exceptions.InvalidJSONError",
        "requests.exceptions.InvalidProxyURL",
        "requests.exceptions.InvalidSchema",
        "requests.exceptions.InvalidURL",
        "requests.exceptions.MissingSchema",
        "requests.exceptions.ProxyError",
        "requests.exceptions.ReadTimeout",
        "requests.exceptions.RequestException",
        "requests.exceptions.RequestsDependencyWarning",
        "requests.exceptions.RequestsWarning",
        "requests.exceptions.RetryError",
        "requests.exceptions.SSLError",
        "requests.exceptions.StreamConsumedError",
        "requests.exceptions.Timeout",
        "requests.exceptions.TooManyRedirects",
        "requests.exceptions.URLRequired",
        "requests.exceptions.UnrewindableBodyError",
        "urllib3.exceptions.BodyNotHttplibCompatible",
        "urllib3.exceptions.ClosedPoolError",
        "urllib3.exceptions.ConnectTimeoutError",
        "urllib3.exceptions.ConnectionError",
        "urllib3.exceptions.DecodeError",
        "urllib3.exceptions.DependencyWarning",
        "urllib3.exceptions.EmptyPoolError",
        "urllib3.exceptions.HTTPError",
        "urllib3.exceptions.HTTPWarning",
        "urllib3.exceptions.HeaderParsingError",
        "urllib3.exceptions.HostChangedError",
        "urllib3.exceptions.IncompleteRead",
        "urllib3.exceptions.InsecurePlatformWarning",
        "urllib3.exceptions.InsecureRequestWarning",
        # "urllib3.exceptions.InvalidChunkLength",
        "urllib3.exceptions.InvalidHeader",
        "urllib3.exceptions.LocationParseError",
        "urllib3.exceptions.LocationValueError",
        "urllib3.exceptions.MaxRetryError",
        "urllib3.exceptions.NewConnectionError",
        "urllib3.exceptions.PoolError",
        "urllib3.exceptions.ProtocolError",
        "urllib3.exceptions.ProxyError",
        "urllib3.exceptions.ProxySchemeUnknown",
        "urllib3.exceptions.ProxySchemeUnsupported",
        "urllib3.exceptions.ReadTimeoutError",
        "urllib3.exceptions.RequestError",
        "urllib3.exceptions.ResponseError",
        "urllib3.exceptions.ResponseNotChunked",
        "urllib3.exceptions.SNIMissingWarning",
        "urllib3.exceptions.SSLError",
        "urllib3.exceptions.SecurityWarning",
        "urllib3.exceptions.SubjectAltNameWarning",
        "urllib3.exceptions.SystemTimeWarning",
        "urllib3.exceptions.TimeoutError",
        "urllib3.exceptions.TimeoutStateError",
        "urllib3.exceptions.URLSchemeUnknown",
        "urllib3.exceptions.UnrewindableBodyError",
        # "urllib3.exceptions.httplib_IncompleteRead",
    ]
):
    def get_level(exception):
        return (logger.ERROR, logger.WARNING)[exception and "s,t,o,p,b,r,e,a,k,i,n,g,f" in str(exception)]

    default = _("Request failed: {0} ({1})")

    def classname(error: Exception) -> str:
        return error.__class__.__name__

    try:
        raise requests_exception
    except requests.exceptions.SSLError as error:
        if ssl.OPENSSL_VERSION_INFO < (1, 0, 1, 5):
            logger.info(
                _("SSL Error requesting url: '{error.request.url}' You have {ssl.OPENSSL_VERSION}, try upgrading OpenSSL to 1.0.1e+. Error: {error}").format(
                    error=error, ssl=ssl
                )
            )
        if settings.SSL_VERIFY:
            logger.info(
                _(
                    "SSL Error requesting url: '{error.request.url}' Try disabling Cert Verification on the advanced tab of /config/general. Error: {error}"
                ).format(error=error)
            )
        logger.debug(default.format(error, classname(error)))
        logger.debug(traceback.format_exc())
    except requests.exceptions.ContentDecodingError as error:
        logger.info(default.format(error, classname(error)))
        logger.debug(traceback.format_exc())
    except urllib3.exceptions.ProxySchemeUnknown as error:
        logger.info(default.format("You must prefix your proxy setting with a scheme (http/https/etc)", error))
    except requests.exceptions.RequestException as error:
        if not (
            hasattr(error, "response")
            and error.response
            and hasattr(error.response, "status_code")
            and error.response.status_code == 404
            and hasattr(error.response, "headers")
            and error.response.headers.get("X-Content-Type-Options") == "nosniff"
        ):
            logger.info(default.format(error, classname(error)))
    except (TypeError, ValueError) as error:
        level = get_level(error)
        logger.log(level, default.format(error, classname(error)))
        if hasattr(requests_exception, "request") and requests_exception.request:
            logger.info(_("url is {requests_exception.request.url}").format(requests_exception=requests_exception))
            logger.info(_("headers are {requests_exception.request.headers}").format(requests_exception=requests_exception))
            logger.info(_("params are {requests_exception.request.params}").format(requests_exception=requests_exception))
            logger.info(_("post_data is {requests_exception.request.data}").format(requests_exception=requests_exception))
        if level == logger.WARNING:
            logger.debug(traceback.format_exc())
    except Exception as error:
        logger.log(get_level(error), default.format(error, classname(error)))
        logger.debug(traceback.format_exc())


def get_size(start_path="."):
    """
    Find the total dir and filesize of a path

    Parameters:
        start_path: Path to recursively count size
    Returns:
         total filesize
    """

    if not os.path.isdir(start_path):
        return -1

    total_size = 0
    for dirpath, dirnames_, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.islink(fp) and not os.path.isfile(fp):
                log = logger.debug if settings.IGNORE_BROKEN_SYMLINKS else logger.warning
                log(_("Unable to get size for file {fp} because the link to the file is not valid").format(fp=fp))
                continue
            try:
                total_size += os.path.getsize(fp)
            except OSError as error:
                logger.exception(_("Unable to get size for file {fp}. Error: {error}").format(fp=fp, error=error))
                logger.debug(traceback.format_exc())
    return total_size


def generateApiKey():
    """Return a new randomized API_KEY"""
    logger.info(_("Generating New API key"))
    secure_hash = hashlib.sha512(str(time.time()).encode())
    secure_hash.update(str(random.SystemRandom().getrandbits(4096)).encode())
    return secure_hash.hexdigest()[:32]


def remove_article(text=""):
    """Remove the english articles from a text string"""

    return re.sub(r"(?i)^(?:A(?!\s+to)n?|The)\s(\w)", r"\1", text)


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

    Parameters:
        src: Source filename
        dest: Destination path (show dir in current usage)
        oldfile: File to be replaced (defaults to None)
        method: The post-processing method
    Returns:
         True if there is enough space for the file, False if there isn't. Also returns True if the OS doesn't support this option
    """

    if not isinstance(oldfile, list):
        oldfile = [oldfile] if oldfile else []

    logger.debug(_("Trying to determine free space on the destination drive"))

    if not os.path.isfile(src):
        logger.warning(_("A path to a file is required for the source. {src} is not a file.").format(src=src))
        return True

    if not (os.path.isdir(dest) or (settings.CREATE_MISSING_SHOW_DIRS and os.path.isdir(os.path.dirname(dest)))):
        logger.warning(
            _("A path is required for the destination. Check that the root dir and show locations are correct for {old_file_name} (I got '{dest}')").format(
                old_file_name=oldfile[0].name, dest=dest
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

    # Let's also do this for symlink and hardlink
    if "link" in method and disk_free > 1024**2:
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
            _(
                "Not enough free space: Needed: {needed_space} bytes ( {pretty_file_size(needed_space)} ), found: {disk_free} bytes ( {pretty_file_size(disk_free)} )"
            ).format(needed_space=needed_space, disk_free=disk_free)
        )
        return False


def disk_usage_hr(diskPath=None):
    """
    returns the free space in human-readable bytes for a given path or False if no path given
    Parameters:
        diskPath: the filesystem path being checked
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
        time_delta += f"{days}d"
    if hours > 0:
        time_delta += f"{hours}h"
    if minutes > 0:
        time_delta += f"{minutes}m"
    if seconds > 0:
        time_delta += f"{seconds}s"

    return time_delta


def is_file_locked(checkfile, write_check=False):
    """
    Checks to see if a file is locked. Performs three checks
        1. Checks if the file even exists
        2. Attempts to open the file for reading. This will determine if the file has a write-lock.
            Write locks occur when the file is being edited or copied to, e.g. a file copy destination
        3. If the readLockCheck parameter is True, attempts to rename the file. If this fails the
            file is open by some other process for reading. The file can be read, but not written to
            or deleted.
    Parameters:
        checkfile: the file being checked
        write_check: when true will check if the file is locked for writing (prevents move operations)
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
        url = f"https://www.thetvdb.com/api/GetSeriesByRemoteID.php?imdbid={indexer_id}"
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
        url = f"https://www.thetvdb.com/api/GetSeriesByRemoteID.php?zap2it={indexer_id}"
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
        url = f"https://api.tvmaze.com/shows/{indexer_id}"
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


def get_exception_class_type_hint_string() -> None:
    """
    This is not used in code, just used for creating a type hint string for me to use above on handle_requests_exception
    """
    output = set()
    import requests.exceptions
    import urllib3.exceptions

    for location in (requests.exceptions, urllib3.exceptions):
        for item_string in dir(location):
            try:
                item = getattr(location, item_string)
                if type(item) == type(Exception) and issubclass(item, (IOError, Exception)):
                    output.add(f"{location.__name__}.{item_string}")
            except Exception as error:
                print(f"the error was by {item_string} with {error}")
    output = output.union({"TypeError", "ValueError", "Exception"})
    return print(f"Union{sorted(list(output))}".replace("'", "").replace(" ", "\n    ").replace("[", "[\n    ").replace("]", "\n]"))
