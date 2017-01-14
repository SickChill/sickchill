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

import os
import shutil
import stat

from rarfile import RarFile, RarWarning, RarFatalError, RarCRCError, NoRarEntry, NotRarFile, \
    RarLockedArchiveError, RarWriteError, RarOpenError, RarUserError, RarMemoryError, BadRarName, BadRarFile, \
    RarCreateError, RarNoFilesError, RarWrongPassword, RarCannotExec, RarSignalExit, RarUnknownError, Error, \
    RarUserBreak, RarNoFilesError, RarCreateError, RarExecError, NoCrypto, NeedFirstVolume, PasswordRequired

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
    if sickbeard.TV_DOWNLOAD_DIR:
        if helpers.real_path(folder) == helpers.real_path(sickbeard.TV_DOWNLOAD_DIR):
            return False

    # check if it's empty folder when wanted checked
    if check_empty:
        check_files = ek(os.listdir, folder)
        if check_files:
            logger.log(u"Not deleting folder {0} found the following files: {1}".format(folder, check_files), logger.INFO)
            return False

        try:
            logger.log(u"Deleting folder (if it's empty): {0}".format(folder))
            ek(os.rmdir, folder)
        except (OSError, IOError) as e:
            logger.log(u"Warning: unable to delete folder: {0}: {1}".format(folder, ex(e)), logger.WARNING)
            return False
    else:
        try:
            logger.log(u"Deleting folder: " + folder)
            shutil.rmtree(folder)
        except (OSError, IOError) as e:
            logger.log(u"Warning: unable to delete folder: {0}: {1}".format(folder, ex(e)), logger.WARNING)
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
        result.output += log_helper(u"Forcing deletion of files, even though last result was not success", logger.DEBUG)
    elif not result.result:
        return

    # Delete all file not needed
    for cur_file in unwanted_files:
        cur_file_path = ek(os.path.join, process_path, cur_file)
        if not ek(os.path.isfile, cur_file_path):
            continue  # Prevent error when a notwantedfiles is an associated files

        result.output += log_helper(u"Deleting file: {0}".format(cur_file), logger.DEBUG)

        # check first the read-only attribute
        file_attribute = ek(os.stat, cur_file_path)[0]
        if not file_attribute & stat.S_IWRITE:
            # File is read-only, so make it writeable
            result.output += log_helper(u"Changing ReadOnly Flag for file: {0}".format(cur_file), logger.DEBUG)
            try:
                ek(os.chmod, cur_file_path, stat.S_IWRITE)
            except OSError as e:
                result.output += log_helper(u"Cannot change permissions of {0}: {1}".format(cur_file_path, ex(e)), logger.DEBUG)
        try:
            ek(os.remove, cur_file_path)
        except OSError as e:
            result.output += log_helper(u"Unable to delete file {0}: {1}".format(cur_file, e.strerror), logger.DEBUG)


def log_helper(message, level=logger.INFO):
    logger.log(message, level)
    return message + u"\n"


# pylint: disable=too-many-arguments,too-many-branches,too-many-statements,too-many-locals
def process_dir(process_path, release_name=None, process_method=None, force=False, is_priority=None, delete_on=False, failed=False, mode="auto"):
    """
    Scans through the files in process_path and processes whatever media files it finds

    :param process_path: The folder name to look in
    :param release_name: The NZB/Torrent name which resulted in this folder being downloaded
    :param force: True to process previously processed files
    :param failed: Boolean for whether or not the download failed
    :param mode: Type of postprocessing auto or manual
    """

    result = ProcessResult()

    # if they passed us a real dir then assume it's the one we want
    if ek(os.path.isdir, process_path):
        process_path = ek(os.path.realpath, process_path)
        result.output += log_helper(u"Processing folder {0}".format(process_path), logger.DEBUG)

    # if the client and SickRage are not on the same machine translate the directory into a network directory
    elif all([sickbeard.TV_DOWNLOAD_DIR,
              ek(os.path.isdir, sickbeard.TV_DOWNLOAD_DIR),
              ek(os.path.normpath, process_path) == ek(os.path.normpath, sickbeard.TV_DOWNLOAD_DIR)]):
        process_path = ek(os.path.join, sickbeard.TV_DOWNLOAD_DIR, ek(os.path.abspath, process_path).split(os.path.sep)[-1])
        result.output += log_helper(u"Trying to use folder: {0} ".format(process_path), logger.DEBUG)

    # if we didn't find a real dir then quit
    if not ek(os.path.isdir, process_path):
        result.output += log_helper(u"Unable to figure out what folder to process. "
                                   u"If your downloader and SickRage aren't on the same PC "
                                   u"make sure you fill out your TV download dir in the config.",
                                   logger.DEBUG)
        return result.output

    path, subdirectories, files = get_path_dir_files(process_path, release_name, mode)

    files = filter(is_torrent_or_nzb_file, files)
    sync_files = filter(is_sync_file, files)

    original_release_name = release_name

    # Don't post process if files are still being synced and option is activated
    postpone = sync_files and sickbeard.POSTPONE_IF_SYNC_FILES

    if not postpone:
        result.output += log_helper(u"PostProcessing Path: {0}".format(path), logger.INFO)
        result.output += log_helper(u"PostProcessing Directories: {0}".format(str(subdirectories)), logger.DEBUG)

        video_files = filter(helpers.is_media_file, files)
        rarFiles = filter(helpers.is_rar_file, files)
        rar_contents = []
        if rarFiles:
            rar_contents = unRAR(path, rarFiles, force, result)
            files += rar_contents
            video_files += filter(helpers.is_media_file, rar_contents)

        video_in_rar = filter(helpers.is_media_file, rar_contents)

        result.output += log_helper(u"PostProcessing Files: {0}".format(files), logger.DEBUG)
        result.output += log_helper(u"PostProcessing VideoFiles: {0}".format(video_files), logger.DEBUG)
        result.output += log_helper(u"PostProcessing RarContent: {0}".format(rar_contents), logger.DEBUG)
        result.output += log_helper(u"PostProcessing VideoInRar: {0}".format(video_in_rar), logger.DEBUG)

        # If release_name is set and there's more than one video file in the folder, files will be lost (overwritten).
        release_name = (release_name, None)[len(video_files) >= 2]

        process_method = process_method if process_method else sickbeard.PROCESS_METHOD
        result.result = True

        # Don't Link media when the media is extracted from a rar in the same path
        if process_method in (u'hardlink', u'symlink') and video_in_rar:
            process_media(path, video_in_rar, release_name, u'move', force, is_priority, result)
            delete_files(path, rar_contents, result)
            for video in set(video_files) - set(video_in_rar):
                process_media(path, [video], release_name, process_method, force, is_priority, result)
        elif sickbeard.DELRARCONTENTS and video_in_rar:
            process_media(path, video_in_rar, release_name, process_method, force, is_priority, result)
            delete_files(path, rar_contents, result, True)
            for video in set(video_files) - set(video_in_rar):
                process_media(path, [video], release_name, process_method, force, is_priority, result)
        else:
            for video in video_files:
                process_media(path, [video], release_name, process_method, force, is_priority, result)

    else:
        result.output += log_helper(u"Found temporary sync files: {0} in path: {1}".format(sync_files, path))
        result.output += log_helper(u"Skipping post processing for folder: {0}".format(path))
        result.missed_files.append(u"{0} : Sync files found".format(path))

    # Process Video File in all TV Subdir
    for subdirectory in subdirectories:
        if not validate_dir(path, subdirectory, original_release_name, failed, result):
            continue

        result.result = True

        for current_directory, directory_names, file_names in ek(os.walk, ek(os.path.join, path, subdirectory), topdown=False):
            if not validate_dir(path, current_directory, original_release_name, failed, result):
                continue

            sync_files = filter(is_sync_file, file_names)

            # Don't post process if files are still being synced and option is activated
            postpone = sync_files and sickbeard.POSTPONE_IF_SYNC_FILES

            if not postpone:
                video_files = filter(helpers.is_media_file, file_names)
                rarFiles = (x for x in file_names if helpers.is_rar_file(ek(os.path.join, current_directory, x)))
                rar_contents = ()
                if rarFiles:
                    rar_contents = unRAR(current_directory, rarFiles, force, result)
                    file_names = set(file_names + rar_contents)
                    video_files += filter(helpers.is_media_file, rar_contents)

                video_in_rar = filter(helpers.is_media_file, rar_contents)
                unwanted_files = [x for x in file_names if x not in video_files]
                if unwanted_files:
                    result.output += log_helper(u"Found unwanted files: {0}".format(unwanted_files), logger.DEBUG)

                # Don't Link media when the media is extracted from a rar in the same path
                if process_method in (u'hardlink', u'symlink') and video_in_rar:
                    process_media(current_directory, video_in_rar, release_name, u'move', force, is_priority, result)
                    process_media(current_directory, set(video_files) - set(video_in_rar), release_name, process_method, force,
                                  is_priority, result)
                    delete_files(current_directory, rar_contents, result)
                elif sickbeard.DELRARCONTENTS and video_in_rar:
                    process_media(current_directory, video_in_rar, release_name, process_method, force, is_priority, result)
                    process_media(current_directory, set(video_files) - set(video_in_rar), release_name, process_method, force,
                                  is_priority, result)
                    delete_files(current_directory, rar_contents, result, True)
                else:
                    process_media(current_directory, video_files, release_name, process_method, force, is_priority, result)

                    # Delete all file not needed and avoid deleting files if Manual PostProcessing
                    if not(process_method == u"move" and result.result) or (mode == u"manual" and not delete_on):
                        continue

                    delete_folder(ek(os.path.join, current_directory, u'@eaDir'))
                    delete_files(current_directory, unwanted_files, result)

                    if all([not sickbeard.NO_DELETE or mode == u"manual",
                            process_method == u"move",
                            ek(os.path.normpath, current_directory) != ek(os.path.normpath, sickbeard.TV_DOWNLOAD_DIR)]):

                        if delete_folder(current_directory, check_empty=True):
                            result.output += log_helper(u"Deleted folder: {0}".format(current_directory), logger.DEBUG)

            else:
                result.output += log_helper(u"Found temporary sync files: {0} in path: {1}".format(sync_files, current_directory))
                result.output += log_helper(u"Skipping post processing for folder: {0}".format(current_directory))
                result.missed_files.append(u"{0} : Sync files found: {1}".format(path, sync_files))

    result.output += log_helper((u"Processing Failed", u"Successfully processed")[result.aggresult], (logger.WARNING, logger.INFO)[result.aggresult])
    if result.missed_files:
        result.output += log_helper(u"Some items were not processed.")
        for missed_file in result.missed_files:
            result.output += log_helper(missed_file)

    return result.output


def validate_dir(path, process_path, original_release_name, failed, result):  # pylint: disable=too-many-locals,too-many-branches,too-many-return-statements
    """
    Check if directory is valid for processing

    :param path: Path to use
    :param process_path: Directory to check
    :param original_release_name: Original NZB/Torrent name
    :param failed: Previously failed objects
    :param result: Previous results
    :return: True if dir is valid for processing, False if not
    """

    process_path = ss(process_path)
    result.output += log_helper(u"Processing folder " + process_path, logger.DEBUG)

    upper_name = ek(os.path.basename, process_path).upper()
    if upper_name.startswith(u'_FAILED_') or upper_name.endswith(u'_FAILED_'):
        result.output += log_helper(u"The directory name indicates it failed to extract.", logger.DEBUG)
        failed = True
    elif upper_name.startswith(u'_UNDERSIZED_') or upper_name.endswith(u'_UNDERSIZED_'):
        result.output += log_helper(u"The directory name indicates that it was previously rejected for being undersized.", logger.DEBUG)
        failed = True
    elif upper_name.startswith(u'_UNPACK') or upper_name.endswith(u'_UNPACK'):
        result.output += log_helper(u"The directory name indicates that this release is in the process of being unpacked.", logger.DEBUG)
        result.missed_files.append(u"{0} : Being unpacked".format(process_path))
        return False

    if failed:
        process_failed(ek(os.path.join, path, process_path), original_release_name, result)
        result.missed_files.append(u"{0} : Failed download".format(process_path))
        return False

    if helpers.is_hidden_folder(ek(os.path.join, path, process_path)):
        result.output += log_helper(u"Ignoring hidden folder: {0}".format(process_path), logger.DEBUG)
        result.missed_files.append(u"{0} : Hidden folder".format(process_path))
        return False

    # make sure the dir isn't inside a show dir
    main_db_con = db.DBConnection()
    sql_results = main_db_con.select("SELECT location FROM tv_shows")

    for sqlShow in sql_results:
        if process_path.lower().startswith(ek(os.path.realpath, sqlShow["location"]).lower() + os.sep) or \
                process_path.lower() == ek(os.path.realpath, sqlShow["location"]).lower():

            result.output += log_helper(
                u"Cannot process an episode that's already been moved to its show dir, skipping " + process_path,
                logger.WARNING)
            return False

    for current_directory, directory_names, file_names in ek(os.walk, ek(os.path.join, path, process_path), topdown=False):
        found_files = filter(helpers.is_media_file, file_names)
        if sickbeard.UNPACK:
            found_files += filter(helpers.is_rar_file, file_names)

        for found_file in found_files:
            if sickbeard.TV_DOWNLOAD_DIR and current_directory and current_directory != sickbeard.TV_DOWNLOAD_DIR and found_files:
                try:
                    NameParser().parse(found_file, cache_result=False)
                except (InvalidNameException, InvalidShowException):
                    pass
                else:
                    return True

        if sickbeard.TV_DOWNLOAD_DIR and current_directory and current_directory != sickbeard.TV_DOWNLOAD_DIR and found_files:
            try:
                NameParser().parse(ek(os.path.basename, current_directory), cache_result=False)
            except (InvalidNameException, InvalidShowException):
                pass
            else:
                return True

    result.output += log_helper(u"{0} : No processable items found in folder".format(process_path), logger.DEBUG)
    return False


def unRAR(path, rarFiles, force, result):  # pylint: disable=too-many-branches,too-many-statements
    """
    Extracts RAR files

    :param path: Path to look for files in
    :param rarFiles: Names of RAR files
    :param force: process currently processing items
    :param result: Previous results
    :return: List of unpacked file names
    """

    unpacked_files = []

    if sickbeard.UNPACK and rarFiles:

        result.output += log_helper(u"Packed Releases detected: {0}".format(rarFiles), logger.DEBUG)
        for archive in rarFiles:
            failure = None
            rar_handle = None
            try:
                archive_path = ek(os.path.join, path, archive)
                result.output += log_helper(u"Checking if archive is valid and contains a video: {0}".format(archive_path), logger.DEBUG)
                if not helpers.is_rar_file(archive_path):
                    continue

                rar_handle = RarFile(archive_path)
                if rar_handle.needs_password():
                    # TODO: Add support in settings for a list of passwords to try here with rar_handle.set_password(x)
                    result.output += log_helper('Arcive needs a password, skipping: {0}'.format(archive_path))
                    continue

                rar_handle.testrar()

                # If there are no video files in the rar, don't extract it
                if not filter(helpers.is_media_file, rar_handle.namelist()):
                    continue

                # Skip extraction if any file in archive has previously been extracted
                skip_file = False
                for file_in_archive in [ek(os.path.basename, x.filename) for x in rar_handle.infolist() if not x.isdir]:
                    if already_processed(path, file_in_archive, force, result):
                        result.output += log_helper(
                            u"Archive file already post-processed, extraction skipped: {0}".format
                            (file_in_archive), logger.DEBUG)

                        skip_file = True
                        break

                if skip_file:
                    continue

                result.output += log_helper(u"Unpacking archive: {0}".format(archive), logger.DEBUG)
                rar_handle.extractall(path=path)
                for x in rar_handle.infolist():
                    if not x.isdir:
                        basename = ek(os.path.basename, x.filename)
                        if basename not in unpacked_files:
                            unpacked_files.append(basename)

            except RarCRCError as e:
                failure = (u'Archive Broken', u'Unpacking failed because of a CRC error')
            except RarWrongPassword:
                failure = (u'Incorrect RAR Password', u'Unpacking failed because of an Incorrect Rar Password')
            except PasswordRequired:
                failure = (u'Rar is password protected', u'Unpacking failed because it needs a password')
            except RarOpenError:
                failure = (u'Rar Open Error, check the parent folder and destination file permissions.',
                           u'Unpacking failed with a File Open Error (file permissions?)')
            except RarExecError:
                failure = (u'Invalid Rar Archive Usage', u'Unpacking Failed with Invalid Rar Archive Usage')
            except BadRarFile:
                failure = (u'Invalid Rar Archive', u'Unpacking Failed with an Invalid Rar Archive Error')
            except NeedFirstVolume:
                continue
            except Exception as e:
                failure = (e, u'Unpacking failed')
            finally:
                if rar_handle:
                    del rar_handle

            if failure:
                result.output += log_helper(u'Failed Unrar archive {0}: {1}'.format(archive, failure[0]), logger.ERROR)
                result.missed_files.append(u'{0} : Unpacking failed: {1}'.format(archive, failure[1]))
                result.result = False
                continue

        result.output += log_helper(u"UnRar content: {0}".format(unpacked_files), logger.DEBUG)

    return unpacked_files


def already_processed(process_path, videofile, force, result):  # pylint: disable=unused-argument
    """
    Check if we already post processed a file

    :param process_path: Directory a file resides in
    :param videofile: File name
    :param force: Force checking when already checking (currently unused)
    :param result: True if file is already postprocessed, False if not
    :return:
    """
    if force:
        return False

    # Avoid processing the same dir again if we use a process method <> move
    main_db_con = db.DBConnection()
    sql_result = main_db_con.select("SELECT release_name FROM tv_episodes WHERE release_name IN (?, ?) LIMIT 1", [process_path, videofile.rpartition('.')[0]])
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

    search_sql += " AND tv_episodes.status IN (" + ",".join([str(x) for x in common.Quality.DOWNLOADED]) + ")"
    search_sql += " AND history.resource LIKE ? LIMIT 1"
    sql_result = main_db_con.select(search_sql, ['%' + videofile])
    if sql_result:
        # result.output += log_helper(u"You're trying to post process a video that's already been processed, skipping", logger.DEBUG)
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
            result.output += log_helper(u"Skipping already processed file: {0}".format(cur_video_file), logger.DEBUG)
            continue

        try:
            processor = postProcessor.PostProcessor(cur_video_file_path, release_name, process_method, is_priority)
            result.result = processor.process()
            process_fail_message = u""
        except EpisodePostProcessingFailedException as e:
            result.result = False
            process_fail_message = ex(e)

        if processor:
            result.output += processor.log

        if result.result:
            result.output += log_helper(u"Processing succeeded for {0}".format(cur_video_file_path))
        else:
            result.output += log_helper(u"Processing failed for {0}: {1}".format(cur_video_file_path, process_fail_message), logger.WARNING)
            result.missed_files.append(u"{0} : Processing failed: {1}".format(cur_video_file_path, process_fail_message))
            result.aggresult = False


def get_path_dir_files(process_path, release_name, mode):
    """
    Get files in a path

    :param process_path: Directory to start in
    :param release_name: NZB/Torrent file, if present
    :param mode: auto/manual
    :return: a tuple of (path,subdirectories,files)
    """
    path = u""
    subdirectories = []
    files = []

    if process_path == sickbeard.TV_DOWNLOAD_DIR and not release_name or mode == u"manual":  # Scheduled Post Processing Active
        # Get at first all the subdir in the process_path
        for path, subdirectories, files in ek(os.walk, process_path):
            break
    else:
        path, directory = ek(os.path.split, process_path)  # Script Post Processing
        if not (release_name is None or release_name.endswith((u'.nzb', u'.torrent'))) and ek(os.path.isfile, ek(os.path.join, process_path, release_name)):
            # For single torrent file without Dir
            subdirectories = []
            files = [ek(os.path.join, process_path, release_name)]
        else:
            subdirectories = [directory]
            files = []

    return path, subdirectories, files


def process_failed(process_path, release_name, result):
    """Process a download that did not complete correctly"""

    if sickbeard.USE_FAILED_DOWNLOADS:
        processor = None

        try:
            processor = failedProcessor.FailedProcessor(process_path, release_name)
            result.result = processor.process()
            process_fail_message = u""
        except FailedPostProcessingFailedException as e:
            result.result = False
            process_fail_message = ex(e)

        if processor:
            result.output += processor.log

        if sickbeard.DELETE_FAILED and result.result:
            if delete_folder(process_path, check_empty=False):
                result.output += log_helper(u"Deleted folder: {0}".format(process_path), logger.DEBUG)

        if result.result:
            result.output += log_helper(u"Failed Download Processing succeeded: ({0}, {1})".format(release_name, process_path))
        else:
            result.output += log_helper(u"Failed Download Processing failed: ({0}, {1}): {2}".format(release_name, process_path, process_fail_message), logger.WARNING)


def subtitles_enabled(video):
    """
    Parse video filename to a show to check if it has subtitle enabled

    :param video: video filename to be parsed
    """

    try:
        parse_result = NameParser().parse(video, cache_result=True)
    except (InvalidNameException, InvalidShowException):
        logger.log(u'Not enough information to parse filename into a valid show. Consider add scene exceptions or improve naming for: {0}'.format(video), logger.WARNING)
        return False

    if parse_result.show.indexerid:
        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT subtitles FROM tv_shows WHERE indexer_id = ? LIMIT 1", [parse_result.show.indexerid])
        return bool(sql_results[0]["subtitles"]) if sql_results else False
    else:
        logger.log(u'Empty indexer ID for: {0}'.format(video), logger.WARNING)
        return False
