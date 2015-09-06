# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import glob
import fnmatch
import os
import re
import subprocess
import stat

import sickbeard

from sickbeard import db
from sickbeard import common
from sickbeard import exceptions
from sickbeard import helpers
from sickbeard import history
from sickbeard import logger
from sickbeard import notifiers
from sickbeard import show_name_helpers
from sickbeard import failed_history
from sickbeard import encodingKludge as ek
from sickbeard.exceptions import ex

from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException

import adba
from sickbeard.helpers import verify_freespace


class PostProcessor(object):
    """
    A class which will process a media file according to the post processing settings in the config.
    """

    EXISTS_LARGER = 1
    EXISTS_SAME = 2
    EXISTS_SMALLER = 3
    DOESNT_EXIST = 4

    IGNORED_FILESTRINGS = ["/.AppleDouble/", ".DS_Store"]

    def __init__(self, file_path, nzb_name=None, process_method=None, is_priority=None):
        """
        Creates a new post processor with the given file path and optionally an NZB name.

        file_path: The path to the file to be processed
        nzb_name: The name of the NZB which resulted in this file being downloaded (optional)
        """
        # absolute path to the folder that is being processed
        self.folder_path = ek.ek(os.path.dirname, ek.ek(os.path.abspath, file_path))

        # full path to file
        self.file_path = file_path

        # file name only
        self.file_name = ek.ek(os.path.basename, file_path)

        # the name of the folder only
        self.folder_name = ek.ek(os.path.basename, self.folder_path)

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

    def _log(self, message, level=logger.INFO):
        """
        A wrapper for the internal logger which also keeps track of messages and saves them to a string for later.

        message: The string to log (unicode)
        level: The log level to use (optional)
        """
        logger.log(message, level)
        self.log += message + '\n'

    def _checkForExistingFile(self, existing_file):
        """
        Checks if a file exists already and if it does whether it's bigger or smaller than
        the file we are post processing

        existing_file: The file to compare to

        Returns:
            DOESNT_EXIST if the file doesn't exist
            EXISTS_LARGER if the file exists and is larger than the file we are post processing
            EXISTS_SMALLER if the file exists and is smaller than the file we are post processing
            EXISTS_SAME if the file exists and is the same size as the file we are post processing
        """

        if not existing_file:
            self._log(u"There is no existing file so there's no worries about replacing it", logger.DEBUG)
            return PostProcessor.DOESNT_EXIST

        # if the new file exists, return the appropriate code depending on the size
        if ek.ek(os.path.isfile, existing_file):

            # see if it's bigger than our old file
            if ek.ek(os.path.getsize, existing_file) > ek.ek(os.path.getsize, self.file_path):
                self._log(u"File " + existing_file + " is larger than " + self.file_path, logger.DEBUG)
                return PostProcessor.EXISTS_LARGER

            elif ek.ek(os.path.getsize, existing_file) == ek.ek(os.path.getsize, self.file_path):
                self._log(u"File " + existing_file + " is the same size as " + self.file_path, logger.DEBUG)
                return PostProcessor.EXISTS_SAME

            else:
                self._log(u"File " + existing_file + " is smaller than " + self.file_path, logger.DEBUG)
                return PostProcessor.EXISTS_SMALLER

        else:
            self._log(u"File " + existing_file + " doesn't exist so there's no worries about replacing it",
                      logger.DEBUG)
            return PostProcessor.DOESNT_EXIST

    def list_associated_files(self, file_path, base_name_only=False, subtitles_only=False, subfolders=False):
        """
        For a given file path searches for files with the same name but different extension and returns their absolute paths

        file_path: The file to check for associated files

        base_name_only: False add extra '.' (conservative search) to file_path minus extension

        Returns: A list containing all files which are associated to the given file
        """
        def recursive_glob(treeroot, pattern):
            results = []
            for base, dirs, files in os.walk(treeroot):
                goodfiles = fnmatch.filter(files, pattern)
                results.extend(os.path.join(base, f) for f in goodfiles)
            return results

        if not file_path:
            return []

        file_path_list = []

        if subfolders:
            base_name = ek.ek(os.path.basename, file_path).rpartition('.')[0]
        else:
            base_name = file_path.rpartition('.')[0]

        if not base_name_only:
            base_name = base_name + '.'

        # don't strip it all and use cwd by accident
        if not base_name:
            return []

        # don't confuse glob with chars we didn't mean to use
        base_name = re.sub(r'[\[\]\*\?]', r'[\g<0>]', base_name)

        if subfolders: # subfolders are only checked in show folder, so names will always be exactly alike
            filelist = ek.ek(recursive_glob, ek.ek(os.path.dirname, file_path), base_name + '*') # just create the list of all files starting with the basename
        else: # this is called when PP, so we need to do the filename check case-insensitive
            filelist = []

            checklist = ek.ek(glob.glob, helpers.fixGlob(ek.ek(os.path.join, ek.ek(os.path.dirname, file_path), '*'))) # get a list of all the files in the folder
            for filefound in checklist: # loop through all the files in the folder, and check if they are the same name even when the cases don't match
                file_name = filefound.rpartition('.')[0]
                if not base_name_only:
                    file_name = file_name + '.'
                if file_name.lower() == base_name.lower(): # if there's no difference in the filename add it to the filelist
                    filelist.append(filefound)


        for associated_file_path in filelist:
            # only add associated to list
            if associated_file_path == file_path:
                continue
            # only list it if the only non-shared part is the extension or if it is a subtitle
            if subtitles_only and not associated_file_path[len(associated_file_path) - 3:] in common.subtitleExtensions:
                continue

            # Exclude .rar files from associated list
            if re.search('(^.+\.(rar|r\d+)$)', associated_file_path):
                continue

            if ek.ek(os.path.isfile, associated_file_path):
                file_path_list.append(associated_file_path)

        if file_path_list:
            self._log(u"Found the following associated files: " + str(file_path_list), logger.DEBUG)
        else:
            self._log(u"No associated files were during this pass", logger.DEBUG)

        return file_path_list

    def _delete(self, file_path, associated_files=False):
        """
        Deletes the file and optionally all associated files.

        file_path: The file to delete
        associated_files: True to delete all files which differ only by extension, False to leave them
        """

        if not file_path:
            return

        # figure out which files we want to delete
        file_list = [file_path]
        if associated_files:
            file_list = file_list + self.list_associated_files(file_path, base_name_only=True, subfolders=True)

        if not file_list:
            self._log(u"There were no files associated with " + file_path + ", not deleting anything", logger.DEBUG)
            return

        # delete the file and any other files which we want to delete
        for cur_file in file_list:
            if ek.ek(os.path.isfile, cur_file):
                self._log(u"Deleting file " + cur_file, logger.DEBUG)
                # check first the read-only attribute
                file_attribute = ek.ek(os.stat, cur_file)[0]
                if (not file_attribute & stat.S_IWRITE):
                    # File is read-only, so make it writeable
                    self._log('Read only mode on file ' + cur_file + ' Will try to make it writeable', logger.DEBUG)
                    try:
                        ek.ek(os.chmod, cur_file, stat.S_IWRITE)
                    except:
                        self._log(u'Cannot change permissions of ' + cur_file, logger.WARNING)

                ek.ek(os.remove, cur_file)

                # do the library update for synoindex
                notifiers.synoindex_notifier.deleteFile(cur_file)

    def _combined_file_operation(self, file_path, new_path, new_base_name, associated_files=False, action=None,
                                 subtitles=False):
        """
        Performs a generic operation (move or copy) on a file. Can rename the file as well as change its location,
        and optionally move associated files too.

        file_path: The full path of the media file to act on
        new_path: Destination path where we want to move/copy the file to
        new_base_name: The base filename (no extension) to use during the copy. Use None to keep the same name.
        associated_files: Boolean, whether we should copy similarly-named files too
        action: function that takes an old path and new path and does an operation with them (move/copy)
        """

        if not action:
            self._log(u"Must provide an action for the combined file operation", logger.ERROR)
            return

        file_list = [file_path]
        if associated_files:
            file_list = file_list + self.list_associated_files(file_path)
        elif subtitles:
            file_list = file_list + self.list_associated_files(file_path, subtitles_only=True)

        if not file_list:
            self._log(u"There were no files associated with " + file_path + ", not moving anything", logger.DEBUG)
            return

        # create base name with file_path (media_file without .extension)
        old_base_name = file_path.rpartition('.')[0]
        old_base_name_length = len(old_base_name)

        # deal with all files
        for cur_file_path in file_list:

            cur_file_name = ek.ek(os.path.basename, cur_file_path)

            # get the extension without .
            cur_extension = cur_file_path[old_base_name_length + 1:]

            # check if file have subtitles language
            if os.path.splitext(cur_extension)[1][1:] in common.subtitleExtensions:
                cur_lang = os.path.splitext(cur_extension)[0]
                if cur_lang in subtitles.wantedLanguages():
                    cur_extension = cur_lang + os.path.splitext(cur_extension)[1]

            # replace .nfo with .nfo-orig to avoid conflicts
            if cur_extension == 'nfo' and sickbeard.NFO_RENAME == True:
                cur_extension = 'nfo-orig'

            # If new base name then convert name
            if new_base_name:
                new_file_name = new_base_name + '.' + cur_extension
            # if we're not renaming we still want to change extensions sometimes
            else:
                new_file_name = helpers.replaceExtension(cur_file_name, cur_extension)

            if sickbeard.SUBTITLES_DIR and cur_extension in common.subtitleExtensions:
                subs_new_path = ek.ek(os.path.join, new_path, sickbeard.SUBTITLES_DIR)
                dir_exists = helpers.makeDir(subs_new_path)
                if not dir_exists:
                    logger.log(u"Unable to create subtitles folder " + subs_new_path, logger.ERROR)
                else:
                    helpers.chmodAsParent(subs_new_path)
                new_file_path = ek.ek(os.path.join, subs_new_path, new_file_name)
            else:
                new_file_path = ek.ek(os.path.join, new_path, new_file_name)

            action(cur_file_path, new_file_path)

    def _move(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):
        """
        file_path: The full path of the media file to move
        new_path: Destination path where we want to move the file to
        new_base_name: The base filename (no extension) to use during the move. Use None to keep the same name.
        associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_move(cur_file_path, new_file_path):

            self._log(u"Moving file from " + cur_file_path + " to " + new_file_path, logger.DEBUG)
            try:
                helpers.moveFile(cur_file_path, new_file_path)
                helpers.chmodAsParent(new_file_path)
            except (IOError, OSError), e:
                self._log("Unable to move file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_move,
                                      subtitles=subtitles)

    def _copy(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):
        """
        file_path: The full path of the media file to copy
        new_path: Destination path where we want to copy the file to
        new_base_name: The base filename (no extension) to use during the copy. Use None to keep the same name.
        associated_files: Boolean, whether we should copy similarly-named files too
        """

        def _int_copy(cur_file_path, new_file_path):

            self._log(u"Copying file from " + cur_file_path + " to " + new_file_path, logger.DEBUG)
            try:
                helpers.copyFile(cur_file_path, new_file_path)
                helpers.chmodAsParent(new_file_path)
            except (IOError, OSError), e:
                logger.log("Unable to copy file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_copy,
                                      subtitles=subtitles)


    def _hardlink(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):
        """
        file_path: The full path of the media file to move
        new_path: Destination path where we want to create a hard linked file
        new_base_name: The base filename (no extension) to use during the link. Use None to keep the same name.
        associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_hard_link(cur_file_path, new_file_path):

            self._log(u"Hard linking file from " + cur_file_path + " to " + new_file_path, logger.DEBUG)
            try:
                helpers.hardlinkFile(cur_file_path, new_file_path)
                helpers.chmodAsParent(new_file_path)
            except (IOError, OSError), e:
                self._log("Unable to link file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_hard_link)

    def _moveAndSymlink(self, file_path, new_path, new_base_name, associated_files=False, subtitles=False):
        """
        file_path: The full path of the media file to move
        new_path: Destination path where we want to move the file to create a symbolic link to
        new_base_name: The base filename (no extension) to use during the link. Use None to keep the same name.
        associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_move_and_sym_link(cur_file_path, new_file_path):

            self._log(u"Moving then symbolic linking file from " + cur_file_path + " to " + new_file_path, logger.DEBUG)
            try:
                helpers.moveAndSymlinkFile(cur_file_path, new_file_path)
                helpers.chmodAsParent(new_file_path)
            except (IOError, OSError), e:
                self._log("Unable to link file " + cur_file_path + " to " + new_file_path + ": " + ex(e), logger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files,
                                      action=_int_move_and_sym_link)

    def _history_lookup(self):
        """
        Look up the NZB name in the history and see if it contains a record for self.nzb_name

        Returns a (indexer_id, season, [], quality, version) tuple. The first two may be None if none were found.
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
        myDB = db.DBConnection()
        for curName in names:
            search_name = re.sub("[\.\-\ ]", "_", curName)
            sql_results = myDB.select("SELECT * FROM history WHERE resource LIKE ?", [search_name])

            if len(sql_results) == 0:
                continue

            indexer_id = int(sql_results[0]["showid"])
            season = int(sql_results[0]["season"])
            quality = int(sql_results[0]["quality"])
            version = int(sql_results[0]["version"])

            if quality == common.Quality.UNKNOWN:
                quality = None

            show = helpers.findCertainShow(sickbeard.showList, indexer_id)

            self.in_history = True
            self.version = version
            to_return = (show, season, [], quality, version)
            self._log("Found result in history: " + str(to_return), logger.DEBUG)

            return to_return

        self.in_history = False
        return to_return

    def _finalize(self, parse_result):
        self.release_group = parse_result.release_group

        # remember whether it's a proper
        if parse_result.extra_info:
            self.is_proper = re.search('(^|[\. _-])(proper|repack)([\. _-]|$)', parse_result.extra_info, re.I) != None

        # if the result is complete then remember that for later
        # if the result is complete then set release name
        if parse_result.series_name and ((parse_result.season_number is not None and parse_result.episode_numbers)
                                         or parse_result.air_date) and parse_result.release_group:

            if not self.release_name:
                self.release_name = helpers.remove_extension(ek.ek(os.path.basename, parse_result.original_name))

        else:
            logger.log(u"Parse result not sufficient (all following have to be set). will not save release name",
                       logger.DEBUG)
            logger.log(u"Parse result(series_name): " + str(parse_result.series_name), logger.DEBUG)
            logger.log(u"Parse result(season_number): " + str(parse_result.season_number), logger.DEBUG)
            logger.log(u"Parse result(episode_numbers): " + str(parse_result.episode_numbers), logger.DEBUG)
            logger.log(u" or Parse result(air_date): " + str(parse_result.air_date), logger.DEBUG)
            logger.log(u"Parse result(release_group): " + str(parse_result.release_group), logger.DEBUG)


    def _analyze_name(self, name, file=True):
        """
        Takes a name and tries to figure out a show, season, and episode from it.

        name: A string which we want to analyze to determine show info from (unicode)

        Returns a (indexer_id, season, [episodes]) tuple. The first two may be None and episodes may be []
        if none were found.
        """

        to_return = (None, None, [], None, None)

        if not name:
            return to_return

        logger.log(u"Analyzing name " + repr(name), logger.DEBUG)

        name = helpers.remove_non_release_groups(helpers.remove_extension(name))

        # parse the name to break it into show name, season, and episode
        np = NameParser(file, tryIndexers=True, trySceneExceptions=True)
        parse_result = np.parse(name)

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

    def _build_anidb_episode(self, connection, filePath):
        ep = adba.Episode(connection, filePath=filePath,
                          paramsF=["quality", "anidb_file_name", "crc32"],
                          paramsA=["epno", "english_name", "short_name_list", "other_name", "synonym_list"])

        return ep

    def _add_to_anidb_mylist(self, filePath):
        if helpers.set_up_anidb_connection():
            if not self.anidbEpisode:  # seams like we could parse the name before, now lets build the anidb object
                self.anidbEpisode = self._build_anidb_episode(sickbeard.ADBA_CONNECTION, filePath)

            self._log(u"Adding the file to the anidb mylist", logger.DEBUG)
            try:
                self.anidbEpisode.add_to_mylist(status=1)  # status = 1 sets the status of the file to "internal HDD"
            except Exception, e:
                self._log(u"exception msg: " + str(e))

    def _find_info(self):
        """
        For a given file try to find the showid, season, and episode.
        """

        show = season = quality = version = None
        episodes = []

        # try to look up the nzb in history
        attempt_list = [self._history_lookup,

                        # try to analyze the nzb name
                        lambda: self._analyze_name(self.nzb_name),

                        # try to analyze the file name
                        lambda: self._analyze_name(self.file_name),

                        # try to analyze the dir name
                        lambda: self._analyze_name(self.folder_name),

                        # try to analyze the file + dir names together
                        lambda: self._analyze_name(self.file_path),

                        # try to analyze the dir + file name together as one name
                        lambda: self._analyze_name(self.folder_name + u' ' + self.file_name)
        ]

        # attempt every possible method to get our info
        for cur_attempt in attempt_list:

            try:
                (cur_show, cur_season, cur_episodes, cur_quality, cur_version) = cur_attempt()
            except (InvalidNameException, InvalidShowException), e:
                logger.log(u"Unable to parse, skipping: " + ex(e), logger.DEBUG)
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

            if cur_season != None:
                season = cur_season
            if cur_episodes:
                episodes = cur_episodes

            # for air-by-date shows we need to look up the season/episode from database
            if season == -1 and show and episodes:
                self._log(
                    u"Looks like this is an air-by-date or sports show, attempting to convert the date to season/episode",
                    logger.DEBUG)
                airdate = episodes[0].toordinal()
                myDB = db.DBConnection()
                # Ignore season 0 when searching for episode(Conflict between special and regular episode, same air date)
                sql_result = myDB.select(
                    "SELECT season, episode FROM tv_episodes WHERE showid = ? and indexer = ? and airdate = ? and season != 0",
                    [show.indexerid, show.indexer, airdate])

                if sql_result:
                    season = int(sql_result[0][0])
                    episodes = [int(sql_result[0][1])]
                else:
                    # Found no result, try with season 0
                    sql_result = myDB.select(
                        "SELECT season, episode FROM tv_episodes WHERE showid = ? and indexer = ? and airdate = ?",
                        [show.indexerid, show.indexer, airdate])
                    if sql_result:
                        season = int(sql_result[0][0])
                        episodes = [int(sql_result[0][1])]
                    else:
                        self._log(u"Unable to find episode with date " + str(episodes[0]) + u" for show " + str(
                        show.indexerid) + u", skipping", logger.DEBUG)
                        # we don't want to leave dates in the episode list if we couldn't convert them to real episode numbers
                        episodes = []
                        continue

            # if there's no season then we can hopefully just use 1 automatically
            elif season == None and show:
                myDB = db.DBConnection()
                numseasonsSQlResult = myDB.select(
                    "SELECT COUNT(DISTINCT season) as numseasons FROM tv_episodes WHERE showid = ? and indexer = ? and season != 0",
                    [show.indexerid, show.indexer])
                if int(numseasonsSQlResult[0][0]) == 1 and season == None:
                    self._log(
                        u"Don't have a season number, but this show appears to only have 1 season, setting season number to 1...",
                        logger.DEBUG)
                    season = 1

            if show and season and episodes:
                return (show, season, episodes, quality, version)

        return (show, season, episodes, quality, version)

    def _get_ep_obj(self, show, season, episodes):
        """
        Retrieve the TVEpisode object requested.

        show: The show object belonging to the show we want to process
        season: The season of the episode (int)
        episodes: A list of episodes to find (list of ints)

        If the episode(s) can be found then a TVEpisode object with the correct related eps will
        be instantiated and returned. If the episode can't be found then None will be returned.
        """

        root_ep = None
        for cur_episode in episodes:
            self._log(u"Retrieving episode object for " + str(season) + "x" + str(cur_episode), logger.DEBUG)

            # now that we've figured out which episode this file is just load it manually
            try:
                curEp = show.getEpisode(season, cur_episode)
                if not curEp:
                    raise exceptions.EpisodeNotFoundException()
            except exceptions.EpisodeNotFoundException, e:
                self._log(u"Unable to create episode: " + ex(e), logger.DEBUG)
                raise exceptions.PostProcessingFailed()

            # associate all the episodes together under a single root episode
            if root_ep == None:
                root_ep = curEp
                root_ep.relatedEps = []
            elif curEp not in root_ep.relatedEps:
                root_ep.relatedEps.append(curEp)

        return root_ep

    def _get_quality(self, ep_obj):
        """
        Determines the quality of the file that is being post processed, first by checking if it is directly
        available in the TVEpisode's status or otherwise by parsing through the data available.

        ep_obj: The TVEpisode object related to the file we are post processing

        Returns: A quality value found in common.Quality
        """

        ep_quality = common.Quality.UNKNOWN

        # if there is a quality available in the status then we don't need to bother guessing from the filename
        if ep_obj.status in common.Quality.SNATCHED + common.Quality.SNATCHED_PROPER + common.Quality.SNATCHED_BEST:
            oldStatus, ep_quality = common.Quality.splitCompositeStatus(ep_obj.status)  # @UnusedVariable
            if ep_quality != common.Quality.UNKNOWN:
                self._log(
                    u"The old status had a quality in it, using that: " + common.Quality.qualityStrings[ep_quality],
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
                u"Looking up quality for name " + cur_name + u", got " + common.Quality.qualityStrings[ep_quality],
                logger.DEBUG)

            # if we find a good one then use it
            if ep_quality != common.Quality.UNKNOWN:
                logger.log(cur_name + u" looks like it has quality " + common.Quality.qualityStrings[
                    ep_quality] + ", using that", logger.DEBUG)
                return ep_quality

        # Try getting quality from the episode (snatched) status
        if ep_obj.status in common.Quality.SNATCHED + common.Quality.SNATCHED_PROPER:
            oldStatus, ep_quality = common.Quality.splitCompositeStatus(ep_obj.status)  # @UnusedVariable
            if ep_quality != common.Quality.UNKNOWN:
                self._log(
                    u"The old status had a quality in it, using that: " + common.Quality.qualityStrings[ep_quality],
                    logger.DEBUG)
                return ep_quality

        # Try guessing quality from the file name
        ep_quality = common.Quality.assumeQuality(self.file_path)
        self._log(
            u"Guessing quality for name " + self.file_name + u", got " + common.Quality.qualityStrings[ep_quality],
            logger.DEBUG)
        if ep_quality != common.Quality.UNKNOWN:
            logger.log(self.file_name + u" looks like it has quality " + common.Quality.qualityStrings[
                ep_quality] + ", using that", logger.DEBUG)
            return ep_quality

        test = str(ep_quality)
        return ep_quality

    def _run_extra_scripts(self, ep_obj):
        """
        Executes any extra scripts defined in the config.

        ep_obj: The object to use when calling the extra script
        """
        for curScriptName in sickbeard.EXTRA_SCRIPTS:

            # generate a safe command line string to execute the script and provide all the parameters
            script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", curScriptName) if piece.strip()]
            script_cmd[0] = ek.ek(os.path.abspath, script_cmd[0])
            self._log(u"Absolute path to script: " + script_cmd[0], logger.DEBUG)

            script_cmd = script_cmd + [ep_obj.location, self.file_path, str(ep_obj.show.indexerid), str(ep_obj.season),
                                       str(ep_obj.episode), str(ep_obj.airdate)]

            # use subprocess to run the command and capture output
            self._log(u"Executing command " + str(script_cmd))
            try:
                p = subprocess.Popen(script_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, cwd=sickbeard.PROG_DIR)
                out, err = p.communicate()  # @UnusedVariable
                self._log(u"Script result: " + str(out), logger.DEBUG)

            except OSError, e:
                self._log(u"Unable to run extra_script: " + ex(e))

            except Exception, e:
                self._log(u"Unable to run extra_script: " + ex(e))

    def _is_priority(self, ep_obj, new_ep_quality):
        """
        Determines if the episode is a priority download or not (if it is expected). Episodes which are expected
        (snatched) or larger than the existing episode are priority, others are not.

        ep_obj: The TVEpisode object in question
        new_ep_quality: The quality of the episode that is being processed

        Returns: True if the episode is priority, False otherwise.
        """

        if self.is_priority:
            return True

        old_ep_status, old_ep_quality = common.Quality.splitCompositeStatus(ep_obj.status)

        # if SB downloaded this on purpose we likely have a priority download
        if self.in_history or ep_obj.status in common.Quality.SNATCHED + common.Quality.SNATCHED_PROPER + common.Quality.SNATCHED_BEST:
            # if the episode is still in a snatched status, then we can assume we want this
            if ep_obj.status in common.Quality.SNATCHED + common.Quality.SNATCHED_PROPER + common.Quality.SNATCHED_BEST:
                self._log(u"SB snatched this episode and it is not processed before", logger.DEBUG)
                return True
            # if it's not snatched, we only want it if the new quality is higher or if it's a proper of equal or higher quality
            if new_ep_quality > old_ep_quality and new_ep_quality != common.Quality.UNKNOWN:
                self._log(u"SB snatched this episode and it is a higher quality so I'm marking it as priority", logger.DEBUG)
                return True
            if self.is_proper and new_ep_quality >= old_ep_quality and new_ep_quality != common.Quality.UNKNOWN:
                self._log(u"SB snatched this episode and it is a proper of equal or higher quality so I'm marking it as priority", logger.DEBUG)
                return True
            return False

        # if the user downloaded it manually and it's higher quality than the existing episode then it's priority
        if new_ep_quality > old_ep_quality and new_ep_quality != common.Quality.UNKNOWN:
            self._log(
                u"This was manually downloaded but it appears to be better quality than what we have so I'm marking it as priority",
                logger.DEBUG)
            return True

        # if the user downloaded it manually and it appears to be a PROPER/REPACK then it's priority
        if self.is_proper and new_ep_quality >= old_ep_quality and new_ep_quality != common.Quality.UNKNOWN:
            self._log(u"This was manually downloaded but it appears to be a proper so I'm marking it as priority",
                      logger.DEBUG)
            return True

        return False

    def process(self):
        """
        Post-process a given file
        """

        self._log(u"Processing " + self.file_path + " (" + str(self.nzb_name) + ")")

        if ek.ek(os.path.isdir, self.file_path):
            self._log(u"File " + self.file_path + " seems to be a directory")
            return False

        for ignore_file in self.IGNORED_FILESTRINGS:
            if ignore_file in self.file_path:
                self._log(u"File " + self.file_path + " is ignored type, skipping")
                return False

        # reset per-file stuff
        self.in_history = False

        # reset the anidb episode object
        self.anidbEpisode = None

        # try to find the file info
        (show, season, episodes, quality, version) = self._find_info()
        if not show:
            self._log(u"This show isn't in your list, you need to add it to SB before post-processing an episode",
                      logger.WARNING)
            raise exceptions.PostProcessingFailed()
        elif season == None or not episodes:
            self._log(u"Not enough information to determine what episode this is", logger.DEBUG)
            self._log(u"Quitting post-processing", logger.DEBUG)
            return False

        # retrieve/create the corresponding TVEpisode objects
        ep_obj = self._get_ep_obj(show, season, episodes)
        old_ep_status, old_ep_quality = common.Quality.splitCompositeStatus(ep_obj.status)

        # get the quality of the episode we're processing
        if quality and not common.Quality.qualityStrings[quality] == 'Unknown':
            self._log(u"Snatch history had a quality in it, using that: " + common.Quality.qualityStrings[quality],
                      logger.DEBUG)
            new_ep_quality = quality
        else:
            new_ep_quality = self._get_quality(ep_obj)

        logger.log(u"Quality of the episode we're processing: " + str(new_ep_quality), logger.DEBUG)

        # see if this is a priority download (is it snatched, in history, PROPER, or BEST)
        priority_download = self._is_priority(ep_obj, new_ep_quality)
        self._log(u"Is ep a priority download: " + str(priority_download), logger.DEBUG)

        # get the version of the episode we're processing
        if version:
            self._log(u"Snatch history had a version in it, using that: v" + str(version),
                      logger.DEBUG)
            new_ep_version = version
        else:
            new_ep_version = -1

        # check for an existing file
        existing_file_status = self._checkForExistingFile(ep_obj.location)

        # if it's not priority then we don't want to replace smaller files in case it was a mistake
        if not priority_download:

            # Not a priority and the quality is lower than what we already have
            if (new_ep_quality < old_ep_quality and new_ep_quality != common.Quality.UNKNOWN) and not existing_file_status == PostProcessor.DOESNT_EXIST:
                self._log(u"File exists and new file quality is lower than existing, marking it unsafe to replace", logger.DEBUG)
                return False

            # if there's an existing file that we don't want to replace stop here
            if existing_file_status == PostProcessor.EXISTS_LARGER:
                if self.is_proper:
                    self._log(
                        u"File exists and new file is smaller, new file is a proper/repack, marking it safe to replace",
                        logger.DEBUG)
                    return True

                else:
                    self._log(u"File exists and new file is smaller, marking it unsafe to replace", logger.DEBUG)
                    return False

            elif existing_file_status == PostProcessor.EXISTS_SAME:
                self._log(u"File exists and new file is same size, marking it unsafe to replace", logger.DEBUG)
                return False

        # if the file is priority then we're going to replace it even if it exists
        else:
            self._log(
                u"This download is marked a priority download so I'm going to replace an existing file if I find one",
                logger.DEBUG)

        # try to find out if we have enough space to perform the copy or move action.
        if not helpers.isFileLocked(self.file_path, False):
            if not verify_freespace(self.file_path, ep_obj.show._location, [ep_obj] + ep_obj.relatedEps):
                self._log("Not enough space to continue PP, exiting")
                return False
        else:
            self._log("Unable to determine needed filespace as the source file is locked for access")


        # delete the existing file (and company)
        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            try:
                self._delete(cur_ep.location, associated_files=True)

                # clean up any left over folders
                if cur_ep.location:
                    helpers.delete_empty_folders(ek.ek(os.path.dirname, cur_ep.location),
                                                 keep_dir=ep_obj.show._location)
            except (OSError, IOError):
                raise exceptions.PostProcessingFailed("Unable to delete the existing files")

            # set the status of the episodes
            # for curEp in [ep_obj] + ep_obj.relatedEps:
            #    curEp.status = common.Quality.compositeStatus(common.SNATCHED, new_ep_quality)

        # if the show directory doesn't exist then make it if allowed
        if not ek.ek(os.path.isdir, ep_obj.show._location) and sickbeard.CREATE_MISSING_SHOW_DIRS:
            self._log(u"Show directory doesn't exist, creating it", logger.DEBUG)
            try:
                ek.ek(os.mkdir, ep_obj.show._location)
                helpers.chmodAsParent(ep_obj.show._location)

                # do the library update for synoindex
                notifiers.synoindex_notifier.addFolder(ep_obj.show._location)
            except (OSError, IOError):
                raise exceptions.PostProcessingFailed("Unable to create the show directory: " + ep_obj.show._location)

            # get metadata for the show (but not episode because it hasn't been fully processed)
            ep_obj.show.writeMetadata(True)

        # update the ep info before we rename so the quality & release name go into the name properly
        sql_l = []

        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            with cur_ep.lock:

                if self.release_name:
                    self._log("Found release name " + self.release_name, logger.DEBUG)
                    cur_ep.release_name = self.release_name
                else:
                    cur_ep.release_name = ""

                if ep_obj.status in common.Quality.SNATCHED_BEST:
                    cur_ep.status = common.Quality.compositeStatus(common.ARCHIVED, new_ep_quality)
                else:
                    cur_ep.status = common.Quality.compositeStatus(common.DOWNLOADED, new_ep_quality)

                cur_ep.subtitles = u''

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
            self._log(u"Couldn't find release in snatch history", logger.WARNING)

        # find the destination folder
        try:
            proper_path = ep_obj.proper_path()
            proper_absolute_path = ek.ek(os.path.join, ep_obj.show.location, proper_path)

            dest_path = ek.ek(os.path.dirname, proper_absolute_path)
        except exceptions.ShowDirNotFoundException:
            raise exceptions.PostProcessingFailed(
                u"Unable to post-process an episode if the show dir doesn't exist, quitting")

        self._log(u"Destination folder for this episode: " + dest_path, logger.DEBUG)

        # create any folders we need
        helpers.make_dirs(dest_path)

        # figure out the base name of the resulting episode file
        if sickbeard.RENAME_EPISODES:
            orig_extension = self.file_name.rpartition('.')[-1]
            new_base_name = ek.ek(os.path.basename, proper_path)
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
                if helpers.isFileLocked(self.file_path, False):
                    raise exceptions.PostProcessingFailed("File is locked for reading")
                self._copy(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                           sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "move":
                if helpers.isFileLocked(self.file_path, True):
                    raise exceptions.PostProcessingFailed("File is locked for reading/writing")
                self._move(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                           sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "hardlink":
                self._hardlink(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                               sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "symlink":
                if helpers.isFileLocked(self.file_path, True):
                    raise exceptions.PostProcessingFailed("File is locked for reading/writing")
                self._moveAndSymlink(self.file_path, dest_path, new_base_name, sickbeard.MOVE_ASSOCIATED_FILES,
                                     sickbeard.USE_SUBTITLES and ep_obj.show.subtitles)
            else:
                logger.log(u"Unknown process method: " + str(self.process_method), logger.ERROR)
                raise exceptions.PostProcessingFailed("Unable to move the files to their new home")
        except (OSError, IOError):
            raise exceptions.PostProcessingFailed("Unable to move the files to their new home")

        # download subtitles
        if sickbeard.USE_SUBTITLES and ep_obj.show.subtitles:
            for cur_ep in [ep_obj] + ep_obj.relatedEps:
                with cur_ep.lock:
                    cur_ep.location = ek.ek(os.path.join, dest_path, new_file_name)
                    cur_ep.downloadSubtitles(force=True)

        # now that processing has finished, we can put the info in the DB. If we do it earlier, then when processing fails, it won't try again.
        if len(sql_l) > 0:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)

        # put the new location in the database
        sql_l = []
        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            with cur_ep.lock:
                cur_ep.location = ek.ek(os.path.join, dest_path, new_file_name)
                sql_l.append(cur_ep.get_sql())

        if len(sql_l) > 0:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)

        # set file modify stamp to show airdate
        if sickbeard.AIRDATE_EPISODES:
            for cur_ep in [ep_obj] + ep_obj.relatedEps:
                with cur_ep.lock:
                    cur_ep.airdateModifyStamp()

        # generate nfo/tbn
        ep_obj.createMetaFiles()

        # log it to history
        history.logDownload(ep_obj, self.file_path, new_ep_quality, self.release_group, new_ep_version)

        # send notifications
        notifiers.notify_download(ep_obj._format_pattern('%SN - %Sx%0E - %EN - %QN'))

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

        self._run_extra_scripts(ep_obj)

        return True
