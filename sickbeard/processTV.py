# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io/
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

import os
import shutil
import stat

from rarfile import RarFile, RarWarning, RarFatalError, RarCRCError, NoRarEntry, NotRarFile, \
    RarLockedArchiveError, RarWriteError, RarOpenError, RarUserError, RarMemoryError, BadRarName, BadRarFile, \
    RarNoFilesError, RarWrongPassword, RarCannotExec, RarSignalExit, RarUnknownError, Error, \
    RarUserBreak, RarCreateError, RarExecError, NoCrypto, NeedFirstVolume, PasswordRequired

import sickbeard
from sickbeard import common, db, failedProcessor, helpers, logger, postProcessor
from sickbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickrage.helper.common import is_sync_file, is_torrent_or_nzb_file
from sickrage.helper.encoding import ek, ss
from sickrage.helper.exceptions import EpisodePostProcessingFailedException, FailedPostProcessingFailedException, ex


class ProcessResult(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.result = True
        self.output = ''
        self.missed_files = []
        self.aggresult = True
        self.current_extracted_dir = ''


def delete_folder(folder, check_empty=True):
    """
    Removes a folder from the filesystem

    :param folder: Path to folder to remove
    :param check_empty: Boolean, check if the folder is empty before removing it, defaults to True
    :return: True on success, False on failure
    """

    # check if it's a folder
    if not ek(os.path.isdir, folder):
        return False

    # check if it isn't TV_DOWNLOAD_DIR
    if sickbeard.TV_DOWNLOAD_DIR and helpers.real_path(folder) == helpers.real_path(sickbeard.TV_DOWNLOAD_DIR):
        return False

    # check if it's empty folder when wanted checked
    if check_empty:
        check_files = ek(os.listdir, folder)
        if check_files:
            logger.log("Not deleting folder {0} found the following files: {1}".format(folder, check_files), logger.INFO)
            return False

        try:
            logger.log("Deleting folder (if it's empty): {0}".format(folder))
            ek(os.rmdir, folder)
        except (OSError, IOError) as e:
            logger.log("Warning: unable to delete folder: {0}: {1}".format(folder, ex(e)), logger.WARNING)
            return False
    else:
        try:
            logger.log("Deleting folder: " + folder)
            shutil.rmtree(folder)
        except (OSError, IOError) as e:
            logger.log("Warning: unable to delete folder: {0}: {1}".format(folder, ex(e)), logger.WARNING)
            return False

    return True


def delete_files(process_path, unwanted_files, result, force=False):
    """
    Remove files from filesystem

    :param process_path: path to process
    :param unwanted_files: files we do not want
    :param result: Processor results
    :param force: Boolean, force deletion, defaults to false
    """
    if not result.result and force:
        result.output += log_helper("Forcing deletion of files, even though last result was not success", logger.DEBUG)
    elif not result.result:
        return

    # Delete all file not needed
    for cur_file in unwanted_files:
        cur_file_path = ek(os.path.join, process_path, cur_file)
        if not ek(os.path.isfile, cur_file_path):
            continue  # Prevent error when a notwantedfiles is an associated files

        result.output += log_helper("Deleting file: {0}".format(cur_file), logger.DEBUG)

        # check first the read-only attribute
        file_attribute = ek(os.stat, cur_file_path)[0]
        if not file_attribute & stat.S_IWRITE:
            # File is read-only, so make it writeable
            result.output += log_helper("Changing ReadOnly Flag for file: {0}".format(cur_file), logger.DEBUG)
            try:
                ek(os.chmod, cur_file_path, stat.S_IWRITE)
            except OSError as e:
                result.output += log_helper("Cannot change permissions of {0}: {1}".format(cur_file_path, ex(e)), logger.DEBUG)
        try:
            ek(os.remove, cur_file_path)
        except OSError as e:
            result.output += log_helper("Unable to delete file {0}: {1}".format(cur_file, e.strerror), logger.DEBUG)


def log_helper(message, level=logger.INFO):
    logger.log(message, level)
    return message + "\n"


# pylint: disable=too-many-arguments,too-many-branches,too-many-statements,too-many-locals
def process_dir(process_path, release_name=None, process_method=None, force=False, is_priority=None, delete_on=False, failed=False, mode="auto", result=None):
    """
    Scans through the files in process_path and processes whatever media files it finds

    :param process_path: The folder name to look in
    :param release_name: The NZB/Torrent name which resulted in this folder being downloaded
    :param process_method: processing method, copy/move/symlink/link
    :param force: True to process previously processed files
    :param is_priority: whether to replace the file even if it exists at higher quality
    :param delete_on: delete files and folders after they are processed (always happens with move and auto combination)
    :param failed: Boolean for whether or not the download failed
    :param mode: Type of postprocessing auto or manual
    """

    result = result or ProcessResult()

    # if they passed us a real dir then assume it's the one we want
    if ek(os.path.isdir, process_path):
        process_path = ek(os.path.realpath, process_path)
        result.output += log_helper("Processing in folder {0}".format(process_path), logger.DEBUG)

    # if the client and SickRage are not on the same machine translate the directory into a network directory
    elif all([sickbeard.TV_DOWNLOAD_DIR,
              ek(os.path.isdir, sickbeard.TV_DOWNLOAD_DIR),
              ek(os.path.normpath, process_path) == ek(os.path.normpath, sickbeard.TV_DOWNLOAD_DIR)]):
        process_path = ek(os.path.join, sickbeard.TV_DOWNLOAD_DIR, ek(os.path.abspath, process_path).split(os.path.sep)[-1])
        result.output += log_helper("Trying to use folder: {0} ".format(process_path), logger.DEBUG)

    # if we didn't find a real dir then quit
    if not ek(os.path.isdir, process_path):
        result.output += log_helper("Unable to figure out what folder to process. "
                                    "If your downloader and SickRage aren't on the same PC "
                                    "make sure you fill out your TV download dir in the config.",
                                    logger.DEBUG)
        return result

    process_method = process_method or sickbeard.PROCESS_METHOD

    for current_directory, directory_names, file_names in ek(os.walk, process_path, followlinks=sickbeard.PROCESSOR_FOLLOW_SYMLINKS):
        result.result = True

        file_names = [f for f in file_names if not is_torrent_or_nzb_file(f)]
        rar_files = [x for x in file_names if helpers.is_rar_file(ek(os.path.join, current_directory, x))]
        for rar_file in rar_files:
            result = unpack(current_directory, rar_file, force, result)
            if result.result and result.current_extracted_dir:
                # delete_on is always set to sickbeard.DELRARCONTENTS here because all of these files are extracted files.
                # we don't need to delete the folder here if the delete_on is set correctly because it will be deleted in process_dir
                # rar contents are always `move`
                # TODO: List files associated with the rar and pass them through to process_dir? Inner video filename may not match the rar release name
                # And maybe only the video was rar'd?
                result = process_dir(
                    process_path=result.current_extracted_dir,
                    release_name=None,
                    process_method='move',
                    force=force,
                    is_priority=is_priority,
                    delete_on=sickbeard.DELRARCONTENTS,
                    failed=failed,
                    mode=mode,
                    result=result
                )
                if process_method == 'move':
                    delete_files(current_directory, [rar_file], result)

        if not validate_dir(current_directory, release_name, failed, result):
            continue

        video_files = filter(helpers.is_media_file, file_names)
        if video_files:
            process_media(current_directory, video_files, release_name, process_method, force, is_priority, result)
        else:
            result.result = False

        # Delete all file not needed and avoid deleting files if Manual PostProcessing
        if not(process_method == "move" and result.result) or (mode == "manual" and not delete_on):
            continue

        # noinspection PyTypeChecker
        unwanted_files = filter(lambda x: x in video_files + rar_files + ['.stfolder'], file_names)
        if unwanted_files:
            result.output += log_helper("Found unwanted files: {0}".format(unwanted_files), logger.DEBUG)

        delete_folder(ek(os.path.join, current_directory, '@eaDir'), False)
        delete_files(current_directory, unwanted_files, result)

        if delete_folder(current_directory, check_empty=(sickbeard.NO_DELETE, delete_on)[sickbeard.NO_DELETE]):
            result.output += log_helper("Deleted folder: {0}".format(current_directory), logger.DEBUG)

    result.output += log_helper(("Processing Failed", "Successfully processed")[result.aggresult], (logger.WARNING, logger.INFO)[result.aggresult])
    if result.missed_files:
        result.output += log_helper("Some items were not processed.")
        for missed_file in result.missed_files:
            result.output += log_helper(missed_file)

    return result


def validate_dir(process_path, release_name, failed, result):  # pylint: disable=too-many-locals,too-many-branches,too-many-return-statements
    """
    Check if directory is valid for processing

    :param process_path: Directory to check
    :param release_name: Original NZB/Torrent name
    :param failed: Previously failed objects
    :param result: Previous results
    :return: True if dir is valid for processing, False if not
    """

    result.output += log_helper("Processing folder " + process_path, logger.DEBUG)

    upper_name = ek(os.path.basename, process_path).upper()
    if upper_name.startswith('_FAILED_') or upper_name.endswith('_FAILED_'):
        result.output += log_helper("The directory name indicates it failed to extract.", logger.DEBUG)
        failed = True
    elif upper_name.startswith('_UNDERSIZED_') or upper_name.endswith('_UNDERSIZED_'):
        result.output += log_helper("The directory name indicates that it was previously rejected for being undersized.", logger.DEBUG)
        failed = True
    elif upper_name.startswith('_UNPACK') or upper_name.endswith('_UNPACK'):
        result.output += log_helper("The directory name indicates that this release is in the process of being unpacked.", logger.DEBUG)
        result.missed_files.append("{0} : Being unpacked".format(process_path))
        return False

    if failed:
        process_failed(process_path, release_name, result)
        result.missed_files.append("{0} : Failed download".format(process_path))
        return False

    if sickbeard.TV_DOWNLOAD_DIR and helpers.real_path(process_path) != helpers.real_path(sickbeard.TV_DOWNLOAD_DIR) and helpers.is_hidden_folder(process_path):
        result.output += log_helper("Ignoring hidden folder: {0}".format(process_path), logger.DEBUG)
        result.missed_files.append("{0} : Hidden folder".format(process_path))
        return False

    # make sure the dir isn't inside a show dir
    main_db_con = db.DBConnection()
    sql_results = main_db_con.select("SELECT location FROM tv_shows")

    for sqlShow in sql_results:
        if process_path.lower().startswith(ek(os.path.realpath, sqlShow[b"location"]).lower() + os.sep) or \
                process_path.lower() == ek(os.path.realpath, sqlShow[b"location"]).lower():

            result.output += log_helper(
                "Cannot process an episode that's already been moved to its show dir, skipping " + process_path,
                logger.WARNING)
            return False

    for current_directory, directory_names, file_names in ek(os.walk, process_path, topdown=False, followlinks=sickbeard.PROCESSOR_FOLLOW_SYMLINKS):
        sync_files = filter(is_sync_file, file_names)
        if sync_files and sickbeard.POSTPONE_IF_SYNC_FILES:
            result.output += log_helper("Found temporary sync files: {0} in path: {1}".format(sync_files, ek(os.path.join, process_path, sync_files[0])))
            result.output += log_helper("Skipping post processing for folder: {0}".format(process_path))
            result.missed_files.append("{0} : Sync files found".format(ek(os.path.join, process_path, sync_files[0])))
            continue

        found_files = filter(helpers.is_media_file, file_names)
        if sickbeard.UNPACK == 1:
            found_files += filter(helpers.is_rar_file, file_names)

        if current_directory != sickbeard.TV_DOWNLOAD_DIR and found_files:
            found_files.append(ek(os.path.basename, current_directory))

        for found_file in found_files:
            try:
                NameParser().parse(found_file, cache_result=False)
            except (InvalidNameException, InvalidShowException) as e:
                pass
            else:
                return True

    result.output += log_helper("{0} : No processable items found in folder".format(process_path), logger.DEBUG)
    return False


def unpack(path, rar_file, force, result):
    """
    Extracts RAR files

    :param path: Path to look for file in
    :param rar_file: Name of RAR file
    :param force: process currently processing items
    :param result: Previous <ProcessResult>result
    :return: <ProcessResult>result
    """

    result.current_extracted_dir = ''
    if sickbeard.UNPACK == 1 and rar_file:
        result.output += log_helper("Packed Release detected: {0}".format(rar_file), logger.DEBUG)
        failure = None
        rar_handle = None
        try:
            full_rar_path = ek(os.path.join, path, rar_file)
            if already_processed(path, rar_file, force, result):
                result.output += log_helper(
                    "Archive file already post-processed, extraction skipped: {0}".format(full_rar_path), logger.DEBUG)
                return result

            if not helpers.is_rar_file(full_rar_path):
                return result

            result.output += log_helper("Checking if archive is valid and contains a video: {0}".format(full_rar_path), logger.DEBUG)
            rar_handle = RarFile(full_rar_path)
            if rar_handle.needs_password():
                # TODO: Add support in settings for a list of passwords to try here with rar_handle.set_password(x)
                result.output += log_helper('Archive needs a password, skipping: {0}'.format(full_rar_path))
                return result

            # If there are no video files in the rar, don't extract it
            rar_media_files = filter(helpers.is_media_file, rar_handle.namelist())
            if not rar_media_files:
                return result

            rar_release_name = rar_file.rpartition('.')[0]

            # Choose the directory we'll unpack to:
            if sickbeard.UNPACK_DIR and os.path.isdir(sickbeard.UNPACK_DIR): # verify the unpack dir exists
                unpack_base_dir = sickbeard.UNPACK_DIR
            else:
                unpack_base_dir = path
                if sickbeard.UNPACK_DIR: # Let user know if we can't unpack there
                    result.output += log_helper('Unpack directory cannot be verified. Using {0}'.format(unpack_base_dir), logger.DEBUG)

            # Fix up the list for checking if already processed
            rar_media_files = [os.path.join(unpack_base_dir, rar_release_name, rar_media_file) for rar_media_file in rar_media_files]
            for rar_media_file in rar_media_files:
                check_path, check_file = os.path.split(rar_media_file)
                if already_processed(check_path, check_file, force, result):
                    result.output += log_helper("Archive file already post-processed, extraction skipped: {0}".format(rar_media_file), logger.DEBUG)
                    return result

            rar_extract_path = ek(os.path.join, unpack_base_dir, rar_release_name)
            result.output += log_helper("Unpacking archive: {0}".format(rar_file), logger.DEBUG)
            rar_handle.extractall(path=rar_extract_path)
            result.current_extracted_dir = rar_extract_path

        except RarCRCError:
            failure = ('Archive Broken', 'Unpacking failed because of a CRC error')
        except RarWrongPassword:
            failure = ('Incorrect RAR Password', 'Unpacking failed because of an Incorrect Rar Password')
        except PasswordRequired:
            failure = ('Rar is password protected', 'Unpacking failed because it needs a password')
        except RarOpenError:
            failure = ('Rar Open Error, check the parent folder and destination file permissions.',
                       'Unpacking failed with a File Open Error (file permissions?)')
        except RarExecError:
            failure = ('Invalid Rar Archive Usage', 'Unpacking Failed with Invalid Rar Archive Usage. Is unrar installed and on the system PATH?')
        except BadRarFile:
            failure = ('Invalid Rar Archive', 'Unpacking Failed with an Invalid Rar Archive Error')
        except NeedFirstVolume:
            pass
        except (Exception, Error) as e:
            failure = (ex(e), 'Unpacking failed')
        finally:
            if rar_handle:
                del rar_handle

        if failure:
            result.output += log_helper('Failed to extract the archive {0}: {1}'.format(rar_file, failure[0]), logger.WARNING)
            result.missed_files.append('{0} : Unpacking failed: {1}'.format(rar_file, failure[1]))
            result.result = False

    return result


def already_processed(process_path, video_file, force, result):  # pylint: disable=unused-argument
    """
    Check if we already post processed a file

    :param process_path: Directory a file resides in
    :param video_file: File name
    :param force: Force checking when already checking (currently unused)
    :param result: True if file is already postprocessed, False if not
    :return:
    """
    if force:
        return False

    # Avoid processing the same dir again if we use a process method <> move
    main_db_con = db.DBConnection()
    sql_result = main_db_con.select("SELECT release_name FROM tv_episodes WHERE release_name IN (?, ?) LIMIT 1", [process_path, video_file.rpartition('.')[0]])
    if sql_result:
        # result.output += log_helper(u"You're trying to post process a dir that's already been processed, skipping", logger.DEBUG)
        return True

    # Needed if we have downloaded the same episode @ different quality
    # But we need to make sure we check the history of the episode we're going to PP, and not others
    try:  # if it fails to find any info (because we're doing an unparsable folder (like the TV root dir) it will throw an exception, which we want to ignore
        parse_result = NameParser(process_path, tryIndexers=True).parse(process_path)
    except (InvalidNameException, InvalidShowException):  # ignore the exception, because we kind of expected it, but create parse_result anyway so we can perform a check on it.
        parse_result = False  # pylint: disable=redefined-variable-type

    search_sql = "SELECT tv_episodes.indexerid, history.resource FROM tv_episodes INNER JOIN history ON history.showid=tv_episodes.showid" # This part is always the same
    search_sql += " WHERE history.season=tv_episodes.season AND history.episode=tv_episodes.episode"

    # If we find a showid, a season number, and one or more episode numbers then we need to use those in the query
    if parse_result and parse_result.show.indexerid and parse_result.episode_numbers and parse_result.season_number:
        search_sql += " AND tv_episodes.showid={0} AND tv_episodes.season={1} AND tv_episodes.episode={2}".format(
            parse_result.show.indexerid, parse_result.season_number, parse_result.episode_numbers[0])

    search_sql += " AND tv_episodes.status IN (" + ",".join([str(x) for x in common.Quality.DOWNLOADED + common.Quality.ARCHIVED]) + ")"
    search_sql += " AND history.resource LIKE ? LIMIT 1"
    sql_result = main_db_con.select(search_sql, ['%' + video_file])
    if sql_result:
        result.output += log_helper("You're trying to post process a video that's already been processed, skipping", logger.DEBUG)
        return True

    return False


def process_media(process_path, video_files, release_name, process_method, force, is_priority, result):  # pylint: disable=too-many-arguments
    """
    Postprocess mediafiles

    :param process_path: Path to process in
    :param video_files: Filenames to look for and postprocess
    :param release_name: Name of NZB/Torrent file related
    :param process_method: auto/manual
    :param force: Postprocess currently postprocessing file
    :param is_priority: Boolean, is this a priority download
    :param result: Previous results
    """

    processor = None
    for cur_video_file in video_files:
        cur_video_file_path = ek(os.path.join, process_path, cur_video_file)

        if already_processed(process_path, cur_video_file, force, result):
            result.output += log_helper("Skipping already processed file: {0}".format(cur_video_file), logger.DEBUG)
            continue

        try:
            processor = postProcessor.PostProcessor(cur_video_file_path, release_name, process_method, is_priority)
            result.result = processor.process()
            process_fail_message = ""
        except EpisodePostProcessingFailedException as e:
            result.result = False
            process_fail_message = ex(e)

        if processor:
            result.output += processor.log

        if result.result:
            result.output += log_helper("Processing succeeded for {0}".format(cur_video_file_path))
        else:
            result.output += log_helper("Processing failed for {0}: {1}".format(cur_video_file_path, process_fail_message), logger.WARNING)
            result.missed_files.append("{0} : Processing failed: {1}".format(cur_video_file_path, process_fail_message))
            result.aggresult = False


def process_failed(process_path, release_name, result):
    """Process a download that did not complete correctly"""

    if sickbeard.USE_FAILED_DOWNLOADS:
        processor = None

        try:
            processor = failedProcessor.FailedProcessor(process_path, release_name)
            result.result = processor.process()
            process_fail_message = ""
        except FailedPostProcessingFailedException as e:
            result.result = False
            process_fail_message = ex(e)

        if processor:
            result.output += processor.log

        if sickbeard.DELETE_FAILED and result.result:
            if delete_folder(process_path, check_empty=False):
                result.output += log_helper("Deleted folder: {0}".format(process_path), logger.DEBUG)

        if result.result:
            result.output += log_helper("Failed Download Processing succeeded: ({0}, {1})".format(release_name, process_path))
        else:
            result.output += log_helper("Failed Download Processing failed: ({0}, {1}): {2}".format(release_name, process_path, process_fail_message), logger.WARNING)


def subtitles_enabled(video):
    """
    Parse video filename to a show to check if it has subtitle enabled

    :param video: video filename to be parsed
    """

    try:
        parse_result = NameParser().parse(video, cache_result=True)
    except (InvalidNameException, InvalidShowException):
        logger.log('Not enough information to parse filename into a valid show. Consider add scene exceptions or improve naming for: {0}'.format(video), logger.WARNING)
        return False

    if parse_result.show.indexerid:
        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT subtitles FROM tv_shows WHERE indexer_id = ? LIMIT 1", [parse_result.show.indexerid])
        return bool(sql_results[0][b"subtitles"]) if sql_results else False
    else:
        logger.log('Empty indexer ID for: {0}'.format(video), logger.WARNING)
        return False
