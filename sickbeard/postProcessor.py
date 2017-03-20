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
# pylint: disable=too-many-lines

from __future__ import print_function, unicode_literals

import fnmatch
import os
import re
import stat
import subprocess

import adba

import sickbeard
from sickbeard import common, db, failed_history, helpers, history, logger, notifiers, show_name_helpers
from sickbeard.helpers import verify_freespace
from sickbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickrage.helper import glob
from sickrage.helper.common import SUBTITLE_EXTENSIONS, remove_extension, replace_extension
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import EpisodeNotFoundException, EpisodePostProcessingFailedException, \
    ShowDirectoryNotFoundException, ex
from sickrage.show.Show import Show


import six


class PostProcessor(object):  # pylint: disable=too-many-instance-attributes
    """
    A class which will process a media file according to the post processing settings in the config.
    """

    EXISTS_LARGER = 1
    EXISTS_SAME = 2
    EXISTS_SMALLER = 3
    DOESNT_EXIST = 4

    IGNORED_FILESTRINGS = [".AppleDouble", ".DS_Store"]

    def __init__(self, file_path, nzb_name=None, process_method=None, is_priority=None):
        """
        Creates a new post processor with the given file path and optionally an NZB name.

        file_path: The path to the file to be processed
        nzb_name: The name of the NZB which resulted in this file being downloaded (optional)
        """
        # absolute path to the folder that is being processed
        self.folder_path = ek(os.path.dirname, ek(os.path.abspath, file_path))

        # full path to file
        self.file_path = file_path

        # file name only
        self.file_name = ek(os.path.basename, file_path)

        # the name of the folder only
        self.folder_name = ek(os.path.basename, self.folder_path)

        # name of the NZB that resulted in this folder
        self.nzb_name = nzb_name

        self.process_method = process_method if process_method else sickbeard.PROCESS_METHOD

        self.in_history = False

        self.release_group = None

        self.release_name = None

        self.is_proper = False

        self.is_priority = is_priority

        self.log = ''

        self.version = None

        self.anidbEpisode = None

    def _log(self, message, level=logger.INFO):
        """
        A wrapper for the internal logger which also keeps track of messages and saves them to a string for later.

        :param message: The string to log (six.text_type)
        :param level: The log level to use (optional)
        """
        logger.log(message, level)
        self.log += message + '\n'

    def _checkForExistingFile(self, existing_file):
        """
        Checks if a file exists already and if it does whether it's bigger or smaller than
        the file we are post processing

        ;param existing_file: The file to compare to

        :return:
            DOESNT_EXIST if the file doesn't exist
            EXISTS_LARGER if the file exists and is larger than the file we are post processing
            EXISTS_SMALLER if the file exists and is smaller than the file we are post processing
            EXISTS_SAME if the file exists and is the same size as the file we are post processing
        """

        if not existing_file:
            self._log("There is no existing file so there's no worries about replacing it", logger.DEBUG)
            return PostProcessor.DOESNT_EXIST

        # if the new file exists, return the appropriate code depending on the size
        if ek(os.path.isfile, existing_file):

            # see if it's bigger than our old file
            if ek(os.path.getsize, existing_file) > ek(os.path.getsize, self.file_path):
                self._log("File " + existing_file + " is larger than " + self.file_path, logger.DEBUG)
                return PostProcessor.EXISTS_LARGER

            elif ek(os.path.getsize, existing_file) == ek(os.path.getsize, self.file_path):
                self._log("File " + existing_file + " is the same size as " + self.file_path, logger.DEBUG)
                return PostProcessor.EXISTS_SAME

            else:
                self._log("File " + existing_file + " is smaller than " + self.file_path, logger.DEBUG)
                return PostProcessor.EXISTS_SMALLER

        else:
            self._log("File " + existing_file + " doesn't exist so there's no worries about replacing it",
                      logger.DEBUG)
            return PostProcessor.DOESNT_EXIST

    def list_associated_files(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
            self, file_path, subtitles_only=False, subfolders=False, rename=False):
        """
        For a given file path searches for files with the same name but different extension and returns their absolute paths

        :param file_path: The file to check for associated files
        :return: A list containing all files which are associated to the given file
        """
        def recursive_glob(treeroot, pattern):
            results = []
            for base, dirnames_, files in ek(os.walk, treeroot.encode(sickbeard.SYS_ENCODING), followlinks=sickbeard.PROCESSOR_FOLLOW_SYMLINKS):
                goodfiles = fnmatch.filter(files, pattern)
                for f in goodfiles:
                    found_file = ek(os.path.join, base, f)
                    if found_file != file_path:
                        results.append(found_file)
            return results

        if not file_path:
            return []

        file_path_list_to_allow = []
        file_path_list_to_delete = []

        if subfolders:
            base_name = ek(os.path.basename, file_path).rpartition('.')[0]
        else:
            base_name = file_path.rpartition('.')[0]

        # don't strip it all and use cwd by accident
        if not base_name:
            return []

        dirname = ek(os.path.dirname, file_path) or '.'

        # subfolders are only checked in show folder, so names will always be exactly alike
        if subfolders:
            # just create the list of all files starting with the basename
            filelist = recursive_glob(dirname, glob.escape(base_name) + '*')
        # this is called when PP, so we need to do the filename check case-insensitive
        else:
            filelist = []

            # loop through all the files in the folder, and check if they are the same name even when the cases don't match
            for found_file in glob.glob(ek(os.path.join, glob.escape(dirname), '*')):
                file_name, separator, file_extension = found_file.rpartition('.')

                # Handles subtitles with language code
                if file_extension in SUBTITLE_EXTENSIONS and file_name.rpartition('.')[0].lower() == base_name.lower():
                    filelist.append(found_file)
                # Handles all files with same basename, including subtitles without language code
                elif file_name.lower() == base_name.lower():
                    filelist.append(found_file)

        for associated_file_path in filelist:
            # Exclude the video file we are post-processing
            if os.path.abspath(associated_file_path) == os.path.abspath(file_path):
                continue

            # If this is a rename in the show folder, we don't need to check anything, just add it to the list
            if rename:
                file_path_list_to_allow.append(associated_file_path)
                continue

            # Exclude non-subtitle files with the 'subtitles_only' option
            if subtitles_only and not associated_file_path.endswith(tuple(SUBTITLE_EXTENSIONS)):
                continue

            # Exclude .rar files from associated list
            if helpers.is_rar_file(associated_file_path):
                continue

            # Define associated files (all, allowed and non allowed)
            if ek(os.path.isfile, associated_file_path):
                # check if allowed or not during post processing
                if sickbeard.MOVE_ASSOCIATED_FILES and associated_file_path.endswith(tuple(sickbeard.ALLOWED_EXTENSIONS.split(","))):
                    file_path_list_to_allow.append(associated_file_path)
                elif sickbeard.DELETE_NON_ASSOCIATED_FILES:
                    file_path_list_to_delete.append(associated_file_path)

        if file_path_list_to_allow or file_path_list_to_delete:
            self._log("Found the following associated files for {0}: {1}".format(file_path, file_path_list_to_allow + file_path_list_to_delete), logger.DEBUG)
            if file_path_list_to_delete:
                self._log("Deleting non allowed associated files for {0}: {1}".format(file_path, file_path_list_to_delete), logger.DEBUG)
                # Delete all extensions the user doesn't allow
                self._delete(file_path_list_to_delete)
            if file_path_list_to_allow:
                self._log("Allowing associated files for {0}: {1}".format(file_path, file_path_list_to_allow), logger.DEBUG)
        else:
            self._log("No associated files for {0} were found during this pass".format(file_path), logger.DEBUG)

        return file_path_list_to_allow

    def _delete(self, file_path, associated_files=False):
        """
        Deletes the file and optionally all associated files.

        :param file_path: The file to delete
        :param associated_files: True to delete all files which differ only by extension, False to leave them
        """

        if not file_path:
            return

        # Check if file_path is a list, if not, make it one
        if not isinstance(file_path, list):
            file_list = [file_path]
        else:
            file_list = file_path

        # figure out which files we want to delete
        if associated_files:
            file_list = file_list + self.list_associated_files(file_path, subfolders=True)

        if not file_list:
            self._log("There were no files associated with " + file_path + ", not deleting anything", logger.DEBUG)
            return

        # delete the file and any other files which we want to delete
        for cur_file in file_list:
            if ek(os.path.isfile, cur_file):
                self._log("Deleting file " + cur_file, logger.DEBUG)
                # check first the read-only attribute
                file_attribute = ek(os.stat, cur_file)[0]
                if not file_attribute & stat.S_IWRITE:
                    # File is read-only, so make it writeable
                    self._log('Read only mode on file ' + cur_file + ' Will try to make it writeable', logger.DEBUG)
                    try:
                        ek(os.chmod, cur_file, stat.S_IWRITE)
                    except Exception:
                        self._log('Cannot change permissions of ' + cur_file, logger.WARNING)

                ek(os.remove, cur_file)

                # do the library update for synoindex
                notifiers.synoindex_notifier.deleteFile(cur_file)

    def _combined_file_operation(self, file_path, new_path,  # pylint: disable=too-many-arguments, too-many-locals, too-many-branches
                                 new_base_name, associated_files=False,
                                 action=None, subtitles=False):
        """
        Performs a generic operation (move or copy) on a file. Can rename the file as well as change its location,
        and optionally move associated files too.

        :param file_path: The full path of the media file to act on
        :param new_path: Destination path where we want to move/copy the file to
        :param new_base_name: The base filename (no extension) to use during the copy. Use None to keep the same name.
        :param associated_files: Boolean, whether we should copy similarly-named files too
        :param action: function that takes an old path and new path and does an operation with them (move/copy)
        :param subtitles: Boolean, whether we should process subtitles too
        """

        if not action:
            self._log("Must provide an action for the combined file operation", logger.ERROR)
            return

        file_list = [file_path]
        subfolders = ek(os.path.normpath, ek(os.path.dirname, file_path)) != ek(os.path.normpath, sickbeard.TV_DOWNLOAD_DIR)
        if associated_files:
            file_list = file_list + self.list_associated_files(file_path, subfolders=subfolders)
        elif subtitles:
            file_list = file_list + self.list_associated_files(file_path, subtitles_only=True, subfolders=subfolders)

        if not file_list:
            self._log("There were no files associated with " + file_path + ", not moving anything", logger.DEBUG)
            return

        # deal with all files
        for cur_file_path in file_list:
            cur_file_name, cur_extension = cur_file_path.rpartition('.')[0:3:2]

            # check if file have subtitles language
            if cur_extension in SUBTITLE_EXTENSIONS and '.' in cur_file_name:
                cur_lang = cur_file_name.rpartition('.')[-1].lower()
                # pt_BR is a special case, subliminal does not handle it well
                if cur_lang == 'pt-br':
                    cur_lang = 'pt-BR'

                # Check that this is a valid subtitle language for this subtitle, and if so prepend the extension with it so it is retained
                cur_lang_name = sickbeard.subtitles.from_code(cur_lang).name
                if new_base_name and cur_lang == 'pt-BR' or cur_lang_name != 'Undetermined':
                    cur_extension = '.'.join((cur_lang, cur_extension))

            # replace .nfo with .nfo-orig to avoid conflicts
            if cur_extension == 'nfo' and sickbeard.NFO_RENAME is True:
                cur_extension = 'nfo-orig'

            # If new base name then convert name
            if new_base_name:
                new_file_name = '.'.join((new_base_name, cur_extension))
            # if we're not renaming we still want to change extensions sometimes
            else:
                new_file_name = ek(os.path.basename, replace_extension(cur_file_path, cur_extension))

            if sickbeard.SUBTITLES_DIR and cur_extension.endswith(tuple(SUBTITLE_EXTENSIONS)):
                subs_new_path = ek(os.path.join, new_path, sickbeard.SUBTITLES_DIR)
                dir_exists = helpers.makeDir(subs_new_path)
                if not dir_exists:
                    logger.log("Unable to create subtitles folder " + subs_new_path, logger.ERROR)
                else:
                    helpers.chmodAsParent(subs_new_path)
                new_file_path = ek(os.path.join, subs_new_path, new_file_name)
            else:
                new_file_path = ek(os.path.join, new_path, new_file_name)

            action(cur_file_path, new_file_path)

    def _move(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):  # pylint: disable=too-many-arguments
        """
        Move file and set proper permissions

        :param file_path: The full path of the media file to move
        :param new_path: Destination path where we want to move the file to
        :param new_base_name: The base filename (no extension) to use during the move. Use None to keep the same name.
        :param associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_move(cur_file_path, new_file_path):

            self._log("Moving file from " + cur_file_path + " to " + new_file_path, logger.DEBUG)
            try:
                helpers.moveFile(cur_file_path, new_file_path)
                helpers.chmodAsParent(new_file_path)
            except (IOError, OSError) as e:
                self._log("Unable to move file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_move,
                                      subtitles=subtitles)

    def _copy(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):  # pylint: disable=too-many-arguments
        """
        Copy file and set proper permissions

        :param file_path: The full path of the media file to copy
        :param new_path: Destination path where we want to copy the file to
        :param new_base_name: The base filename (no extension) to use during the copy. Use None to keep the same name.
        :param associated_files: Boolean, whether we should copy similarly-named files too
        """

        def _int_copy(cur_file_path, new_file_path):

            self._log("Copying file from " + cur_file_path + " to " + new_file_path, logger.DEBUG)
            try:
                helpers.copyFile(cur_file_path, new_file_path)
                helpers.chmodAsParent(new_file_path)
            except (IOError, OSError) as e:
                self._log("Unable to copy file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_copy,
                                      subtitles=subtitles)

    def _hardlink(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):  # pylint: disable=too-many-arguments
        """
        Hardlink file and set proper permissions

        :param file_path: The full path of the media file to move
        :param new_path: Destination path where we want to create a hard linked file
        :param new_base_name: The base filename (no extension) to use during the link. Use None to keep the same name.
        :param associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_hard_link(cur_file_path, new_file_path):

            self._log("Hard linking file from " + cur_file_path + " to " + new_file_path, logger.DEBUG)
            try:
                helpers.hardlinkFile(cur_file_path, new_file_path)
                helpers.chmodAsParent(new_file_path)
            except (IOError, OSError) as e:
                self._log("Unable to link file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_hard_link, subtitles=subtitles)

    def _moveAndSymlink(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):  # pylint: disable=too-many-arguments
        """
        Move file, symlink source location back to destination, and set proper permissions

        :param file_path: The full path of the media file to move
        :param new_path: Destination path where we want to move the file to create a symbolic link to
        :param new_base_name: The base filename (no extension) to use during the link. Use None to keep the same name.
        :param associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_move_and_sym_link(cur_file_path, new_file_path):

            self._log("Moving then symbolic linking file from " + cur_file_path + " to " + new_file_path, logger.DEBUG)
            try:
                helpers.moveAndSymlinkFile(cur_file_path, new_file_path)
                helpers.chmodAsParent(new_file_path)
            except (IOError, OSError) as e:
                self._log("Unable to link file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files,
                                      action=_int_move_and_sym_link, subtitles=subtitles)

    def _symlink(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):  # pylint: disable=too-many-arguments
        """
        symlink destination to source location, and set proper permissions

        :param file_path: The full path of the media file to move
        :param new_path: Destination path where we want to move the file to create a symbolic link to
        :param new_base_name: The base filename (no extension) to use during the link. Use None to keep the same name.
        :param associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_sym_link(cur_file_path, new_file_path):

            self._log("Creating then symbolic linking file from " + new_file_path + " to " + cur_file_path, logger.DEBUG)
            try:
                helpers.symlink(cur_file_path, new_file_path)
                helpers.chmodAsParent(cur_file_path)
            except (IOError, OSError) as e:
                self._log("Unable to link file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files,
                                      action=_int_sym_link, subtitles=subtitles)


    def _history_lookup(self):
        """
        Look up the NZB name in the history and see if it contains a record for self.nzb_name

        :return: A (indexer_id, season, [], quality, version) tuple. The first two may be None if none were found.
        """

        to_return = (None, None, [], None, None)

        # if we don't have either of these then there's nothing to use to search the history for anyway
        if not self.nzb_name and not self.folder_name:
            self.in_history = False
            return to_return

        # make a list of possible names to use in the search
        names = []
        if self.nzb_name:
            names.append(self.nzb_name)
            if '.' in self.nzb_name:
                names.append(self.nzb_name.rpartition(".")[0])
        if self.folder_name:
            names.append(self.folder_name)

        # search the database for a possible match and return immediately if we find one
        main_db_con = db.DBConnection()
        for curName in names:
            search_name = re.sub(r"[\.\- ]", "_", curName)
            sql_results = main_db_con.select("SELECT showid, season, quality, version, resource FROM history WHERE resource LIKE ? AND (action % 100 = 4 OR action % 100 = 6)", [search_name])

            if not sql_results:
                continue

            indexer_id = int(sql_results[0][b"showid"])
            season = int(sql_results[0][b"season"])
            quality = int(sql_results[0][b"quality"])
            version = int(sql_results[0][b"version"])

            if quality == common.Quality.UNKNOWN:
                quality = None

            show = Show.find(sickbeard.showList, indexer_id)

            self.in_history = True
            self.version = version
            to_return = (show, season, [], quality, version)

            qual_str = common.Quality.qualityStrings[quality] if quality is not None else quality
            self._log("Found result in history for {0} - Season: {1} - Quality: {2} - Version: {3}".format
                      (show.name if show else "UNDEFINED", season, qual_str, version), logger.DEBUG)

            return to_return

        self.in_history = False
        return to_return

    def _finalize(self, parse_result):
        """
        Store parse result if it is complete and final

        :param parse_result: Result of parsers
        """
        self.release_group = parse_result.release_group

        # remember whether it's a proper
        if parse_result.extra_info:
            self.is_proper = re.search(r'\b(proper|repack|real)\b', parse_result.extra_info, re.I) is not None

        # if the result is complete then remember that for later
        # if the result is complete then set release name
        if (parse_result.series_name and ((parse_result.season_number is not None and parse_result.episode_numbers)
            or parse_result.air_date) and parse_result.release_group):

            if not self.release_name:
                self.release_name = helpers.remove_non_release_groups(remove_extension(ek(os.path.basename, parse_result.original_name)))

        else:
            logger.log("Parse result not sufficient (all following have to be set). will not save release name",
                       logger.DEBUG)
            logger.log("Parse result(series_name): " + str(parse_result.series_name), logger.DEBUG)
            logger.log("Parse result(season_number): " + str(parse_result.season_number), logger.DEBUG)
            logger.log("Parse result(episode_numbers): " + str(parse_result.episode_numbers), logger.DEBUG)
            logger.log(" or Parse result(air_date): " + str(parse_result.air_date), logger.DEBUG)
            logger.log("Parse result(release_group): " + str(parse_result.release_group), logger.DEBUG)

    def _analyze_name(self, name):
        """
        Takes a name and tries to figure out a show, season, and episode from it.

        :param name: A string which we want to analyze to determine show info from (six.text_type)

        :return: A (indexer_id, season, [episodes]) tuple. The first two may be None and episodes may be []
        if none were found.
        """

        to_return = (None, None, [], None, None)

        if not name:
            return to_return

        logger.log("Analyzing name " + name, logger.DEBUG)

        name = helpers.remove_non_release_groups(remove_extension(name))

        # parse the name to break it into show name, season, and episode
        try:
            parse_result = NameParser(True, tryIndexers=True).parse(name)
        except (InvalidNameException, InvalidShowException) as error:
            logger.log("{0}".format(error), logger.DEBUG)
            return to_return

        # show object
        show = parse_result.show

        if parse_result.is_air_by_date:
            season = -1
            episodes = [parse_result.air_date]
        else:
            season = parse_result.season_number
            episodes = parse_result.episode_numbers

        to_return = (show, season, episodes, parse_result.quality, None)

        self._finalize(parse_result)
        return to_return

    @staticmethod
    def _build_anidb_episode(connection, filePath):
        """
        Look up anidb properties for an episode

        :param connection: anidb connection handler
        :param filePath: file to check
        :return: episode object
        """
        ep = adba.Episode(connection, filePath=filePath,
                          paramsF=["quality", "anidb_file_name", "crc32"],
                          paramsA=["epno", "english_name", "short_name_list", "other_name", "synonym_list"])

        return ep

    def _add_to_anidb_mylist(self, filePath):
        """
        Adds an episode to anidb mylist

        :param filePath: file to add to mylist
        """
        if helpers.set_up_anidb_connection():
            if not self.anidbEpisode:  # seems like we could parse the name before, now lets build the anidb object
                self.anidbEpisode = self._build_anidb_episode(sickbeard.ADBA_CONNECTION, filePath)

            self._log("Adding the file to the anidb mylist", logger.DEBUG)
            try:
                self.anidbEpisode.add_to_mylist(status=1)  # status = 1 sets the status of the file to "internal HDD"
            except Exception as e:
                self._log("exception msg: " + str(e))

    def _find_info(self):  # pylint: disable=too-many-locals, too-many-branches
        """
        For a given file try to find the showid, season, and episode.

        :return: A (show, season, episodes, quality, version) tuple
        """

        show = season = quality = version = None
        episodes = []

        # try to look up the nzb in history
        attempt_list = [
            self._history_lookup,

            # try to analyze the nzb name
            lambda: self._analyze_name(self.nzb_name),

            # try to analyze the file name
            lambda: self._analyze_name(self.file_name),

            # try to analyze the dir name
            lambda: self._analyze_name(self.folder_name),

            # try to analyze the file + dir names together
            lambda: self._analyze_name(self.file_path),

            # try to analyze the dir + file name together as one name
            lambda: self._analyze_name(self.folder_name + ' ' + self.file_name)
        ]

        # attempt every possible method to get our info
        for cur_attempt in attempt_list:

            try:
                cur_show, cur_season, cur_episodes, cur_quality, cur_version = cur_attempt()
            except (InvalidNameException, InvalidShowException) as error:
                logger.log("{0}".format(error), logger.DEBUG)
                continue

            if not cur_show:
                continue
            else:
                show = cur_show

            if cur_quality and not (self.in_history and quality):
                quality = cur_quality

            # we only get current version for animes from history to prevent issues with old database entries
            if cur_version is not None:
                version = cur_version

            if cur_season is not None:
                season = cur_season
            if cur_episodes:
                episodes = cur_episodes

            # for air-by-date shows we need to look up the season/episode from database
            if season == -1 and show and episodes:
                self._log(
                    "Looks like this is an air-by-date or sports show, attempting to convert the date to season/episode",
                    logger.DEBUG)

                try:
                    airdate = episodes[0].toordinal()
                except AttributeError:
                    self._log("Could not convert to a valid airdate: {0}".format(episodes[0]), logger.DEBUG)
                    episodes = []
                    continue

                main_db_con = db.DBConnection()
                # Ignore season 0 when searching for episode(Conflict between special and regular episode, same air date)
                sql_result = main_db_con.select(
                    "SELECT season, episode FROM tv_episodes WHERE showid = ? and indexer = ? and airdate = ? and season != 0",
                    [show.indexerid, show.indexer, airdate])

                if sql_result:
                    season = int(sql_result[0][b'season'])
                    episodes = [int(sql_result[0][b'episode'])]
                else:
                    # Found no result, try with season 0
                    sql_result = main_db_con.select(
                        "SELECT season, episode FROM tv_episodes WHERE showid = ? and indexer = ? and airdate = ?",
                        [show.indexerid, show.indexer, airdate])
                    if sql_result:
                        season = int(sql_result[0][b'season'])
                        episodes = [int(sql_result[0][b'episode'])]
                    else:
                        self._log(
                            "Unable to find episode with date " +
                            str(episodes[0]) + " for show " + str(show.indexerid) + ", skipping", logger.DEBUG)
                        # we don't want to leave dates in the episode list if we couldn't convert them to real episode numbers
                        episodes = []
                        continue

            # if there's no season then we can hopefully just use 1 automatically
            elif season is None and show:
                main_db_con = db.DBConnection()
                numseasonsSQlResult = main_db_con.select(
                    "SELECT COUNT(DISTINCT season) FROM tv_episodes WHERE showid = ? and indexer = ? and season != 0",
                    [show.indexerid, show.indexer])
                if int(numseasonsSQlResult[0][0]) == 1 and season is None:
                    self._log(
                        "Don't have a season number, but this show appears to only have 1 season, setting season number to 1...",
                        logger.DEBUG)
                    season = 1

            if show and season and episodes:
                return show, season, episodes, quality, version

        return show, season, episodes, quality, version

    def _get_ep_obj(self, show, season, episodes):
        """
        Retrieve the TVEpisode object requested.

        :param show: The show object belonging to the show we want to process
        :param season: The season of the episode (int)
        :param episodes: A list of episodes to find (list of ints)

        :return: If the episode(s) can be found then a TVEpisode object with the correct related eps will
        be instantiated and returned. If the episode can't be found then None will be returned.
        """

        root_ep = None
        for cur_episode in episodes:
            self._log("Retrieving episode object for " + str(season) + "x" + str(cur_episode), logger.DEBUG)

            # now that we've figured out which episode this file is just load it manually
            try:
                curEp = show.getEpisode(season, cur_episode)
                if not curEp:
                    raise EpisodeNotFoundException()
            except EpisodeNotFoundException as e:
                self._log("Unable to create episode: " + ex(e), logger.DEBUG)
                raise EpisodePostProcessingFailedException()

            # associate all the episodes together under a single root episode
            if root_ep is None:
                root_ep = curEp
                root_ep.relatedEps = []
            elif curEp not in root_ep.relatedEps:
                root_ep.relatedEps.append(curEp)

        return root_ep

    def _get_quality(self, ep_obj):
        """
        Determines the quality of the file that is being post processed, first by checking if it is directly
        available in the TVEpisode's status or otherwise by parsing through the data available.

        :param ep_obj: The TVEpisode object related to the file we are post processing
        :return: A quality value found in common.Quality
        """

        # if there is a quality available in the status then we don't need to bother guessing from the filename
        if ep_obj.status in common.Quality.SNATCHED + common.Quality.SNATCHED_PROPER + common.Quality.SNATCHED_BEST:
            ep_status_, ep_quality = common.Quality.splitCompositeStatus(ep_obj.status)  # @UnusedVariable
            if ep_quality != common.Quality.UNKNOWN:
                self._log(
                    "The old status had a quality in it, using that: " + common.Quality.qualityStrings[ep_quality],
                    logger.DEBUG)
                return ep_quality

        # nzb name is the most reliable if it exists, followed by folder name and lastly file name
        name_list = [self.nzb_name, self.folder_name, self.file_name]

        # search all possible names for our new quality, in case the file or dir doesn't have it
        for cur_name in name_list:

            # some stuff might be None at this point still
            if not cur_name:
                continue

            ep_quality = common.Quality.nameQuality(cur_name, ep_obj.show.is_anime)
            self._log(
                "Looking up quality for name " + cur_name + ", got " + common.Quality.qualityStrings[ep_quality],
                logger.DEBUG)

            # if we find a good one then use it
            if ep_quality != common.Quality.UNKNOWN:
                logger.log(cur_name + " looks like it has quality " + common.Quality.qualityStrings[
                    ep_quality] + ", using that", logger.DEBUG)
                return ep_quality

        # Try getting quality from the episode (snatched) status
        if ep_obj.status in common.Quality.SNATCHED + common.Quality.SNATCHED_PROPER + common.Quality.SNATCHED_BEST:
            ep_status_, ep_quality = common.Quality.splitCompositeStatus(ep_obj.status)  # @UnusedVariable
            if ep_quality != common.Quality.UNKNOWN:
                self._log(
                    "The old status had a quality in it, using that: " + common.Quality.qualityStrings[ep_quality],
                    logger.DEBUG)
                return ep_quality

        # Try guessing quality from the file name
        ep_quality = common.Quality.nameQuality(self.file_path)
        self._log(
            "Guessing quality for name " + self.file_name + ", got " + common.Quality.qualityStrings[ep_quality],
            logger.DEBUG)
        if ep_quality != common.Quality.UNKNOWN:
            logger.log(self.file_name + " looks like it has quality " + common.Quality.qualityStrings[
                ep_quality] + ", using that", logger.DEBUG)
            return ep_quality

        return ep_quality

    def _run_extra_scripts(self, ep_obj):
        """
        Executes any extra scripts defined in the config.

        :param ep_obj: The object to use when calling the extra script
        """

        if not sickbeard.EXTRA_SCRIPTS:
            return

        file_path = self.file_path
        if isinstance(file_path, six.text_type):
            try:
                file_path = file_path.encode(sickbeard.SYS_ENCODING)
            except UnicodeEncodeError:
                # ignore it
                pass

        ep_location = ep_obj.location
        if isinstance(ep_location, six.text_type):
            try:
                ep_location = ep_location.encode(sickbeard.SYS_ENCODING)
            except UnicodeEncodeError:
                # ignore it
                pass

        for curScriptName in sickbeard.EXTRA_SCRIPTS:
            if isinstance(curScriptName, six.text_type):
                try:
                    curScriptName = curScriptName.encode(sickbeard.SYS_ENCODING)
                except UnicodeEncodeError:
                    # ignore it
                    pass

            # generate a safe command line string to execute the script and provide all the parameters
            script_cmd = [piece for piece in re.split(r'(\'.*?\'|".*?"| )', curScriptName) if piece.strip()]
            script_cmd[0] = ek(os.path.abspath, script_cmd[0])
            self._log("Absolute path to script: {0}".format(script_cmd[0]), logger.DEBUG)

            script_cmd += [
                ep_location, file_path, str(ep_obj.show.indexerid),
                str(ep_obj.season), str(ep_obj.episode), str(ep_obj.airdate)
            ]

            # use subprocess to run the command and capture output
            self._log("Executing command: {0}".format(script_cmd))
            try:
                p = subprocess.Popen(
                    script_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, cwd=sickbeard.PROG_DIR
                )
                out, err_ = p.communicate()

                self._log("Script result: {0}".format(out), logger.DEBUG)

            except Exception as e:
                self._log("Unable to run extra_script: {0}".format(ex(e)))

    def _is_priority(self, ep_obj, new_ep_quality):  # pylint: disable=too-many-return-statements
        """
        Determines if the episode is a priority download or not (if it is expected). Episodes which are expected
        (snatched) or larger than the existing episode are priority, others are not.

        :param ep_obj: The TVEpisode object in question
        :param new_ep_quality: The quality of the episode that is being processed
        :return: True if the episode is priority, False otherwise.
        """

        if self.is_priority:
            return True

        old_ep_status_, old_ep_quality = common.Quality.splitCompositeStatus(ep_obj.status)

        # if SR downloaded this on purpose we likely have a priority download
        if self.in_history or ep_obj.status in common.Quality.SNATCHED + common.Quality.SNATCHED_PROPER + common.Quality.SNATCHED_BEST:
            # if the episode is still in a snatched status, then we can assume we want this
            if not self.in_history:
                self._log("SR snatched this episode and it is not processed before", logger.DEBUG)
                return True

            # if it's in history, we only want it if the new quality is higher or if it's a proper of equal or higher quality
            if new_ep_quality > old_ep_quality and new_ep_quality != common.Quality.UNKNOWN:
                self._log("SR snatched this episode and it is a higher quality so I'm marking it as priority", logger.DEBUG)
                return True

            if self.is_proper and new_ep_quality >= old_ep_quality and new_ep_quality != common.Quality.UNKNOWN:
                self._log("SR snatched this episode and it is a proper of equal or higher quality so I'm marking it as priority", logger.DEBUG)
                return True

            return False

        # if the user downloaded it manually and it's higher quality than the existing episode then it's priority
        if new_ep_quality > old_ep_quality and new_ep_quality != common.Quality.UNKNOWN:
            self._log("This was manually downloaded but it appears to be better quality than what we have so I'm marking it as priority", logger.DEBUG)
            return True

        # if the user downloaded it manually and it appears to be a PROPER/REPACK then it's priority
        if self.is_proper and new_ep_quality >= old_ep_quality and new_ep_quality != common.Quality.UNKNOWN:
            self._log("This was manually downloaded but it appears to be a proper so I'm marking it as priority", logger.DEBUG)
            return True

        return False

    def process(self):  # pylint: disable=too-many-return-statements, too-many-locals, too-many-branches, too-many-statements
        """
        Post-process a given file

        :return: True on success, False on failure
        """

        self._log("Processing " + self.file_path + " (" + str(self.nzb_name) + ")")

        if ek(os.path.isdir, self.file_path):
            self._log("File {0} seems to be a directory".format(self.file_path))
            return False

        if not ek(os.path.exists, self.file_path):
            self._log("File {0} doesn't exist, did unrar fail?".format(self.file_path))
            return False

        for ignore_file in self.IGNORED_FILESTRINGS:
            if ignore_file in self.file_path:
                self._log("File {0} is ignored type, skipping".format(self.file_path))
                return False

        # reset per-file stuff
        self.in_history = False

        # reset the anidb episode object
        self.anidbEpisode = None

        # try to find the file info
        (show, season, episodes, quality, version) = self._find_info()
        if not show:
            self._log("This show isn't in your list, you need to add it to SR before post-processing an episode")
            raise EpisodePostProcessingFailedException()
        elif season is None or not episodes:
            self._log("Not enough information to determine what episode this is. Quitting post-processing")
            return False

        # retrieve/create the corresponding TVEpisode objects
        ep_obj = self._get_ep_obj(show, season, episodes)
        old_ep_status_, old_ep_quality = common.Quality.splitCompositeStatus(ep_obj.status)

        # get the quality of the episode we're processing
        if quality and not common.Quality.qualityStrings[quality] == 'Unknown':
            self._log("Snatch history had a quality in it, using that: " + common.Quality.qualityStrings[quality],
                      logger.DEBUG)
            new_ep_quality = quality
        else:
            new_ep_quality = self._get_quality(ep_obj)

        logger.log("Quality of the episode we're processing: {0}".format(common.Quality.qualityStrings[new_ep_quality]), logger.DEBUG)

        # see if this is a priority download (is it snatched, in history, PROPER, or BEST)
        priority_download = self._is_priority(ep_obj, new_ep_quality)
        self._log("Is ep a priority download: " + str(priority_download), logger.DEBUG)

        # get the version of the episode we're processing
        if version:
            self._log("Snatch history had a version in it, using that: v" + str(version),
                      logger.DEBUG)
            new_ep_version = version
        else:
            new_ep_version = -1

        # check for an existing file
        existing_file_status = self._checkForExistingFile(ep_obj.location)

        if not priority_download:
            if existing_file_status == PostProcessor.EXISTS_SAME:
                self._log("File exists and new file is same size, pretending we did something")
                return True

            if new_ep_quality <= old_ep_quality and old_ep_quality != common.Quality.UNKNOWN and existing_file_status != PostProcessor.DOESNT_EXIST:
                if self.is_proper and new_ep_quality == old_ep_quality:
                    self._log("New file is a proper/repack, marking it safe to replace")
                else:
                    allowed_qualities_, preferred_qualities = common.Quality.splitQuality(int(show.quality))
                    if new_ep_quality not in preferred_qualities:
                        self._log("File exists and new file quality is not in a preferred quality list, marking it unsafe to replace")
                        return False

            # Check if the processed file season is already in our indexer. If not, the file is most probably mislabled/fake and will be skipped
            # Only proceed if the file season is > 0
            if int(ep_obj.season) > 0:
                main_db_con = db.DBConnection()
                max_season = main_db_con.select(
                    "SELECT MAX(season) FROM tv_episodes WHERE showid = ? and indexer = ?", [show.indexerid, show.indexer])

                if not isinstance(max_season[0][0], int) or max_season[0][0] < 0:
                    self._log(
                        "File has season {0}, while the database does not have any known seasons yet. "
                        "Try forcing a full update on the show and process this file again. "
                        "The file may be incorrectly labeled or fake, aborting.".format(ep_obj.season)
                    )
                    return False

                # If the file season (ep_obj.season) is bigger than the indexer season (max_season[0][0]), skip the file
                if int(ep_obj.season) > max_season[0][0]:
                    self._log("File has season {0}, while the indexer is on season {1}. "
                              "Try forcing a full update on the show and process this file again. "
                              "The file may be incorrectly labeled or fake, aborting.".format(ep_obj.season, max_season[0][0]))
                    return False

        # if the file is priority then we're going to replace it even if it exists
        else:
            self._log(
                "This download is marked a priority download so I'm going to replace an existing file if I find one")

        # try to find out if we have enough space to perform the copy or move action.
        if sickbeard.USE_FREE_SPACE_CHECK and not helpers.is_file_locked(self.file_path):
            if not verify_freespace(self.file_path, ep_obj.show._location, [ep_obj] + ep_obj.relatedEps, method=self.process_method):  # pylint: disable=protected-access
                self._log("Not enough space to continue PP, exiting", logger.WARNING)
                return False
        else:
            self._log("Unable to determine needed file space as the source file is locked for access")

        # delete the existing file (and company)
        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            try:
                self._delete(cur_ep.location, associated_files=True)

                # clean up any left over folders
                if cur_ep.location:
                    helpers.delete_empty_folders(ek(os.path.dirname, cur_ep.location), keep_dir=ep_obj.show._location)  # pylint: disable=protected-access
            except (OSError, IOError):
                raise EpisodePostProcessingFailedException("Unable to delete the existing files")

            # set the status of the episodes
            # for curEp in [ep_obj] + ep_obj.relatedEps:
            #    curEp.status = common.Quality.compositeStatus(common.SNATCHED, new_ep_quality)

        # if the show directory doesn't exist then make it if allowed
        if not ek(os.path.isdir, ep_obj.show._location) and sickbeard.CREATE_MISSING_SHOW_DIRS:  # pylint: disable=protected-access
            self._log("Show directory doesn't exist, creating it", logger.DEBUG)
            try:
                ek(os.mkdir, ep_obj.show._location)  # pylint: disable=protected-access
                helpers.chmodAsParent(ep_obj.show._location)  # pylint: disable=protected-access

                # do the library update for synoindex
                notifiers.synoindex_notifier.addFolder(ep_obj.show._location)  # pylint: disable=protected-access
            except (OSError, IOError):
                raise EpisodePostProcessingFailedException("Unable to create the show directory: " + ep_obj.show._location)  # pylint: disable=protected-access

            # get metadata for the show (but not episode because it hasn't been fully processed)
            ep_obj.show.writeMetadata(True)

        # update the ep info before we rename so the quality & release name go into the name properly
        sql_l = []

        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            with cur_ep.lock:

                if self.release_name:
                    self._log("Found release name " + self.release_name, logger.DEBUG)
                    cur_ep.release_name = self.release_name
                elif self.file_name:
                    # If we can't get the release name we expect, save the original release name instead
                    self._log("Using original release name " + self.file_name, logger.DEBUG)
                    cur_ep.release_name = self.file_name
                else:
                    cur_ep.release_name = ""

                cur_ep.status = common.Quality.compositeStatus(common.DOWNLOADED, new_ep_quality)

                cur_ep.subtitles = ''

                cur_ep.subtitles_searchcount = 0

                cur_ep.subtitles_lastsearch = '0001-01-01 00:00:00'

                cur_ep.is_proper = self.is_proper

                cur_ep.version = new_ep_version

                if self.release_group:
                    cur_ep.release_group = self.release_group
                else:
                    cur_ep.release_group = ""

                sql_l.append(cur_ep.get_sql())

        # Just want to keep this consistent for failed handling right now
        releaseName = show_name_helpers.determineReleaseName(self.folder_path, self.nzb_name)
        if releaseName is not None:
            failed_history.logSuccess(releaseName)
        else:
            self._log("Couldn't find release in snatch history", logger.WARNING)

        # find the destination folder
        try:
            proper_path = ep_obj.proper_path()
            proper_absolute_path = ek(os.path.join, ep_obj.show.location, proper_path)

            dest_path = ek(os.path.dirname, proper_absolute_path)
        except ShowDirectoryNotFoundException:
            raise EpisodePostProcessingFailedException(
                "Unable to post-process an episode if the show dir doesn't exist, quitting")

        self._log("Destination folder for this episode: " + dest_path, logger.DEBUG)

        # create any folders we need
        helpers.make_dirs(dest_path)

        # figure out the base name of the resulting episode file
        if sickbeard.RENAME_EPISODES:
            orig_extension = self.file_name.rpartition('.')[-1]
            new_base_name = ek(os.path.basename, proper_path)
            new_file_name = new_base_name + '.' + orig_extension

        else:
            # if we're not renaming then there's no new base name, we'll just use the existing name
            new_base_name = None
            new_file_name = self.file_name

        # add to anidb
        if ep_obj.show.is_anime and sickbeard.ANIDB_USE_MYLIST:
            self._add_to_anidb_mylist(self.file_path)

        try:
            # move the episode and associated files to the show dir
            if self.process_method == "copy":
                if helpers.is_file_locked(self.file_path, False):
                    raise EpisodePostProcessingFailedException("File is locked for reading")
                self._copy(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                           sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "move":
                if helpers.is_file_locked(self.file_path, True):
                    raise EpisodePostProcessingFailedException("File is locked for reading/writing")
                self._move(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                           sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "hardlink":
                self._hardlink(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                               sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "symlink":
                if helpers.is_file_locked(self.file_path, True):
                    raise EpisodePostProcessingFailedException("File is locked for reading/writing")
                self._moveAndSymlink(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                                     sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "symlink_reversed":
                self._symlink(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                                     sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            else:
                logger.log("Unknown process method: " + str(self.process_method), logger.ERROR)
                raise EpisodePostProcessingFailedException("Unable to move the files to their new home")
        except (OSError, IOError):
            raise EpisodePostProcessingFailedException("Unable to move the files to their new home")

        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            with cur_ep.lock:
                cur_ep.location = ek(os.path.join, dest_path, new_file_name)
                # download subtitles
                if sickbeard.USE_SUBTITLES and ep_obj.show.subtitles \
                    and (cur_ep.season != 0 or sickbeard.SUBTITLES_INCLUDE_SPECIALS):
                    cur_ep.refreshSubtitles()
                    cur_ep.download_subtitles(force=True)
                sql_l.append(cur_ep.get_sql())

        # now that processing has finished, we can put the info in the DB. If we do it earlier, then when processing fails, it won't try again.
        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

        ep_obj.airdateModifyStamp()

        if sickbeard.USE_ICACLS and os.name == 'nt':
            os.popen('icacls "' + ep_obj._location + '"* /reset /T')

        # generate nfo/tbn
        try:
            ep_obj.createMetaFiles()
        except Exception:
            logger.log("Could not create/update meta files. Continuing with postProcessing...")

        # log it to history
        history.logDownload(ep_obj, self.file_path, new_ep_quality, self.release_group, new_ep_version)

        # If any notification fails, don't stop postProcessor
        try:
            # send notifications
            notifiers.notify_download(ep_obj._format_pattern('%SN - %Sx%0E - %EN - %QN'))  # pylint: disable=protected-access

            # do the library update for KODI
            notifiers.kodi_notifier.update_library(ep_obj.show.name)

            # do the library update for Plex
            notifiers.plex_notifier.update_library(ep_obj)

            # do the library update for EMBY
            notifiers.emby_notifier.update_library(ep_obj.show)

            # do the library update for NMJ
            # nmj_notifier kicks off its library update when the notify_download is issued (inside notifiers)

            # do the library update for Synology Indexer
            notifiers.synoindex_notifier.addFile(ep_obj.location)

            # do the library update for pyTivo
            notifiers.pytivo_notifier.update_library(ep_obj)

            # do the library update for Trakt
            notifiers.trakt_notifier.update_library(ep_obj)
        except Exception:
            logger.log("Some notifications could not be sent. Continuing with postProcessing...")

        self._run_extra_scripts(ep_obj)

        return True
