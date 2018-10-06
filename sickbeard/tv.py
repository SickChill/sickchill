# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sick-rage.github.io
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

from __future__ import unicode_literals

import datetime
import os.path
import re
import shutil
import stat
import threading
import traceback

import six
from imdb import imdb
from unidecode import unidecode

import sickbeard
from sickbeard import db, helpers, image_cache, logger, network_timezones, notifiers, postProcessor, subtitles
from sickbeard.blackandwhitelist import BlackAndWhiteList
from sickbeard.common import (ARCHIVED, DOWNLOADED, FAILED, IGNORED, NAMING_DUPLICATE, NAMING_EXTEND, NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED,
                              NAMING_SEPARATED_REPEAT, Overview, Quality, SKIPPED, SNATCHED, SNATCHED_PROPER, statusStrings, UNAIRED, UNKNOWN, WANTED)
from sickbeard.indexers.indexer_config import INDEXER_TVRAGE
from sickbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickrage.helper import glob
from sickrage.helper.common import dateTimeFormat, episode_num, remove_extension, replace_extension, sanitize_filename, try_int
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import (EpisodeDeletedException, EpisodeNotFoundException, ex, MultipleEpisodesInDatabaseException,
                                        MultipleShowObjectsException, MultipleShowsInDatabaseException, NoNFOException, ShowDirectoryNotFoundException,
                                        ShowNotFoundException)
from sickrage.show.Show import Show

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

try:
    from send2trash import send2trash
except ImportError:
    pass


def dirty_setter(attr_name):
    def wrapper(self, val):
        if getattr(self, attr_name) != val:
            setattr(self, attr_name, val)
            self.dirty = True

    return wrapper


class TVShow(object):  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    def __init__(self, indexer, indexerid, lang=""):
        self._indexerid = int(indexerid)
        self._indexer = int(indexer)
        self._name = ""
        self._imdbid = ""
        self._network = ""
        self._genre = ""
        self._classification = ""
        self._runtime = 0
        self._imdb_info = {}
        self._quality = int(sickbeard.QUALITY_DEFAULT)
        self._season_folders = int(sickbeard.SEASON_FOLDERS_DEFAULT)
        self._status = "Unknown"
        self._airs = ""
        self._startyear = 0
        self._paused = 0
        self._air_by_date = 0
        self._subtitles = int(sickbeard.SUBTITLES_DEFAULT)
        self._subtitles_sr_metadata = 0
        self._dvdorder = 0
        self._lang = lang
        self._last_update_indexer = 1
        self._sports = 0
        self._anime = 0
        self._scene = 0
        self._rls_ignore_words = ""
        self._rls_require_words = ""
        self._default_ep_status = SKIPPED
        self.dirty = True

        self._location = ""
        self.lock = threading.Lock()
        self.episodes = {}
        self.nextaired = ""
        self.release_groups = None

        otherShow = Show.find(sickbeard.showList, self.indexerid)
        if otherShow is not None:
            raise MultipleShowObjectsException("Can't create a show if it already exists")

        self.loadFromDB()

    name = property(lambda self: self._name, dirty_setter("_name"))
    indexerid = property(lambda self: self._indexerid, dirty_setter("_indexerid"))
    indexer = property(lambda self: self._indexer, dirty_setter("_indexer"))
    # location = property(lambda self: self._location, dirty_setter("_location"))
    imdbid = property(lambda self: self._imdbid, dirty_setter("_imdbid"))
    network = property(lambda self: self._network, dirty_setter("_network"))
    genre = property(lambda self: self._genre, dirty_setter("_genre"))
    classification = property(lambda self: self._classification, dirty_setter("_classification"))
    runtime = property(lambda self: self._runtime, dirty_setter("_runtime"))
    imdb_info = property(lambda self: self._imdb_info, dirty_setter("_imdb_info"))
    quality = property(lambda self: self._quality, dirty_setter("_quality"))
    season_folders = property(lambda self: self._season_folders, dirty_setter("_season_folders"))
    status = property(lambda self: self._status, dirty_setter("_status"))
    airs = property(lambda self: self._airs, dirty_setter("_airs"))
    startyear = property(lambda self: self._startyear, dirty_setter("_startyear"))
    paused = property(lambda self: self._paused, dirty_setter("_paused"))
    air_by_date = property(lambda self: self._air_by_date, dirty_setter("_air_by_date"))
    subtitles = property(lambda self: self._subtitles, dirty_setter("_subtitles"))
    dvdorder = property(lambda self: self._dvdorder, dirty_setter("_dvdorder"))
    lang = property(lambda self: self._lang, dirty_setter("_lang"))
    last_update_indexer = property(lambda self: self._last_update_indexer, dirty_setter("_last_update_indexer"))
    sports = property(lambda self: self._sports, dirty_setter("_sports"))
    anime = property(lambda self: self._anime, dirty_setter("_anime"))
    scene = property(lambda self: self._scene, dirty_setter("_scene"))
    rls_ignore_words = property(lambda self: self._rls_ignore_words, dirty_setter("_rls_ignore_words"))
    rls_require_words = property(lambda self: self._rls_require_words, dirty_setter("_rls_require_words"))
    default_ep_status = property(lambda self: self._default_ep_status, dirty_setter("_default_ep_status"))
    subtitles_sr_metadata = property(lambda self: self._subtitles_sr_metadata, dirty_setter("_subtitles_sr_metadata"))

    @property
    def is_anime(self):
        return int(self.anime) > 0

    @property
    def is_sports(self):
        return int(self.sports) > 0

    @property
    def is_scene(self):
        return int(self.scene) > 0

    @property
    def network_logo_name(self):
        return unidecode(self.network).lower()

    @property
    def sort_name(self):
        return helpers.sortable_name(self.name)

    def _getLocation(self):
        # no dir check needed if missing show dirs are created during post-processing
        if sickbeard.CREATE_MISSING_SHOW_DIRS or ek(os.path.isdir, self._location):
            return self._location

        raise ShowDirectoryNotFoundException("Show folder doesn't exist, you shouldn't be using it")

    def _setLocation(self, newLocation):
        logger.log("Setter sets location to " + newLocation, logger.DEBUG)
        # Don't validate dir if user wants to add shows without creating a dir
        if sickbeard.ADD_SHOWS_WO_DIR or ek(os.path.isdir, newLocation):
            dirty_setter("_location")(self, newLocation)
        else:
            raise NoNFOException("Invalid folder for the show!")

    location = property(_getLocation, _setLocation)

    # delete references to anything that's not in the internal lists
    def flushEpisodes(self):

        for curSeason in self.episodes:
            for curEp in self.episodes[curSeason]:
                myEp = self.episodes[curSeason][curEp]
                self.episodes[curSeason][curEp] = None
                del myEp

    def getAllEpisodes(self, season=None, has_location=False):

        sql_selection = 'SELECT season, episode, '

        # subselection to detect multi-episodes early, share_location > 0
        sql_selection += '(SELECT COUNT (*) FROM tv_episodes WHERE showid = tve.showid '
        sql_selection += 'AND season = tve.season AND location != \'\' AND location = tve.location '
        sql_selection += 'AND episode != tve.episode) AS share_location '
        sql_selection += 'FROM tv_episodes tve WHERE showid = {0} '.format(self.indexerid)

        if season is not None:
            sql_selection += 'AND season = {0} '.format(season)

        if has_location:
            sql_selection += 'AND location != \'\' '

        # need ORDER episode ASC to rename multi-episodes in order S01E01-02
        sql_selection += 'ORDER BY season ASC, episode ASC '

        main_db_con = db.DBConnection()
        results = main_db_con.select(sql_selection)

        ep_list = []
        for cur_result in results:
            cur_ep = self.getEpisode(cur_result[b"season"], cur_result[b"episode"])
            if not cur_ep:
                continue

            cur_ep.relatedEps = []
            if cur_ep.location:
                # if there is a location, check if it's a multi-episode (share_location > 0) and put them in relatedEps
                if cur_result[b"share_location"] > 0:
                    related_eps_result = main_db_con.select(
                        "SELECT season, episode FROM tv_episodes WHERE showid = ? AND season = ? AND location = ? AND episode != ? ORDER BY episode ASC",
                        [self.indexerid, cur_ep.season, cur_ep.location, cur_ep.episode])
                    for cur_related_ep in related_eps_result:
                        related_ep = self.getEpisode(cur_related_ep[b"season"], cur_related_ep[b"episode"])
                        if related_ep and related_ep not in cur_ep.relatedEps:
                            cur_ep.relatedEps.append(related_ep)
            ep_list.append(cur_ep)

        return ep_list

    def getEpisode(self, season=None, episode=None, ep_file=None, noCreate=False, absolute_number=None):  # pylint: disable=too-many-arguments
        season = try_int(season, None)
        episode = try_int(episode, None)
        absolute_number = try_int(absolute_number, None)

        # if we get an anime get the real season and episode
        if self.is_anime and absolute_number and not season and not episode:
            main_db_con = db.DBConnection()
            sql = "SELECT season, episode FROM tv_episodes WHERE showid = ? AND absolute_number = ? AND season != 0"
            sql_results = main_db_con.select(sql, [self.indexerid, absolute_number])

            if len(sql_results) == 1:
                episode = int(sql_results[0][b"episode"])
                season = int(sql_results[0][b"season"])
                logger.log("Found episode by absolute number {absolute} which is {ep}".format
                           (absolute=absolute_number,
                            ep=episode_num(season, episode)), logger.DEBUG)
            elif len(sql_results) > 1:
                logger.log("Multiple entries for absolute number: {absolute} in show: {name} found ".format
                           (absolute=absolute_number, name=self.name), logger.ERROR)

                return None
            else:
                logger.log(
                    "No entries for absolute number: " + str(absolute_number) + " in show: " + self.name + " found.",
                    logger.DEBUG)
                return None

        if season not in self.episodes:
            self.episodes[season] = {}

        if episode not in self.episodes[season] or self.episodes[season][episode] is None:
            if noCreate:
                return None

            # logger.log("{id}: An object for episode {ep} didn't exist in the cache, trying to create it".format
            #            (id=self.indexerid, ep=episode_num(season, episode)), logger.DEBUG)

            if ep_file:
                ep = TVEpisode(self, season, episode, ep_file)
            else:
                ep = TVEpisode(self, season, episode)

            if ep is not None:
                self.episodes[season][episode] = ep

        return self.episodes[season][episode]

    def should_update(self, update_date=datetime.date.today()):

        # if show is not 'Ended' always update (status 'Continuing')
        if self.status == 'Continuing':
            return True

        # run logic against the current show latest aired and next unaired data to see if we should bypass 'Ended' status

        graceperiod = datetime.timedelta(days=30)

        last_airdate = datetime.date.fromordinal(1)

        # get latest aired episode to compare against today - graceperiod and today + graceperiod
        main_db_con = db.DBConnection()
        sql_result = main_db_con.select(
            "SELECT IFNULL(MAX(airdate), 0) as last_aired FROM tv_episodes WHERE showid = ? AND season > 0 AND airdate > 1 AND status > 1",
            [self.indexerid])

        if sql_result and sql_result[0][b'last_aired'] != 0:
            last_airdate = datetime.date.fromordinal(sql_result[0][b'last_aired'])
            if (update_date - graceperiod) <= last_airdate <= (update_date + graceperiod):
                return True

        # get next upcoming UNAIRED episode to compare against today + graceperiod
        sql_result = main_db_con.select(
            "SELECT IFNULL(MIN(airdate), 0) as airing_next FROM tv_episodes WHERE showid = ? AND season > 0 AND airdate > 1 AND status = 1",
            [self.indexerid])

        if sql_result and sql_result[0][b'airing_next'] != 0:
            next_airdate = datetime.date.fromordinal(sql_result[0][b'airing_next'])
            if next_airdate <= (update_date + graceperiod):
                return True

        last_update_indexer = datetime.date.fromordinal(self.last_update_indexer)

        # in the first year after ended (last airdate), update every 30 days
        if (update_date - last_airdate) < datetime.timedelta(days=450) and (update_date - last_update_indexer) > datetime.timedelta(days=30):
            return True

        return False

    def writeShowNFO(self):

        result = False

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        logger.log(str(self.indexerid) + ": Writing NFOs for show", logger.DEBUG)
        for cur_provider in sickbeard.metadata_provider_dict.values():
            result = cur_provider.create_show_metadata(self) or result

        return result

    def writeMetadata(self, show_only=False):

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        self.getImages()

        self.writeShowNFO()

        if not show_only:
            self.writeEpisodeNFOs()

    def writeEpisodeNFOs(self):

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        logger.log(str(self.indexerid) + ": Writing NFOs for all episodes", logger.DEBUG)

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT season, episode FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        for epResult in sql_results:
            logger.log("{id}: Retrieving/creating episode {ep}".format
                       (id=self.indexerid, ep=episode_num(epResult[b"season"], epResult[b"episode"])),
                       logger.DEBUG)
            curEp = self.getEpisode(epResult[b"season"], epResult[b"episode"])
            if not curEp:
                continue

            curEp.createMetaFiles()

    def updateMetadata(self):

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        result = False

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        logger.log(str(self.indexerid) + ": Updating NFOs for show with new indexer info")
        for cur_provider in sickbeard.metadata_provider_dict.values():
            result = cur_provider.update_show_indexer_metadata(self) or result

        return result

    # find all media files in the show folder and create episodes for as many as possible
    def loadEpisodesFromDir(self):

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, not loading episodes from disk", logger.DEBUG)
            return

        logger.log(str(self.indexerid) + ": Loading all episodes from the show directory " + self._location, logger.DEBUG)

        # get file list
        media_files = helpers.list_media_files(self._location)

        # create TVEpisodes from each media file (if possible)
        sql_l = []
        for media_file in media_files:
            logger.log("{tvdbid}: Creating episode from {filename}".format(tvdbid=str(self.indexerid), filename=ek(os.path.basename, media_file)), logger.DEBUG)
            curEpisode = None
            try:
                curEpisode = self.makeEpFromFile(media_file)
            except (ShowNotFoundException, EpisodeNotFoundException) as error:
                logger.log("Episode {filename} returned an exception: {ex}".format(filename=ek(os.path.basename, media_file), ex=ex(error)), logger.ERROR)
                continue
            except EpisodeDeletedException:
                logger.log("The episode deleted itself when I tried making an object for it", logger.DEBUG)

            if curEpisode is None:
                continue

            # see if we should save the release name in the db
            ep_file_name = ek(os.path.basename, curEpisode.location)
            ep_file_name = ek(os.path.splitext, ep_file_name)[0]

            try:
                parse_result = NameParser(False, showObj=self, tryIndexers=True).parse(ep_file_name)
            except (InvalidNameException, InvalidShowException):
                parse_result = None

            if ' ' not in ep_file_name and parse_result and parse_result.release_group:
                logger.log(
                    "Name " + ep_file_name + " gave release group of " + parse_result.release_group + ", seems valid",
                    logger.DEBUG)
                curEpisode.release_name = ep_file_name
                curEpisode.release_group = parse_result.release_group

            # store the reference in the show
            if curEpisode is not None:
                if self.subtitles:
                    try:
                        curEpisode.refreshSubtitles()
                    except Exception:
                        logger.log("{0}: Could not refresh subtitles".format(self.indexerid), logger.ERROR)
                        logger.log(traceback.format_exc(), logger.DEBUG)

                sql_l.append(curEpisode.get_sql())

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

    def loadEpisodesFromDB(self):  # pylint: disable=too-many-locals

        logger.log("Loading all episodes from the DB", logger.DEBUG)
        scannedEps = {}

        try:
            main_db_con = db.DBConnection()
            sql = "SELECT season, episode, showid, show_name FROM tv_episodes JOIN tv_shows WHERE showid = indexer_id and showid = ?"
            sql_results = main_db_con.select(sql, [self.indexerid])
        except Exception as error:
            logger.log("Could not load episodes from the DB. Error: {0}".format(error), logger.ERROR)
            return scannedEps

        lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

        lINDEXER_API_PARMS['language'] = self.lang or sickbeard.INDEXER_DEFAULT_LANGUAGE
        logger.log("Using language: " + str(self.lang), logger.DEBUG)

        if self.dvdorder:
            lINDEXER_API_PARMS['dvdorder'] = True

        # logger.log("lINDEXER_API_PARMS: " + str(lINDEXER_API_PARMS), logger.DEBUG)
        # Spamming log
        t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

        cachedShow = t[self.indexerid]
        cachedSeasons = {}

        curShowid = None
        curShowName = None

        for curResult in sql_results:

            curSeason = int(curResult[b"season"])
            curEpisode = int(curResult[b"episode"])
            curShowid = int(curResult[b'showid'])
            curShowName = str(curResult[b'show_name'])

            logger.log("{0}: Loading {1} episodes from DB".format(curShowid, curShowName), logger.DEBUG)
            deleteEp = False

            if curSeason not in cachedSeasons:
                try:
                    cachedSeasons[curSeason] = cachedShow[curSeason]
                except sickbeard.indexer_seasonnotfound as error:
                    logger.log("{0}: {1} (unaired/deleted) in the indexer {2} for {3}. Removing existing records from database".format
                               (curShowid, error.message, sickbeard.indexerApi(self.indexer).name, curShowName), logger.DEBUG)
                    deleteEp = True

            if curSeason not in scannedEps:
                logger.log("{id}: Not curSeason in scannedEps".format(id=curShowid), logger.DEBUG)
                scannedEps[curSeason] = {}

            logger.log("{id}: Loading {show} {ep} from the DB".format
                       (id=curShowid, show=curShowName, ep=episode_num(curSeason, curEpisode)),
                       logger.DEBUG)

            try:
                curEp = self.getEpisode(curSeason, curEpisode)
                if not curEp:
                    raise EpisodeNotFoundException

                # if we found out that the ep is no longer on TVDB then delete it from our database too
                if deleteEp:
                    curEp.deleteEpisode()

                curEp.loadFromDB(curSeason, curEpisode)
                curEp.loadFromIndexer(tvapi=t, cachedSeason=cachedSeasons[curSeason])
                scannedEps[curSeason][curEpisode] = True
            except EpisodeDeletedException:
                logger.log("{id}: Tried loading {show} {ep} from the DB that should have been deleted, skipping it".format
                           (id=curShowid, show=curShowName, ep=episode_num(curSeason, curEpisode)),
                           logger.DEBUG)
                continue

        if curShowName and curShowid:
            logger.log("{id}: Finished loading all episodes for {show} from the DB".format
                       (show=curShowName, id=curShowid), logger.DEBUG)

        return scannedEps

    def loadEpisodesFromIndexer(self, cache=True):

        lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

        if not cache:
            lINDEXER_API_PARMS['cache'] = False

        lINDEXER_API_PARMS['language'] = self.lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

        if self.dvdorder:
            lINDEXER_API_PARMS['dvdorder'] = True

        try:
            t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
            showObj = t[self.indexerid]
        except sickbeard.indexer_error:
            logger.log("" + sickbeard.indexerApi(self.indexer).name +
                       " timed out, unable to update episodes from " +
                       sickbeard.indexerApi(self.indexer).name, logger.WARNING)
            return None

        logger.log(
            str(self.indexerid) + ": Loading all episodes from " + sickbeard.indexerApi(self.indexer).name + "..", logger.DEBUG)

        scannedEps = {}

        sql_l = []
        for season in showObj:
            scannedEps[season] = {}
            for episode in showObj[season]:
                # need some examples of wtf episode 0 means to decide if we want it or not
                if episode == 0:
                    continue
                try:
                    ep = self.getEpisode(season, episode)
                    if not ep:
                        raise EpisodeNotFoundException
                except EpisodeNotFoundException:
                    logger.log("{id}: {indexer} object for {ep} is incomplete, skipping this episode".format
                               (id=self.indexerid, indexer=sickbeard.indexerApi(self.indexer).name, ep=episode_num(season, episode)))
                    continue
                else:
                    try:
                        ep.loadFromIndexer(tvapi=t)
                    except EpisodeDeletedException:
                        logger.log("The episode was deleted, skipping the rest of the load")
                        continue

                with ep.lock:
                    # logger.log("{id}: Loading info from {indexer} for episode {ep}".format
                    #            (id=self.indexerid, indexer=sickbeard.indexerApi(self.indexer).name,
                    #             ep=episode_num(season, episode)), logger.DEBUG)
                    ep.loadFromIndexer(season, episode, tvapi=t)

                    sql_l.append(ep.get_sql())

                scannedEps[season][episode] = True

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

        # Done updating save last update date
        self.last_update_indexer = datetime.datetime.now().toordinal()

        self.saveToDB()

        return scannedEps

    def getImages(self):
        fanart_result = poster_result = banner_result = False
        season_posters_result = season_banners_result = season_all_poster_result = season_all_banner_result = False

        for cur_provider in sickbeard.metadata_provider_dict.values():

            # logger.log("Running metadata routines for " + cur_provider.name, logger.DEBUG)

            fanart_result = cur_provider.create_fanart(self) or fanart_result
            poster_result = cur_provider.create_poster(self) or poster_result
            banner_result = cur_provider.create_banner(self) or banner_result

            season_posters_result = cur_provider.create_season_posters(self) or season_posters_result
            season_banners_result = cur_provider.create_season_banners(self) or season_banners_result
            season_all_poster_result = cur_provider.create_season_all_poster(self) or season_all_poster_result
            season_all_banner_result = cur_provider.create_season_all_banner(self) or season_all_banner_result

        return fanart_result or poster_result or banner_result or season_posters_result or season_banners_result or season_all_poster_result or season_all_banner_result

    # make a TVEpisode object from a media file
    def makeEpFromFile(self, filepath):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements

        if not ek(os.path.isfile, filepath):
            logger.log("{0}: That isn't even a real file dude... {1}".format
                       (self.indexerid, filepath))
            return None

        logger.log("{0}: Creating episode object from {1}".format
                   (self.indexerid, filepath), logger.DEBUG)

        try:
            parse_result = NameParser(showObj=self, tryIndexers=True, parse_method=('normal', 'anime')[self.is_anime]).parse(filepath, True, True)
        except (InvalidNameException, InvalidShowException) as error:
            logger.log("{0}: {1}".format(self.indexerid, error), logger.DEBUG)
            return None

        episodes = [ep for ep in parse_result.episode_numbers if ep is not None]
        if not episodes:
            logger.log("{0}: parse_result: {1}".format(self.indexerid, parse_result))
            logger.log("{0}: No episode number found in {1}, ignoring it".format
                       (self.indexerid, filepath), logger.INFO)
            return None

        # for now lets assume that any episode in the show dir belongs to that show
        season = parse_result.season_number if parse_result.season_number is not None else 1
        rootEp = None

        sql_l = []
        for current_ep in episodes:
            logger.log("{0}: {1} parsed to {2} {3}".format
                       (self.indexerid, filepath, self.name, episode_num(season, current_ep)), logger.DEBUG)

            checkQualityAgain = False
            same_file = False

            curEp = self.getEpisode(season, current_ep)
            if not curEp:
                try:
                    curEp = self.getEpisode(season, current_ep, filepath)
                    if not curEp:
                        raise EpisodeNotFoundException
                except EpisodeNotFoundException:
                    logger.log("{0}: Unable to figure out what this file is, skipping {1}".format
                               (self.indexerid, filepath), logger.ERROR)
                    continue

            else:
                # if there is a new file associated with this ep then re-check the quality
                if curEp.location and ek(os.path.normpath, curEp.location) != ek(os.path.normpath, filepath):
                    logger.log(
                        "{0}: The old episode had a different file associated with it, re-checking the quality using the new filename {1}".format
                        (self.indexerid, filepath), logger.DEBUG)
                    checkQualityAgain = True

                with curEp.lock:
                    old_size = curEp.file_size
                    curEp.location = filepath
                    # if the sizes are the same then it's probably the same file
                    same_file = old_size and curEp.file_size == old_size
                    curEp.checkForMetaFiles()

            if rootEp is None:
                rootEp = curEp
            else:
                if curEp not in rootEp.relatedEps:
                    with rootEp.lock:
                        rootEp.relatedEps.append(curEp)

            # if it's a new file then
            if not same_file:
                with curEp.lock:
                    curEp.release_name = ''
                    curEp.release_group = ''

            # if they replace a file on me I'll make some attempt at re-checking the quality unless I know it's the same file
            if checkQualityAgain and not same_file:
                newQuality = Quality.nameQuality(filepath, self.is_anime)
                logger.log("{0}: Since this file has been renamed, I checked {1} and found quality {2}".format
                           (self.indexerid, filepath, Quality.qualityStrings[newQuality]), logger.DEBUG)

                with curEp.lock:
                    curEp.status = Quality.compositeStatus(DOWNLOADED, newQuality)

            # check for status/quality changes as long as it's a new file
            elif not same_file and sickbeard.helpers.is_media_file(filepath) and curEp.status not in Quality.DOWNLOADED + Quality.ARCHIVED + [IGNORED]:
                oldStatus, oldQuality = Quality.splitCompositeStatus(curEp.status)
                newQuality = Quality.nameQuality(filepath, self.is_anime)

                newStatus = None

                # if it was snatched and now exists then set the status correctly
                if oldStatus == SNATCHED and oldQuality <= newQuality:
                    logger.log("{0}: This ep used to be snatched with quality {1} but a file exists with quality {2} so I'm setting the status to DOWNLOADED".format
                               (self.indexerid, Quality.qualityStrings[oldQuality], Quality.qualityStrings[newQuality]), logger.DEBUG)
                    newStatus = DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif oldStatus == SNATCHED_PROPER and oldQuality < newQuality:
                    logger.log("{0}: This ep used to be snatched proper with quality {1} but a file exists with quality {2} so I'm setting the status to DOWNLOADED".format
                               (self.indexerid, Quality.qualityStrings[oldQuality], Quality.qualityStrings[newQuality]), logger.DEBUG)
                    newStatus = DOWNLOADED

                elif oldStatus not in (SNATCHED, SNATCHED_PROPER):
                    newStatus = DOWNLOADED

                if newStatus is not None:
                    with curEp.lock:
                        logger.log("{0}: We have an associated file, so setting the status from {1} to DOWNLOADED/{2}".format
                                   (self.indexerid, curEp.status, Quality.statusFromName(filepath, anime=self.is_anime)), logger.DEBUG)
                        curEp.status = Quality.compositeStatus(newStatus, newQuality)

            with curEp.lock:
                sql_l.append(curEp.get_sql())

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

        # creating metafiles on the root should be good enough
        if rootEp:
            with rootEp.lock:
                rootEp.createMetaFiles()

        return rootEp

    def loadFromDB(self):  # pylint: disable=too-many-branches, too-many-statements

        # logger.log(str(self.indexerid) + ": Loading show info from database", logger.DEBUG)

        main_db_con = db.DBConnection(row_type='dict')
        sql_results = main_db_con.select("SELECT * FROM tv_shows WHERE indexer_id = ?", [self.indexerid])

        if len(sql_results) > 1:
            raise MultipleShowsInDatabaseException()
        elif not sql_results:
            logger.log(str(self.indexerid) + ": Unable to find the show in the database")
            return
        else:
            self.indexer = int(sql_results[0][b"indexer"] or 0)

            if not self.name:
                self.name = sql_results[0][b"show_name"]
            if not self.network:
                self.network = sql_results[0][b"network"]
            if not self.genre:
                self.genre = sql_results[0][b"genre"]
            if not self.classification:
                self.classification = sql_results[0][b"classification"]

            self.runtime = sql_results[0][b"runtime"]

            self.status = sql_results[0][b"status"]
            if self.status is None:
                self.status = "Unknown"

            self.airs = sql_results[0][b"airs"]
            if self.airs is None:
                self.airs = ""

            self.startyear = int(sql_results[0][b"startyear"] or 0)
            self.air_by_date = int(sql_results[0][b"air_by_date"] or 0)
            self.anime = int(sql_results[0][b"anime"] or 0)
            self.sports = int(sql_results[0][b"sports"] or 0)
            self.scene = int(sql_results[0][b"scene"] or 0)
            self.subtitles = int(sql_results[0][b"subtitles"] or 0)
            self.dvdorder = int(sql_results[0][b"dvdorder"] or 0)
            self.quality = int(sql_results[0][b"quality"] or UNKNOWN)
            self.season_folders = int(not int(sql_results[0][b"flatten_folders"] or 0))  # FIXME: inverted until next database version
            self.paused = int(sql_results[0][b"paused"] or 0)

            try:
                self._location = sql_results[0][b"location"]
            except Exception:
                dirty_setter("_location")(self, sql_results[0][b"location"])

            if not self.lang:
                self.lang = sql_results[0][b"lang"]

            self.last_update_indexer = sql_results[0][b"last_update_indexer"]

            self.rls_ignore_words = sql_results[0][b"rls_ignore_words"]
            self.rls_require_words = sql_results[0][b"rls_require_words"]

            self.default_ep_status = int(sql_results[0][b"default_ep_status"] or SKIPPED)

            if not self.imdbid:
                self.imdbid = sql_results[0][b"imdb_id"]

            if self.is_anime:
                self.release_groups = BlackAndWhiteList(self.indexerid)

            self.subtitles_sr_metadata = int(sql_results[0][b"sub_use_sr_metadata"] or 0)

        # Get IMDb_info from database
        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT * FROM imdb_info WHERE indexer_id = ?", [self.indexerid])

        if not sql_results:
            self.loadIMDbInfo()
            sql_results = main_db_con.select("SELECT * FROM imdb_info WHERE indexer_id = ?", [self.indexerid])
            if not sql_results:
                logger.log(str(self.indexerid) + ": Unable to find IMDb show info in the database")
                return

        self.imdb_info = dict(zip(sql_results[0].keys(), sql_results[0]))
        self.dirty = False
        return True

    def loadFromIndexer(self, cache=True, tvapi=None):

        if self.indexer == INDEXER_TVRAGE:
            return

        logger.log(str(self.indexerid) + ": Loading show info from " + sickbeard.indexerApi(self.indexer).name, logger.DEBUG)

        # There's gotta be a better way of doing this but we don't wanna
        # change the cache value elsewhere
        if tvapi:
            t = tvapi
        else:
            lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

            if not cache:
                lINDEXER_API_PARMS['cache'] = False

            lINDEXER_API_PARMS['language'] = self.lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

            if self.dvdorder:
                lINDEXER_API_PARMS['dvdorder'] = True

            t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

        myEp = t[self.indexerid]

        try:
            self.name = myEp[b'seriesname'].strip()
        except AttributeError:
            raise sickbeard.indexer_attributenotfound(
                "Found {0}, but attribute 'seriesname' was empty.".format(self.indexerid))

        self.classification = getattr(myEp, 'classification', 'Scripted')
        self.genre = getattr(myEp, 'genre', '')
        self.network = getattr(myEp, 'network', '')
        self.runtime = getattr(myEp, 'runtime', '')

        self.imdbid = getattr(myEp, 'imdb_id', '')

        if getattr(myEp, 'airs_dayofweek', None) is not None and getattr(myEp, 'airs_time', None) is not None:
            self.airs = myEp[b"airs_dayofweek"] + " " + myEp[b"airs_time"]

        if self.airs is None:
            self.airs = ''

        if getattr(myEp, 'firstaired', None) is not None:
            self.startyear = int(str(myEp[b"firstaired"]).split('-')[0])

        self.status = getattr(myEp, 'status', 'Unknown')

    def check_imdbid(self):
        try:
            int(re.sub(r"[^0-9]", "", self.imdbid))
        except (ValueError, TypeError):
            self.imdbid = ""

    def loadIMDbInfo(self):  # pylint: disable=too-many-branches

        imdb_info = {
            'imdb_id': '',
            'title': '',
            'year': '',
            'akas': [],
            'runtimes': '',
            'genres': [],
            'countries': '',
            'country_codes': [],
            'certificates': [],
            'rating': '',
            'votes': '',
            'last_update': ''
        }

        if sickbeard.PROXY_SETTING and sickbeard.PROXY_INDEXERS:
            i = imdb.IMDb(proxy=sickbeard.PROXY_SETTING)
        else:
            i = imdb.IMDb()

        # Check that the imdbid we have is valid for searching
        self.check_imdbid()

        if self.name and not self.imdbid:
            self.imdbid = i.title2imdbID(self.name, kind='tv series')

        # Make sure the lib didn't give us back something bogus
        self.check_imdbid()

        if not self.imdbid:
            logger.log(str(self.indexerid) + ": Not loading show info from IMDb, because we don't know the imdbid", logger.DEBUG)
            # Set to empty to avoid Keyerrors
            self.imdb_info = imdb_info
            return

        logger.log(str(self.indexerid) + ": Loading show info from IMDb", logger.DEBUG)

        imdbTv = i.get_movie(str(re.sub(r"[^0-9]", "", self.imdbid)))

        imdb_info[b'imdb_id'] = self.imdbid

        for key in [x for x in imdb_info.keys() if x.replace('_', ' ') in imdbTv.keys()]:
            # Store only the first value for string type
            if isinstance(imdb_info[key], six.string_types) and isinstance(imdbTv.get(key.replace('_', ' ')), list):
                imdb_info[key] = imdbTv.get(key.replace('_', ' '))[0]
            else:
                imdb_info[key] = imdbTv.get(key.replace('_', ' '))

        # Filter only the value
        if imdb_info[b'runtimes']:
            imdb_info[b'runtimes'] = re.search(r'\d+', imdb_info[b'runtimes']).group(0)
        else:
            imdb_info[b'runtimes'] = self.runtime

        if imdb_info[b'akas']:
            imdb_info[b'akas'] = '|'.join(imdb_info[b'akas'])
        else:
            imdb_info[b'akas'] = ''

        # Join all genres in a string
        if imdb_info[b'genres']:
            imdb_info[b'genres'] = '|'.join(imdb_info[b'genres'])
        else:
            imdb_info[b'genres'] = ''

        # Get only the production country certificate if any
        if imdb_info[b'certificates'] and imdb_info[b'countries']:
            dct = {}
            try:
                for item in imdb_info[b'certificates']:
                    dct[item.split(':')[0]] = item.split(':')[1]

                imdb_info[b'certificates'] = dct[imdb_info[b'countries']]
            except Exception:
                imdb_info[b'certificates'] = ''

        else:
            imdb_info[b'certificates'] = ''

        if imdb_info[b'country_codes']:
            imdb_info[b'country_codes'] = '|'.join(imdb_info[b'country_codes'])
        else:
            imdb_info[b'country_codes'] = ''

        imdb_info[b'last_update'] = datetime.date.today().toordinal()

        # Rename dict keys without spaces for DB upsert
        self.imdb_info = dict(
            (k.replace(' ', '_'), k(v) if hasattr(v, 'keys') else v) for k, v in six.iteritems(imdb_info))
        logger.log(str(self.indexerid) + ": Obtained info from IMDb ->" + str(self.imdb_info), logger.DEBUG)

    def nextEpisode(self):
        curDate = datetime.date.today().toordinal()
        if not self.nextaired or self.nextaired and curDate > self.nextaired:
            main_db_con = db.DBConnection()
            sql_results = main_db_con.select(
                "SELECT airdate, season, episode FROM tv_episodes WHERE showid = ? AND airdate >= ? AND status IN (?,?) ORDER BY airdate ASC LIMIT 1",
                [self.indexerid, datetime.date.today().toordinal(), UNAIRED, WANTED])

            self.nextaired = sql_results[0][b'airdate'] if sql_results else ''

        return self.nextaired

    def deleteShow(self, full=False):
        main_db_con = db.DBConnection()

        episodes_locations = main_db_con.select("SELECT location FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        sql_l = [["DELETE FROM tv_episodes WHERE showid = ?", [self.indexerid]],
                 ["DELETE FROM tv_shows WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM imdb_info WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM xem_refresh WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM scene_numbering WHERE indexer_id = ?", [self.indexerid]]]

        main_db_con.mass_action(sql_l)

        action = ('delete', 'trash')[sickbeard.TRASH_REMOVE_SHOW]

        # remove self from show list
        sickbeard.showList = [x for x in sickbeard.showList if int(x.indexerid) != self.indexerid]

        # clear the cache
        image_cache_dir = ek(os.path.join, sickbeard.CACHE_DIR, 'images')
        for cache_file in ek(glob.glob, ek(os.path.join, glob.escape(image_cache_dir), str(self.indexerid) + '.*')):
            logger.log('Attempt to {0} cache file {1}'.format(action, cache_file))
            try:
                if sickbeard.TRASH_REMOVE_SHOW:
                    send2trash(cache_file)
                else:
                    ek(os.remove, cache_file)

            except OSError as error:
                logger.log('Unable to {0} {1}: {2}'.format(action, cache_file, error), logger.WARNING)

        # remove entire show folder
        if full:
            try:
                logger.log('Attempt to {0} show folder {1}'.format(action, self._location))
                # check first the read-only attribute
                file_attribute = ek(os.stat, self.location)[0]
                if not file_attribute & stat.S_IWRITE:
                    # File is read-only, so make it writeable
                    logger.log('Attempting to make writeable the read only folder {0}'.format(self._location), logger.DEBUG)
                    try:
                        ek(os.chmod, self.location, stat.S_IWRITE)
                    except Exception as error:
                        logger.log('Unable to change permissions of {0}: {1}'.format(self._location, error), logger.WARNING)

                shows_in_folder = main_db_con.select("SELECT location from tv_shows WHERE location LIKE '{showloc}%' AND indexer_id != ?".format(
                    showloc=self.location), [self.indexerid])
                num_shows_in_folder = len(shows_in_folder)
                if num_shows_in_folder:
                    logger.log('Cannot delete the show folder from disk, because this location is the root dir for {num} other shows!'.format(num=num_shows_in_folder))
                    logger.log('Deleting individual episodes. There may be some related files or folders left behind afterwards.')
                    for ep_file in episodes_locations:
                        for show_file in ek(glob.glob, helpers.replace_extension(glob.escape(ep_file[b'location']), '*')):
                            logger.log('Attempt to {0} related file {1}'.format(action, show_file))
                            try:
                                if sickbeard.TRASH_REMOVE_SHOW:
                                    send2trash(show_file)
                                else:
                                    ek(os.remove, show_file)
                            except OSError as error:
                                logger.log('Unable to {0} {1}: {2}'.format(action, show_file, error), logger.WARNING)
                else:
                    if sickbeard.TRASH_REMOVE_SHOW:
                        send2trash(self.location)
                    else:
                        ek(shutil.rmtree, self.location)

                    logger.log('{0} show folder {1}'.format
                               (('Deleted', 'Trashed')[sickbeard.TRASH_REMOVE_SHOW], self._location))

            except ShowDirectoryNotFoundException:
                logger.log("Show folder does not exist, no need to {0} {1}".format(action, self._location), logger.WARNING)
            except OSError as error:
                logger.log('Unable to {0} {1}: {2}'.format(action, self._location, error), logger.WARNING)

        if sickbeard.USE_TRAKT and sickbeard.TRAKT_SYNC_WATCHLIST:
            logger.log("Removing show: indexerid " + str(self.indexerid) + ", Title " + str(self.name) + " from Watchlist", logger.DEBUG)
            notifiers.trakt_notifier.update_watchlist(self, update="remove")

    def populateCache(self):
        cache_inst = image_cache.ImageCache()

        logger.log("Checking & filling cache for show " + self.name, logger.DEBUG)
        cache_inst.fill_cache(self)

    def refreshDir(self):

        # make sure the show dir is where we think it is unless dirs are created on the fly
        if not ek(os.path.isdir, self._location) and not sickbeard.CREATE_MISSING_SHOW_DIRS:
            return False

        # load from dir
        self.loadEpisodesFromDir()

        # run through all locations from DB, check that they exist
        logger.log(str(self.indexerid) + ": Loading all episodes with a location from the database", logger.DEBUG)

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT season, episode, location FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        sql_l = []
        for ep in sql_results:
            curLoc = ek(os.path.normpath, ep[b"location"])
            season = int(ep[b"season"])
            episode = int(ep[b"episode"])

            try:
                curEp = self.getEpisode(season, episode)
                if not curEp:
                    raise EpisodeDeletedException
            except EpisodeDeletedException:
                logger.log("The episode was deleted while we were refreshing it, moving on to the next one",
                           logger.DEBUG)
                continue

            # if the path doesn't exist or if it's not in our show dir
            if not ek(os.path.isfile, curLoc) or not ek(os.path.normpath, curLoc).startswith(
                    ek(os.path.normpath, self.location)):

                # check if downloaded files still exist, update our data if this has changed
                if not sickbeard.SKIP_REMOVED_FILES:
                    with curEp.lock:
                        # if it used to have a file associated with it and it doesn't anymore then set it to sickbeard.EP_DEFAULT_DELETED_STATUS
                        if curEp.location and curEp.status in Quality.DOWNLOADED:

                            if sickbeard.EP_DEFAULT_DELETED_STATUS == ARCHIVED:
                                oldStatus_, oldQuality = Quality.splitCompositeStatus(curEp.status)
                                new_status = Quality.compositeStatus(ARCHIVED, oldQuality)
                            else:
                                new_status = sickbeard.EP_DEFAULT_DELETED_STATUS

                            logger.log("{id}: Location for {ep} doesn't exist, removing it and changing our status to {status}".format
                                       (id=self.indexerid, ep=episode_num(season, episode), status=statusStrings[new_status]), logger.DEBUG)
                            curEp.status = new_status
                            curEp.subtitles = list()
                            curEp.subtitles_searchcount = 0
                            curEp.subtitles_lastsearch = str(datetime.datetime.min)
                        curEp.location = ''
                        curEp.hasnfo = False
                        curEp.hastbn = False
                        curEp.release_name = ''
                        curEp.release_group = ''

                        sql_l.append(curEp.get_sql())

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

    def download_subtitles(self, force=False):
        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, can't download subtitles", logger.DEBUG)
            return

        logger.log("{0}: Downloading subtitles".format(self.indexerid), logger.DEBUG)

        try:
            episodes = self.getAllEpisodes(has_location=True)
            if not episodes:
                logger.log("{0}: No episodes to download subtitles for {1}".format(self.indexerid, self.name), logger.DEBUG)
                return

            for episode in episodes:
                episode.download_subtitles(force=force)

        except Exception:
            logger.log("{0}: Error occurred when downloading subtitles for {1}".format(self.indexerid, self.name), logger.DEBUG)
            logger.log(traceback.format_exc(), logger.ERROR)

    def saveToDB(self, forceSave=False):

        if not self.dirty and not forceSave:
            # logger.log(str(self.indexerid) + ": Not saving show to db - record is not dirty", logger.DEBUG)
            return

        logger.log("{0:d}: Saving to database: {1}".format(self.indexerid, self.name), logger.DEBUG)

        controlValueDict = {"indexer_id": self.indexerid}
        newValueDict = {"indexer": self.indexer,
                        "show_name": self.name,
                        "location": self._location,
                        "network": self.network,
                        "genre": self.genre,
                        "classification": self.classification,
                        "runtime": self.runtime,
                        "quality": self.quality,
                        "airs": self.airs,
                        "status": self.status,
                        "flatten_folders": int(not self.season_folders),  # FIXME: inverted until next database version
                        "paused": self.paused,
                        "air_by_date": self.air_by_date,
                        "anime": self.anime,
                        "scene": self.scene,
                        "sports": self.sports,
                        "subtitles": self.subtitles,
                        "dvdorder": self.dvdorder,
                        "startyear": self.startyear,
                        "lang": self.lang,
                        "imdb_id": self.imdbid,
                        "last_update_indexer": self.last_update_indexer,
                        "rls_ignore_words": self.rls_ignore_words,
                        "rls_require_words": self.rls_require_words,
                        "default_ep_status": self.default_ep_status,
                        "sub_use_sr_metadata": self.subtitles_sr_metadata}

        main_db_con = db.DBConnection()
        main_db_con.upsert("tv_shows", newValueDict, controlValueDict)

        helpers.update_anime_support()

        if self.imdbid and self.imdb_info:
            main_db_con = db.DBConnection()
            main_db_con.upsert("imdb_info", self.imdb_info, controlValueDict)

    def __str__(self):
        toReturn = ""
        toReturn += "indexerid: " + str(self.indexerid) + "\n"
        toReturn += "indexer: " + str(self.indexer) + "\n"
        toReturn += "name: " + self.name + "\n"
        toReturn += "location: " + self._location + "\n"
        if self.network:
            toReturn += "network: " + self.network + "\n"
        if self.airs:
            toReturn += "airs: " + self.airs + "\n"
        toReturn += "status: " + self.status + "\n"
        toReturn += "startyear: " + str(self.startyear) + "\n"
        if self.genre:
            toReturn += "genre: " + self.genre + "\n"
        toReturn += "classification: " + self.classification + "\n"
        toReturn += "runtime: " + str(self.runtime) + "\n"
        toReturn += "quality: " + str(self.quality) + "\n"
        toReturn += "scene: " + str(self.is_scene) + "\n"
        toReturn += "sports: " + str(self.is_sports) + "\n"
        toReturn += "anime: " + str(self.is_anime) + "\n"
        return toReturn

    @staticmethod
    def qualitiesToString(qualities=None):
        return ', '.join([Quality.qualityStrings[quality] for quality in qualities or [] if quality and quality in Quality.qualityStrings]) or 'None'

    def wantEpisode(self, season, episode, quality, manualSearch=False, downCurQuality=False):  # pylint: disable=too-many-return-statements, too-many-arguments

        # if the quality isn't one we want under any circumstances then just say no
        allowed_qualities, preferred_qualities = Quality.splitQuality(self.quality)
        logger.log("Any,Best = [ {0} ] [ {1} ] Found = [ {2} ]".format
                   (self.qualitiesToString(allowed_qualities),
                    self.qualitiesToString(preferred_qualities),
                    self.qualitiesToString([quality])), logger.DEBUG)

        if quality not in allowed_qualities + preferred_qualities or quality is UNKNOWN:
            logger.log("Don't want this quality, ignoring found result for {name} {ep} with quality {quality}".format
                       (name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]),
                       logger.DEBUG)
            return False

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                                         [self.indexerid, season, episode])

        if not sql_results or not len(sql_results):
            logger.log("Unable to find a matching episode in database, ignoring found result for {name} {ep} with quality {quality}".format
                       (name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]), logger.DEBUG)
            return False

        epStatus = int(sql_results[0][b"status"])
        epStatus_text = statusStrings[epStatus]

        # if we know we don't want it then just say no
        if epStatus in Quality.ARCHIVED + [UNAIRED, SKIPPED, IGNORED] and not manualSearch:
            logger.log("Existing episode status is '{status}', ignoring found result for {name} {ep} with quality {quality}".format
                       (status=epStatus_text, name=self.name, ep=episode_num(season, episode),
                        quality=Quality.qualityStrings[quality]), logger.DEBUG)
            return False

        curStatus_, curQuality = Quality.splitCompositeStatus(epStatus)

        # if it's one of these then we want it as long as it's in our allowed initial qualities
        if epStatus in (WANTED, SKIPPED, UNKNOWN, FAILED):
            logger.log("Existing episode status is '{status}', getting found result for {name} {ep} with quality {quality}".format
                       (status=epStatus_text, name=self.name, ep=episode_num(season, episode),
                        quality=Quality.qualityStrings[quality]), logger.DEBUG)
            return True
        elif manualSearch:
            if (downCurQuality and quality >= curQuality) or (not downCurQuality and quality != curQuality):
                logger.log("Usually ignoring found result, but forced search allows the quality,"
                           " getting found result for {name} {ep} with quality {quality}".format
                           (name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]),
                           logger.DEBUG)
                return True

        # if we are re-downloading then we only want it if it's in our preferred_qualities list and better than what we have,
        # or we only have one bestQuality and we do not have that quality yet
        if (epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER and quality in preferred_qualities
            and (quality > curQuality or curQuality not in preferred_qualities)):
            logger.log("Episode already exists with quality {existing_quality} but the found result"
                       " quality {new_quality} is wanted more, getting found result for {name} {ep}".format
                       (existing_quality=Quality.qualityStrings[curQuality],
                        new_quality=Quality.qualityStrings[quality], name=self.name,
                        ep=episode_num(season, episode)), logger.DEBUG)
            return True
        elif curQuality == Quality.UNKNOWN and manualSearch:
            logger.log("Episode already exists but quality is Unknown, getting found result for {name} {ep} with quality {quality}".format
                       (name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]), logger.DEBUG)
            return True
        else:
            logger.log("Episode already exists with quality {existing_quality} and the found result has same/lower quality,"
                       " ignoring found result for {name} {ep} with quality {new_quality}".format
                       (existing_quality=Quality.qualityStrings[curQuality], name=self.name,
                        ep=episode_num(season, episode), new_quality=Quality.qualityStrings[quality]),
                       logger.DEBUG)
        return False

    def getOverview(self, epStatus):  # pylint: disable=too-many-return-statements, too-many-branches
        """
        Get the Overview status from the Episode status

        :param epStatus: an Episode status
        :return: an Overview status
        """

        ep_status = try_int(epStatus) or UNKNOWN

        if ep_status == WANTED:
            return Overview.WANTED
        elif ep_status in (UNAIRED, UNKNOWN):
            return Overview.UNAIRED
        elif ep_status in (SKIPPED, IGNORED):
            return Overview.SKIPPED
        elif ep_status in Quality.ARCHIVED:
            return Overview.GOOD
        elif ep_status in Quality.FAILED:
            return Overview.WANTED
        elif ep_status in Quality.SNATCHED:
            return Overview.SNATCHED
        elif ep_status in Quality.SNATCHED_PROPER:
            return Overview.SNATCHED_PROPER
        elif ep_status in Quality.SNATCHED_BEST:
            return Overview.SNATCHED_BEST
        elif ep_status in Quality.DOWNLOADED:
            allowed_qualities, preferred_qualities = Quality.splitQuality(self.quality)
            ep_status, cur_quality = Quality.splitCompositeStatus(ep_status)

            if cur_quality not in allowed_qualities + preferred_qualities:
                return Overview.QUAL
            elif preferred_qualities and cur_quality not in preferred_qualities:
                return Overview.QUAL
            else:
                return Overview.GOOD
        else:
            logger.log('Could not parse episode status into a valid overview status: {0}'.format(epStatus), logger.ERROR)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d[b'lock']
        return d

    def __setstate__(self, d):
        d[b'lock'] = threading.Lock()
        self.__dict__.update(d)


class TVEpisode(object):  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    def __init__(self, show, season, episode, ep_file=""):
        self._name = ""
        self._season = season
        self._episode = episode
        self._absolute_number = 0
        self._description = ""
        self._subtitles = list()
        self._subtitles_searchcount = 0
        self._subtitles_lastsearch = str(datetime.datetime.min)
        self._airdate = datetime.date.fromordinal(1)
        self._hasnfo = False
        self._hastbn = False
        self._status = UNKNOWN
        self._indexerid = 0
        self._file_size = 0
        self._release_name = ''
        self._is_proper = False
        self._version = 0
        self._release_group = ''

        # setting any of the above sets the dirty flag
        self.dirty = True

        self.show = show

        self.scene_season = 0
        self.scene_episode = 0
        self.scene_absolute_number = 0

        self._location = ep_file

        self._indexer = int(self.show.indexer)

        self.lock = threading.Lock()

        self.specifyEpisode(self.season, self.episode)

        self.relatedEps = []

        self.checkForMetaFiles()

        self.wantedQuality = []

    name = property(lambda self: self._name, dirty_setter("_name"))
    season = property(lambda self: self._season, dirty_setter("_season"))
    episode = property(lambda self: self._episode, dirty_setter("_episode"))
    absolute_number = property(lambda self: self._absolute_number, dirty_setter("_absolute_number"))
    description = property(lambda self: self._description, dirty_setter("_description"))
    subtitles = property(lambda self: self._subtitles, dirty_setter("_subtitles"))
    subtitles_searchcount = property(lambda self: self._subtitles_searchcount, dirty_setter("_subtitles_searchcount"))
    subtitles_lastsearch = property(lambda self: self._subtitles_lastsearch, dirty_setter("_subtitles_lastsearch"))
    airdate = property(lambda self: self._airdate, dirty_setter("_airdate"))
    hasnfo = property(lambda self: self._hasnfo, dirty_setter("_hasnfo"))
    hastbn = property(lambda self: self._hastbn, dirty_setter("_hastbn"))
    status = property(lambda self: self._status, dirty_setter("_status"))
    indexer = property(lambda self: self._indexer, dirty_setter("_indexer"))
    indexerid = property(lambda self: self._indexerid, dirty_setter("_indexerid"))
    # location = property(lambda self: self._location, dirty_setter("_location"))
    file_size = property(lambda self: self._file_size, dirty_setter("_file_size"))
    release_name = property(lambda self: self._release_name, dirty_setter("_release_name"))
    is_proper = property(lambda self: self._is_proper, dirty_setter("_is_proper"))
    version = property(lambda self: self._version, dirty_setter("_version"))
    release_group = property(lambda self: self._release_group, dirty_setter("_release_group"))

    def _set_location(self, new_location):
        logger.log("Setter sets location to " + new_location, logger.DEBUG)

        # self._location = newLocation
        dirty_setter("_location")(self, new_location)

        if new_location and ek(os.path.isfile, new_location):
            self.file_size = ek(os.path.getsize, new_location)
        else:
            self.file_size = 0

    location = property(lambda self: self._location, _set_location)

    def refreshSubtitles(self):
        """Look for subtitles files and refresh the subtitles property"""
        self.subtitles, save_subtitles = subtitles.refresh_subtitles(self)
        if save_subtitles:
            self.saveToDB()

    def download_subtitles(self, force=False, force_lang=None):
        if not ek(os.path.isfile, self.location):
            logger.log("{id}: Episode file doesn't exist, can't download subtitles for {ep}".format
                       (id=self.show.indexerid, ep=episode_num(self.season, self.episode)),
                       logger.DEBUG)
            return

        if not subtitles.needs_subtitles(self.subtitles, force_lang):
            logger.log('Episode already has all needed subtitles, skipping episode {ep} of show {show}'.format
                       (ep=episode_num(self.season, self.episode), show=self.show.name), logger.DEBUG)
            return

        logger.log("Checking subtitle candidates for {show} {ep} ({location})".format
                   (show=self.show.name, ep=episode_num(self.season, self.episode),
                    location=os.path.basename(self.location)), logger.DEBUG)

        self.subtitles, new_subtitles = subtitles.download_subtitles(self, force_lang)

        self.subtitles_searchcount += 1 if self.subtitles_searchcount else 1
        self.subtitles_lastsearch = datetime.datetime.now().strftime(dateTimeFormat)
        self.saveToDB()

        if new_subtitles:
            subtitle_list = ", ".join([subtitles.name_from_code(code) for code in new_subtitles])
            logger.log("{id}: Downloaded {subtitles} subtitles for {show} {ep}".format
                       (id=self.show.indexerid, subtitles=subtitle_list, show=self.show.name,
                        ep=episode_num(self.season, self.episode)), logger.DEBUG)

            notifiers.notify_subtitle_download(self.pretty_name(), subtitle_list)
        else:
            logger.log("{id}: No subtitles downloaded for {show} {ep}".format
                       (id=self.show.indexerid, show=self.show.name,
                        ep=episode_num(self.season, self.episode)), logger.DEBUG)

        return new_subtitles

    def checkForMetaFiles(self):

        oldhasnfo = self.hasnfo
        oldhastbn = self.hastbn

        cur_nfo = False
        cur_tbn = False

        # check for nfo and tbn
        if ek(os.path.isfile, self.location):
            for cur_provider in sickbeard.metadata_provider_dict.values():
                if cur_provider.episode_metadata:
                    new_result = cur_provider._has_episode_metadata(self)  # pylint: disable=protected-access
                else:
                    new_result = False
                cur_nfo = new_result or cur_nfo

                if cur_provider.episode_thumbnails:
                    new_result = cur_provider._has_episode_thumb(self)  # pylint: disable=protected-access
                else:
                    new_result = False
                cur_tbn = new_result or cur_tbn

        self.hasnfo = cur_nfo
        self.hastbn = cur_tbn

        # if either setting has changed return true, if not return false
        return oldhasnfo != self.hasnfo or oldhastbn != self.hastbn

    def specifyEpisode(self, season, episode):

        sql_results = self.loadFromDB(season, episode)

        if not sql_results:
            # only load from NFO if we didn't load from DB
            if ek(os.path.isfile, self.location):
                try:
                    self.loadFromNFO(self.location)
                except NoNFOException:
                    logger.log("{id}: There was an error loading the NFO for episode {ep}".format
                               (id=self.show.indexerid, ep=episode_num(season, episode)), logger.ERROR)

                # if we tried loading it from NFO and didn't find the NFO, try the Indexers
                if not self.hasnfo:
                    try:
                        result = self.loadFromIndexer(season, episode)
                    except EpisodeDeletedException:
                        result = False

                    # if we failed SQL *and* NFO, Indexers then fail
                    if not result:
                        raise EpisodeNotFoundException("Couldn't find episode {ep}".format(ep=episode_num(season, episode)))

    def loadFromDB(self, season, episode):  # pylint: disable=too-many-branches
        # logger.log("{id}: Loading episode details for {name} {ep} from DB".format
        #            (id=self.show.indexerid, name=self.show.name,
        #             ep=episode_num(season, episode)), logger.DEBUG)

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                                         [self.show.indexerid, season, episode])

        if len(sql_results) > 1:
            raise MultipleEpisodesInDatabaseException("Your DB has two records for the same show somehow.")
        elif not sql_results:
            logger.log("{id}: Episode {ep} not found in the database".format
                       (id=self.show.indexerid, ep=episode_num(season, episode)),
                       logger.DEBUG)
            return False
        else:
            if sql_results[0][b"name"]:
                self.name = sql_results[0][b"name"]

            self.season = season
            self.episode = episode
            self.absolute_number = sql_results[0][b"absolute_number"]
            self.description = sql_results[0][b"description"]
            if not self.description:
                self.description = ""
            if sql_results[0][b"subtitles"] and sql_results[0][b"subtitles"]:
                self.subtitles = sql_results[0][b"subtitles"].split(",")
            self.subtitles_searchcount = sql_results[0][b"subtitles_searchcount"]
            self.subtitles_lastsearch = sql_results[0][b"subtitles_lastsearch"]
            self.airdate = datetime.date.fromordinal(int(sql_results[0][b"airdate"]))
            # logger.log("1 Status changes from " + str(self.status) + " to " + str(sql_results[0][b"status"]), logger.DEBUG)
            self.status = int(sql_results[0][b"status"] or -1)

            # don't overwrite my location
            if sql_results[0][b"location"] and not self._location:
                self.location = ek(os.path.normpath, sql_results[0][b"location"])

            if sql_results[0][b"file_size"]:
                self.file_size = int(sql_results[0][b"file_size"])
            else:
                self.file_size = 0

            self.indexerid = int(sql_results[0][b"indexerid"])
            self.indexer = int(sql_results[0][b"indexer"])

            sickbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

            self.scene_season = try_int(sql_results[0][b"scene_season"], 0)
            self.scene_episode = try_int(sql_results[0][b"scene_episode"], 0)
            self.scene_absolute_number = try_int(sql_results[0][b"scene_absolute_number"], 0)

            if self.scene_absolute_number == 0:
                self.scene_absolute_number = sickbeard.scene_numbering.get_scene_absolute_numbering(
                    self.show.indexerid,
                    self.show.indexer,
                    self.absolute_number
                )

            if self.scene_season == 0 or self.scene_episode == 0:
                self.scene_season, self.scene_episode = sickbeard.scene_numbering.get_scene_numbering(
                    self.show.indexerid,
                    self.show.indexer,
                    self.season, self.episode
                )

            if sql_results[0][b"release_name"] is not None:
                self.release_name = sql_results[0][b"release_name"]

            if sql_results[0][b"is_proper"]:
                self.is_proper = int(sql_results[0][b"is_proper"])

            if sql_results[0][b"version"]:
                self.version = int(sql_results[0][b"version"])

            if sql_results[0][b"release_group"] is not None:
                self.release_group = sql_results[0][b"release_group"]

            self.dirty = False
            return True

    def loadFromIndexer(self, season=None, episode=None, cache=True, tvapi=None, cachedSeason=None):  # pylint: disable=too-many-arguments, too-many-branches, too-many-statements

        if season is None:
            season = self.season
        if episode is None:
            episode = self.episode

        # logger.log("{id}: Loading episode details for {show} {ep} from {indexer}".format
        #            (id=self.show.indexerid, show=self.show.name, ep=episode_num(season, episode),
        #             indexer=sickbeard.indexerApi(self.show.indexer).name), logger.DEBUG)

        indexer_lang = self.show.lang

        try:
            if cachedSeason:
                myEp = cachedSeason[episode]
            else:
                if tvapi:
                    t = tvapi
                else:
                    lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

                    if not cache:
                        lINDEXER_API_PARMS['cache'] = False

                    lINDEXER_API_PARMS['language'] = indexer_lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

                    if self.show.dvdorder:
                        lINDEXER_API_PARMS['dvdorder'] = True

                    t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
                myEp = t[self.show.indexerid][season][episode]

        except (sickbeard.indexer_error, IOError) as error:
            logger.log("" + sickbeard.indexerApi(self.indexer).name + " threw up an error: " + ex(error), logger.DEBUG)
            # if the episode is already valid just log it, if not throw it up
            if self.name:
                logger.log("" + sickbeard.indexerApi(self.indexer).name +
                           " timed out but we have enough info from other sources, allowing the error", logger.DEBUG)
                return
            else:
                logger.log("" + sickbeard.indexerApi(self.indexer).name + " timed out, unable to create the episode",
                           logger.ERROR)
                return False
        except (sickbeard.indexer_episodenotfound, sickbeard.indexer_seasonnotfound):
            logger.log("Unable to find the episode on " + sickbeard.indexerApi(
                self.indexer).name + "... has it been removed? Should I delete from db?", logger.DEBUG)
            # if I'm no longer on the Indexers but I once was then delete myself from the DB
            if self.indexerid != -1:
                self.deleteEpisode()
            return

        if getattr(myEp, 'episodename', None) is None:
            logger.log("This episode {show} - {ep} has no name on {indexer}. Setting to an empty string".format
                       (show=self.show.name, ep=episode_num(season, episode), indexer=sickbeard.indexerApi(self.indexer).name))
            setattr(myEp, 'episodename', '')

        if getattr(myEp, 'absolute_number', None) is None:
            logger.log("{id}: This episode {show} - {ep} has no absolute number on {indexer}".format
                       (id=self.show.indexerid, show=self.show.name, ep=episode_num(season, episode),
                        indexer=sickbeard.indexerApi(self.indexer).name), logger.DEBUG)
        else:
            logger.log("{id}: The absolute number for {ep} is: {absolute} ".format
                       (id=self.show.indexerid, ep=episode_num(season, episode), absolute=myEp[b"absolute_number"]), logger.DEBUG)
            self.absolute_number = int(myEp[b"absolute_number"])

        self.name = getattr(myEp, 'episodename', "")
        self.season = season
        self.episode = episode

        sickbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

        self.scene_absolute_number = sickbeard.scene_numbering.get_scene_absolute_numbering(
            self.show.indexerid,
            self.show.indexer,
            self.absolute_number
        )

        self.scene_season, self.scene_episode = sickbeard.scene_numbering.get_scene_numbering(
            self.show.indexerid,
            self.show.indexer,
            self.season, self.episode
        )

        self.description = getattr(myEp, 'overview', "")

        firstaired = getattr(myEp, 'firstaired', None)
        if not firstaired or firstaired == "0000-00-00":
            firstaired = str(datetime.date.fromordinal(1))
        rawAirdate = [int(x) for x in firstaired.split("-")]

        try:
            self.airdate = datetime.date(rawAirdate[0], rawAirdate[1], rawAirdate[2])
        except (ValueError, IndexError):
            logger.log("Malformed air date of {aired} retrieved from {indexer} for ({show} - {ep})".format
                       (aired=firstaired, indexer=sickbeard.indexerApi(self.indexer).name, show=self.show.name,
                        ep=episode_num(season, episode)), logger.WARNING)
            # if I'm incomplete on the indexer but I once was complete then just delete myself from the DB for now
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        # early conversion to int so that episode doesn't get marked dirty
        self.indexerid = getattr(myEp, 'id', None)
        if self.indexerid is None:
            logger.log("Failed to retrieve ID from {indexer}".format
                       (indexer=sickbeard.indexerApi(self.indexer).name), logger.ERROR)
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        # don't update show status if show dir is missing, unless it's missing on purpose
        if not ek(os.path.isdir, self.show._location) and not sickbeard.CREATE_MISSING_SHOW_DIRS and not sickbeard.ADD_SHOWS_WO_DIR:  # pylint: disable=protected-access
            logger.log("The show dir {0} is missing, not bothering to change the episode statuses since it'd probably be invalid".format(self.show._location))  # pylint: disable=protected-access
            return

        if self.location:
            logger.log("{id}: Setting status for {ep} based on status {status} and location {location}".format
                       (id=self.show.indexerid, ep=episode_num(season, episode),
                        status=statusStrings[self.status], location=self.location), logger.DEBUG)

        if not ek(os.path.isfile, self.location):
            if self.airdate >= datetime.date.today() or self.airdate == datetime.date.fromordinal(1):
                logger.log("{0}: Episode airs in the future or has no airdate, marking it {1}".format(self.show.indexerid, statusStrings[UNAIRED]), logger.DEBUG)
                self.status = UNAIRED
            elif self.status in [UNAIRED, UNKNOWN]:
                # Only do UNAIRED/UNKNOWN, it could already be snatched/ignored/skipped, or downloaded/archived to disconnected media
                logger.log("Episode has already aired, marking it {0}".format(statusStrings[self.show.default_ep_status]), logger.DEBUG)
                self.status = self.show.default_ep_status if self.season > 0 else SKIPPED  # auto-skip specials
            else:
                logger.log("Not touching status [ {0} ] It could be skipped/ignored/snatched/archived".format(statusStrings[self.status]), logger.DEBUG)

        # if we have a media file then it's downloaded
        elif sickbeard.helpers.is_media_file(self.location):
            # leave propers alone, you have to either post-process them or manually change them back
            if self.status not in Quality.SNATCHED_PROPER + Quality.DOWNLOADED + Quality.SNATCHED + Quality.ARCHIVED:
                logger.log(
                    "5 Status changes from " + str(self.status) + " to " + str(Quality.statusFromName(self.location)),
                    logger.DEBUG)
                self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

        # shouldn't get here probably
        else:
            logger.log("6 Status changes from " + str(self.status) + " to " + str(UNKNOWN), logger.DEBUG)
            self.status = UNKNOWN

    def loadFromNFO(self, location):  # pylint: disable=too-many-branches

        if not ek(os.path.isdir, self.show._location):  # pylint: disable=protected-access
            logger.log(
                str(self.show.indexerid) + ": The show dir is missing, not bothering to try loading the episode NFO")
            return

        logger.log(
            str(self.show.indexerid) + ": Loading episode details from the NFO file associated with " + location,
            logger.DEBUG)

        self.location = location

        if self.location != "":

            if self.status == UNKNOWN and sickbeard.helpers.is_media_file(self.location):
                logger.log("7 Status changes from " + str(self.status) + " to " + str(
                    Quality.statusFromName(self.location, anime=self.show.is_anime)), logger.DEBUG)
                self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

            nfoFile = replace_extension(self.location, "nfo")
            logger.log(str(self.show.indexerid) + ": Using NFO name " + nfoFile, logger.DEBUG)

            if ek(os.path.isfile, nfoFile):
                try:
                    showXML = etree.ElementTree(file=nfoFile)
                except (SyntaxError, ValueError) as error:
                    logger.log("Error loading the NFO, backing up the NFO and skipping for now: " + ex(error), logger.ERROR)
                    try:
                        ek(os.rename, nfoFile, nfoFile + ".old")
                    except Exception as error:
                        logger.log(
                            "Failed to rename your episode's NFO file - you need to delete it or fix it: " + ex(error), logger.ERROR)
                    raise NoNFOException("Error in NFO format")

                for epDetails in showXML.getiterator('episodedetails'):
                    if epDetails.findtext('season') is None or int(epDetails.findtext('season')) != self.season or \
                       epDetails.findtext('episode') is None or int(epDetails.findtext('episode')) != self.episode:
                        logger.log("{id}: NFO has an <episodedetails> block for a different episode - wanted {ep_wanted} but got {ep_found}".format
                                   (id=self.show.indexerid, ep_wanted=episode_num(self.season, self.episode),
                                    ep_found=episode_num(epDetails.findtext('season'), epDetails.findtext('episode'))),
                                   logger.DEBUG)
                        continue

                    if epDetails.findtext('title') is None or epDetails.findtext('aired') is None:
                        raise NoNFOException("Error in NFO format (missing episode title or airdate)")

                    self.name = epDetails.findtext('title')
                    self.episode = int(epDetails.findtext('episode'))
                    self.season = int(epDetails.findtext('season'))

                    sickbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

                    self.scene_absolute_number = sickbeard.scene_numbering.get_scene_absolute_numbering(
                        self.show.indexerid,
                        self.show.indexer,
                        self.absolute_number
                    )

                    self.scene_season, self.scene_episode = sickbeard.scene_numbering.get_scene_numbering(
                        self.show.indexerid,
                        self.show.indexer,
                        self.season, self.episode
                    )

                    self.description = epDetails.findtext('plot')
                    if self.description is None:
                        self.description = ""

                    if epDetails.findtext('aired'):
                        rawAirdate = [int(x) for x in epDetails.findtext('aired').split("-")]
                        self.airdate = datetime.date(rawAirdate[0], rawAirdate[1], rawAirdate[2])
                    else:
                        self.airdate = datetime.date.fromordinal(1)

                    self.hasnfo = True
            else:
                self.hasnfo = False

            if ek(os.path.isfile, replace_extension(nfoFile, "tbn")):
                self.hastbn = True
            else:
                self.hastbn = False

    def __str__(self):

        toReturn = ""
        toReturn += "{0!r} - S{1!r}E{2!r} - {3!r}\n".format(self.show.name, self.season, self.episode, self.name)
        toReturn += "location: {0!r}\n".format(self.location)
        toReturn += "description: {0!r}\n".format(self.description)
        toReturn += "subtitles: {0!r}\n".format(",".join(self.subtitles))
        toReturn += "subtitles_searchcount: {0!r}\n".format(self.subtitles_searchcount)
        toReturn += "subtitles_lastsearch: {0!r}\n".format(self.subtitles_lastsearch)
        toReturn += "airdate: {0!r} ({1!r})\n".format(self.airdate.toordinal(), self.airdate)
        toReturn += "hasnfo: {0!r}\n".format(self.hasnfo)
        toReturn += "hastbn: {0!r}\n".format(self.hastbn)
        toReturn += "status: {0!r}\n".format(self.status)
        return toReturn

    def createMetaFiles(self):

        if not ek(os.path.isdir, self.show._location):  # pylint: disable=protected-access
            logger.log(str(self.show.indexerid) + ": The show dir is missing, not bothering to try to create metadata")
            return

        self.createNFO()
        self.createThumbnail()

        if self.checkForMetaFiles():
            self.saveToDB()

    def createNFO(self):

        result = False

        for cur_provider in sickbeard.metadata_provider_dict.values():
            result = cur_provider.create_episode_metadata(self) or result

        return result

    def createThumbnail(self):

        result = False

        for cur_provider in sickbeard.metadata_provider_dict.values():
            result = cur_provider.create_episode_thumb(self) or result

        return result

    def deleteEpisode(self):

        logger.log("Deleting {show} {ep} from the DB".format
                   (show=self.show.name, ep=episode_num(self.season, self.episode)), logger.DEBUG)

        # remove myself from the show dictionary
        if self.show.getEpisode(self.season, self.episode, noCreate=True) == self:
            logger.log("Removing myself from my show's list", logger.DEBUG)
            del self.show.episodes[self.season][self.episode]

        # delete myself from the DB
        logger.log("Deleting myself from the database", logger.DEBUG)
        main_db_con = db.DBConnection()
        sql = "DELETE FROM tv_episodes WHERE showid=" + str(self.show.indexerid) + " AND season=" + str(
            self.season) + " AND episode=" + str(self.episode)
        main_db_con.action(sql)

        raise EpisodeDeletedException()

    def get_sql(self, forceSave=False):
        """
        Creates SQL queue for this episode if any of its data has been changed since the last save.

        forceSave: If True it will create SQL queue even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """
        try:
            if not self.dirty and not forceSave:
                logger.log(str(self.show.indexerid) + ": Not creating SQL queue - record is not dirty", logger.DEBUG)
                return

            main_db_con = db.DBConnection()
            rows = main_db_con.select(
                'SELECT episode_id, subtitles FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?',
                [self.show.indexerid, self.season, self.episode])

            epID = None
            if rows:
                epID = int(rows[0][b'episode_id'])

            if epID:
                # use a custom update method to get the data into the DB for existing records.
                # Multi or added subtitle or removed subtitles
                if sickbeard.SUBTITLES_MULTI or not rows[0][b'subtitles'] or not self.subtitles:
                    return [
                        "UPDATE tv_episodes SET indexerid = ?, indexer = ?, name = ?, description = ?, subtitles = ?, "
                        "subtitles_searchcount = ?, subtitles_lastsearch = ?, airdate = ?, hasnfo = ?, hastbn = ?, status = ?, "
                        "location = ?, file_size = ?, release_name = ?, is_proper = ?, showid = ?, season = ?, episode = ?, "
                        "absolute_number = ?, version = ?, release_group = ? WHERE episode_id = ?",
                        [self.indexerid, self.indexer, self.name, self.description, ",".join(self.subtitles),
                         self.subtitles_searchcount, self.subtitles_lastsearch, self.airdate.toordinal(), self.hasnfo,
                         self.hastbn,
                         self.status, self.location, self.file_size, self.release_name, self.is_proper, self.show.indexerid,
                         self.season, self.episode, self.absolute_number, self.version, self.release_group, epID]]
                else:
                    # Don't update the subtitle language when the srt file doesn't contain the alpha2 code, keep value from subliminal
                    return [
                        "UPDATE tv_episodes SET indexerid = ?, indexer = ?, name = ?, description = ?, "
                        "subtitles_searchcount = ?, subtitles_lastsearch = ?, airdate = ?, hasnfo = ?, hastbn = ?, status = ?, "
                        "location = ?, file_size = ?, release_name = ?, is_proper = ?, showid = ?, season = ?, episode = ?, "
                        "absolute_number = ?, version = ?, release_group = ? WHERE episode_id = ?",
                        [self.indexerid, self.indexer, self.name, self.description,
                         self.subtitles_searchcount, self.subtitles_lastsearch, self.airdate.toordinal(), self.hasnfo,
                         self.hastbn,
                         self.status, self.location, self.file_size, self.release_name, self.is_proper, self.show.indexerid,
                         self.season, self.episode, self.absolute_number, self.version, self.release_group, epID]]
            else:
                # use a custom insert method to get the data into the DB.
                return [
                    "INSERT OR IGNORE INTO tv_episodes (episode_id, indexerid, indexer, name, description, subtitles, "
                    "subtitles_searchcount, subtitles_lastsearch, airdate, hasnfo, hastbn, status, location, file_size, "
                    "release_name, is_proper, showid, season, episode, absolute_number, version, release_group) VALUES "
                    "((SELECT episode_id FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?)"
                    ",?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
                    [self.show.indexerid, self.season, self.episode, self.indexerid, self.indexer, self.name,
                     self.description, ",".join(self.subtitles), self.subtitles_searchcount, self.subtitles_lastsearch,
                     self.airdate.toordinal(), self.hasnfo, self.hastbn, self.status, self.location, self.file_size,
                     self.release_name, self.is_proper, self.show.indexerid, self.season, self.episode,
                     self.absolute_number, self.version, self.release_group]]
        except Exception as error:
            logger.log("Error while updating database: {0}".format(error), logger.ERROR)

    def saveToDB(self, forceSave=False):
        """
        Saves this episode to the database if any of its data has been changed since the last save.

        forceSave: If True it will save to the database even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """

        if not self.dirty and not forceSave:
            # logger.log(str(self.show.indexerid) + ": Not saving episode to db - record is not dirty", logger.DEBUG)
            return

        newValueDict = {"indexerid": self.indexerid,
                        "indexer": self.indexer,
                        "name": self.name,
                        "description": self.description,
                        "subtitles": ",".join(self.subtitles),
                        "subtitles_searchcount": self.subtitles_searchcount,
                        "subtitles_lastsearch": self.subtitles_lastsearch,
                        "airdate": self.airdate.toordinal(),
                        "hasnfo": self.hasnfo,
                        "hastbn": self.hastbn,
                        "status": self.status,
                        "location": self.location,
                        "file_size": self.file_size,
                        "release_name": self.release_name,
                        "is_proper": self.is_proper,
                        "absolute_number": self.absolute_number,
                        "version": self.version,
                        "release_group": self.release_group}

        controlValueDict = {"showid": self.show.indexerid,
                            "season": self.season,
                            "episode": self.episode}

        # logger.log("%s: Saving episode details to database %rx%r: %s" %
        #            (self.show.indexerid, self.season, self.episode, statusStrings[self.status]), logger.DEBUG)

        # use a custom update/insert method to get the data into the DB
        main_db_con = db.DBConnection()
        main_db_con.upsert("tv_episodes", newValueDict, controlValueDict)

    def fullPath(self):
        if self.location is None or self.location == "":
            return None
        else:
            return ek(os.path.join, self.show.location, self.location)

    def createStrings(self, pattern=None):
        patterns = [
            '%S.N.S%SE%0E',
            '%S.N.S%0SE%E',
            '%S.N.S%SE%E',
            '%S.N.S%0SE%0E',
            '%SN S%SE%0E',
            '%SN S%0SE%E',
            '%SN S%SE%E',
            '%SN S%0SE%0E'
        ]

        strings = []
        if not pattern:
            for p in patterns:
                strings += [self._format_pattern(p)]
            return strings
        return self._format_pattern(pattern)

    def pretty_name(self):
        """
        Returns the name of this episode in a "pretty" human-readable format. Used for logging
        and notifications and such.

        Returns: A string representing the episode's name and season/ep numbers
        """

        if self.show.anime and not self.show.scene:
            return self._format_pattern('%SN - %AB - %EN')
        elif self.show.air_by_date:
            return self._format_pattern('%SN - %AD - %EN')

        return self._format_pattern('%SN - S%0SE%0E - %EN')

    def _ep_name(self):
        """
        Returns the name of the episode to use during renaming. Combines the names of related episodes.
        Eg. "Ep Name (1)" and "Ep Name (2)" becomes "Ep Name"
            "Ep Name" and "Other Ep Name" becomes "Ep Name & Other Ep Name"
        """

        multiNameRegex = r"(.*) \(\d{1,2}\)"

        self.relatedEps = sorted(self.relatedEps, key=lambda x: x.episode)

        if not self.relatedEps:
            goodName = self.name
        else:
            goodName = ''

            singleName = True
            curGoodName = None

            for curName in [self.name] + [x.name for x in self.relatedEps]:
                match = re.match(multiNameRegex, curName)
                if not match:
                    singleName = False
                    break

                if curGoodName is None:
                    curGoodName = match.group(1)
                elif curGoodName != match.group(1):
                    singleName = False
                    break

            if singleName:
                goodName = curGoodName
            else:
                goodName = self.name
                for relEp in self.relatedEps:
                    goodName += " & " + relEp.name

        return goodName

    def _replace_map(self):  # pylint: disable=too-many-branches
        """
        Generates a replacement map for this episode which maps all possible custom naming patterns to the correct
        value for this episode.

        Returns: A dict with patterns as the keys and their replacement values as the values.
        """

        ep_name = self._ep_name()

        def dot(name):
            # assert isinstance(name, unicode), name + ' is not unicode'
            return helpers.sanitizeSceneName(name)

        def us(name):
            return re.sub('[ -]', '_', name)

        def release_name(name):
            if name:
                name = helpers.remove_non_release_groups(remove_extension(name))
            return name

        def release_group(show, name):
            if name:
                name = helpers.remove_non_release_groups(remove_extension(name))
            else:
                return ''

            try:
                parse_result = NameParser(name, showObj=show, naming_pattern=True).parse(name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.log("Unable to get parse release_group: {0}".format(error), logger.DEBUG)
                return ''

            if not parse_result.release_group:
                return ''
            return parse_result.release_group.strip('.- []{}')

        epStatus_, epQual = Quality.splitCompositeStatus(self.status)  # @UnusedVariable

        if sickbeard.NAMING_STRIP_YEAR:
            show_name = re.sub(r"\(\d+\)$", "", self.show.name).strip()
        else:
            show_name = self.show.name

        # try to get the release group
        rel_grp = {
            "SickRage": 'SickRage'
        }
        if hasattr(self, 'location'):  # from the location name
            rel_grp[b'location'] = release_group(self.show, self.location)
            if not rel_grp[b'location']:
                del rel_grp[b'location']
        if hasattr(self, '_release_group'):  # from the release group field in db
            rel_grp[b'database'] = self._release_group.strip('.- []{}')
            if not rel_grp[b'database']:
                del rel_grp[b'database']
        if hasattr(self, 'release_name'):  # from the release name field in db
            rel_grp[b'release_name'] = release_group(self.show, self.release_name)
            if not rel_grp[b'release_name']:
                del rel_grp[b'release_name']

        # use release_group, release_name, location in that order
        if 'database' in rel_grp:
            relgrp = 'database'
        elif 'release_name' in rel_grp:
            relgrp = 'release_name'
        elif 'location' in rel_grp:
            relgrp = 'location'
        else:
            relgrp = 'SickRage'

        # try to get the release encoder to comply with scene naming standards
        encoder = Quality.sceneQualityFromName(self.release_name.replace(rel_grp[relgrp], ""), epQual)
        if encoder:
            logger.log("Found codec for '" + show_name + ": " + ep_name + "'.", logger.DEBUG)

        return {
            '%SN': show_name,
            '%S.N': dot(show_name),
            '%S_N': us(show_name),
            '%EN': ep_name,
            '%E.N': dot(ep_name),
            '%E_N': us(ep_name),
            '%QN': Quality.qualityStrings[epQual],
            '%Q.N': dot(Quality.qualityStrings[epQual]),
            '%Q_N': us(Quality.qualityStrings[epQual]),
            '%SQN': Quality.sceneQualityStrings[epQual] + encoder,
            '%SQ.N': dot(Quality.sceneQualityStrings[epQual] + encoder),
            '%SQ_N': us(Quality.sceneQualityStrings[epQual] + encoder),
            '%S': str(self.season),
            '%0S': '{0:02d}'.format(int(self.season)),
            '%E': str(self.episode),
            '%0E': '{0:02d}'.format(int(self.episode)),
            '%XS': str(self.scene_season),
            '%0XS': '{0:02d}'.format(int(self.scene_season)),
            '%XE': str(self.scene_episode),
            '%0XE': '{0:02d}'.format(int(self.scene_episode)),
            '%AB': '{0:03d}'.format(int(self.absolute_number)),
            '%XAB': '{0:03d}'.format(int(self.scene_absolute_number)),
            '%RN': release_name(self.release_name),
            '%RG': rel_grp[relgrp],
            '%CRG': rel_grp[relgrp].upper(),
            '%AD': str(self.airdate).replace('-', ' '),
            '%A.D': str(self.airdate).replace('-', '.'),
            '%A_D': us(str(self.airdate)),
            '%A-D': str(self.airdate),
            '%Y': str(self.airdate.year),
            '%M': str(self.airdate.month),
            '%D': str(self.airdate.day),
            '%CY': str(datetime.date.today().year),
            '%CM': str(datetime.date.today().month),
            '%CD': str(datetime.date.today().day),
            '%0M': '{0:02d}'.format(int(self.airdate.month)),
            '%0D': '{0:02d}'.format(int(self.airdate.day)),
            '%RT': "PROPER" if self.is_proper else "",
        }

    @staticmethod
    def _format_string(pattern, replace_map):
        """
        Replaces all template strings with the correct value
        """

        result_name = pattern

        # do the replacements
        for cur_replacement in sorted(replace_map.keys(), reverse=True):
            result_name = result_name.replace(cur_replacement, sanitize_filename(replace_map[cur_replacement]))
            result_name = result_name.replace(cur_replacement.lower(),
                                              sanitize_filename(replace_map[cur_replacement].lower()))

        return result_name

    def _format_pattern(self, pattern=None, multi=None, anime_type=None):  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
        """
        Manipulates an episode naming pattern and then fills the template in
        """

        if pattern is None:
            pattern = sickbeard.NAMING_PATTERN

        if multi is None:
            multi = sickbeard.NAMING_MULTI_EP

        if sickbeard.NAMING_CUSTOM_ANIME:
            if anime_type is None:
                anime_type = sickbeard.NAMING_ANIME
        else:
            anime_type = 3

        replace_map = self._replace_map()

        result_name = pattern

        # if there's no release group in the db, let the user know we replaced it
        if replace_map[b'%RG'] and replace_map[b'%RG'] != 'SickRage':
            if not hasattr(self, '_release_group'):
                logger.log("Episode has no release group, replacing it with '" + replace_map[b'%RG'] + "'", logger.DEBUG)
                self._release_group = replace_map[b'%RG']  # if release_group is not in the db, put it there
            elif not self._release_group:
                logger.log("Episode has no release group, replacing it with '" + replace_map[b'%RG'] + "'", logger.DEBUG)
                self._release_group = replace_map[b'%RG']  # if release_group is not in the db, put it there

        # if there's no release name then replace it with a reasonable facsimile
        if not replace_map[b'%RN']:

            if self.show.air_by_date or self.show.sports:
                result_name = result_name.replace('%RN', '%S.N.%A.D.%E.N-' + replace_map[b'%RG'])
                result_name = result_name.replace('%rn', '%s.n.%A.D.%e.n-' + replace_map[b'%RG'].lower())

            elif anime_type != 3:
                result_name = result_name.replace('%RN', '%S.N.%AB.%E.N-' + replace_map[b'%RG'])
                result_name = result_name.replace('%rn', '%s.n.%ab.%e.n-' + replace_map[b'%RG'].lower())

            else:
                result_name = result_name.replace('%RN', '%S.N.S%0SE%0E.%E.N-' + replace_map[b'%RG'])
                result_name = result_name.replace('%rn', '%s.n.s%0se%0e.%e.n-' + replace_map[b'%RG'].lower())

            # logger.log("Episode has no release name, replacing it with a generic one: " + result_name, logger.DEBUG)

        if not replace_map[b'%RT']:
            result_name = re.sub('([ _.-]*)%RT([ _.-]*)', r'\2', result_name)

        # split off ep name part only
        name_groups = re.split(r'[\\/]', result_name)

        # figure out the double-ep numbering style for each group, if applicable
        for cur_name_group in name_groups:

            season_format = sep = ep_sep = ep_format = None

            season_ep_regex = r'''
                                (?P<pre_sep>[ _.-]*)
                                ((?:s(?:eason|eries)?\s*)?%0?S(?![._]?N))
                                (.*?)
                                (%0?E(?![._]?N))
                                (?P<post_sep>[ _.-]*)
                              '''
            ep_only_regex = r'(E?%0?E(?![._]?N))'

            # try the normal way
            season_ep_match = re.search(season_ep_regex, cur_name_group, re.I | re.X)
            ep_only_match = re.search(ep_only_regex, cur_name_group, re.I | re.X)

            # if we have a season and episode then collect the necessary data
            if season_ep_match:
                season_format = season_ep_match.group(2)
                ep_sep = season_ep_match.group(3)
                ep_format = season_ep_match.group(4)
                sep = season_ep_match.group('pre_sep')
                if not sep:
                    sep = season_ep_match.group('post_sep')
                if not sep:
                    sep = ' '

                # force 2-3-4 format if they chose to extend
                if multi in (NAMING_EXTEND, NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED):
                    ep_sep = '-'

                regex_used = season_ep_regex

            # if there's no season then there's not much choice so we'll just force them to use 03-04-05 style
            elif ep_only_match:
                season_format = ''
                ep_sep = '-'
                ep_format = ep_only_match.group(1)
                sep = ''
                regex_used = ep_only_regex

            else:
                continue

            # we need at least this much info to continue
            if not ep_sep or not ep_format:
                continue

            # start with the ep string, eg. E03
            ep_string = self._format_string(ep_format.upper(), replace_map)
            for other_ep in self.relatedEps:

                # for limited extend we only append the last ep
                if multi in (NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED) and other_ep != self.relatedEps[-1]:
                    continue

                elif multi == NAMING_DUPLICATE:
                    # add " - S01"
                    ep_string += sep + season_format

                elif multi == NAMING_SEPARATED_REPEAT:
                    ep_string += sep

                # add "E04"
                ep_string += ep_sep

                if multi == NAMING_LIMITED_EXTEND_E_PREFIXED:
                    ep_string += 'E'

                ep_string += other_ep._format_string(ep_format.upper(), other_ep._replace_map())  # pylint: disable=protected-access

            if anime_type != 3:
                if self.absolute_number == 0:
                    curAbsolute_number = self.episode
                else:
                    curAbsolute_number = self.absolute_number

                if self.season != 0:  # dont set absolute numbers if we are on specials !
                    if anime_type == 1:  # this crazy person wants both ! (note: +=)
                        ep_string += sep + "{#:03d}".format(**{
                            "#": curAbsolute_number})
                    elif anime_type == 2:  # total anime freak only need the absolute number ! (note: =)
                        ep_string = "{#:03d}".format(**{"#": curAbsolute_number})

                    for relEp in self.relatedEps:
                        if relEp.absolute_number != 0:
                            ep_string += '-' + "{#:03d}".format(**{"#": relEp.absolute_number})
                        else:
                            ep_string += '-' + "{#:03d}".format(**{"#": relEp.episode})

            regex_replacement = None
            if anime_type == 2 and not ep_only_match:
                regex_replacement = r'\g<pre_sep>' + ep_string + r'\g<post_sep>'
            elif season_ep_match:
                regex_replacement = r'\g<pre_sep>\g<2>\g<3>' + ep_string + r'\g<post_sep>'
            elif ep_only_match:
                regex_replacement = ep_string

            if regex_replacement:
                # fill out the template for this piece and then insert this piece into the actual pattern
                cur_name_group_result = re.sub('(?i)(?x)' + regex_used, regex_replacement, cur_name_group)
                # cur_name_group_result = cur_name_group.replace(ep_format, ep_string)
                result_name = result_name.replace(cur_name_group, cur_name_group_result)

        result_name = self._format_string(result_name, replace_map)

        logger.log("formatting pattern: " + pattern + " -> " + result_name, logger.DEBUG)

        return result_name

    def proper_path(self):
        """
        Figures out the path where this episode SHOULD live according to the renaming rules, relative from the show dir
        """

        anime_type = sickbeard.NAMING_ANIME
        if not self.show.is_anime:
            anime_type = 3

        result = self.formatted_filename(anime_type=anime_type)

        # if they want us to flatten it and we're allowed to flatten it then we will
        if not (self.show.season_folders or sickbeard.NAMING_FORCE_FOLDERS):
            return result

        # if not we append the folder on and use that
        else:
            result = ek(os.path.join, self.formatted_dir(anime_type=anime_type), result)

        return result

    def formatted_dir(self, pattern=None, multi=None, anime_type=None):
        """
        Just the folder name of the episode
        """

        if pattern is None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and sickbeard.NAMING_CUSTOM_ABD and not self.relatedEps:
                pattern = sickbeard.NAMING_ABD_PATTERN
            elif self.show.sports and sickbeard.NAMING_CUSTOM_SPORTS and not self.relatedEps:
                pattern = sickbeard.NAMING_SPORTS_PATTERN
            elif self.show.anime and sickbeard.NAMING_CUSTOM_ANIME:
                pattern = sickbeard.NAMING_ANIME_PATTERN
            else:
                pattern = sickbeard.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        if len(name_groups) == 1:
            return ''
        else:
            return self._format_pattern(os.sep.join(name_groups[:-1]), multi, anime_type)

    def formatted_filename(self, pattern=None, multi=None, anime_type=None):
        """
        Just the filename of the episode, formatted based on the naming settings
        """

        if pattern is None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and sickbeard.NAMING_CUSTOM_ABD and not self.relatedEps:
                pattern = sickbeard.NAMING_ABD_PATTERN
            elif self.show.sports and sickbeard.NAMING_CUSTOM_SPORTS and not self.relatedEps:
                pattern = sickbeard.NAMING_SPORTS_PATTERN
            elif self.show.anime and sickbeard.NAMING_CUSTOM_ANIME:
                pattern = sickbeard.NAMING_ANIME_PATTERN
            else:
                pattern = sickbeard.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        return sanitize_filename(self._format_pattern(name_groups[-1], multi, anime_type))

    def rename(self):  # pylint: disable=too-many-locals, too-many-branches
        """
        Renames an episode file and all related files to the location and filename as specified
        in the naming settings.
        """

        if not ek(os.path.isfile, self.location):
            logger.log("Can't perform rename on " + self.location + " when it doesn't exist, skipping", logger.WARNING)
            return

        proper_path = self.proper_path()
        absolute_proper_path = ek(os.path.join, self.show.location, proper_path)
        absolute_current_path_no_ext, file_ext = ek(os.path.splitext, self.location)
        absolute_current_path_no_ext_length = len(absolute_current_path_no_ext)

        related_subs = []

        current_path = absolute_current_path_no_ext

        if absolute_current_path_no_ext.startswith(self.show.location):
            current_path = absolute_current_path_no_ext[len(self.show.location):]

        logger.log("Renaming/moving episode from the base path " + self.location + " to " + absolute_proper_path,
                   logger.DEBUG)

        # if it's already named correctly then don't do anything
        if proper_path == current_path:
            logger.log(str(self.indexerid) + ": File " + self.location + " is already named correctly, skipping",
                       logger.DEBUG)
            return

        # get related files
        related_files = postProcessor.PostProcessor(self.location).list_associated_files(
            self.location, subfolders=True, rename=True)

        # get related subs
        if self.show.subtitles and sickbeard.SUBTITLES_DIR:
            # assume that the video file is in the subtitles dir to find associated subs
            subs_path = os.path.join(sickbeard.SUBTITLES_DIR, ek(os.path.basename, self.location))
            related_subs = postProcessor.PostProcessor(self.location).list_associated_files(
                subs_path, subtitles_only=True, subfolders=True, rename=True)

        logger.log("Files associated to " + self.location + ": " + str(related_files), logger.DEBUG)

        # move the ep file
        result = helpers.rename_ep_file(self.location, absolute_proper_path, absolute_current_path_no_ext_length)

        if sickbeard.MOVE_ASSOCIATED_FILES:
            # move related files
            for cur_related_file in related_files:
                # We need to fix something here because related files can be in subfolders and the original code doesn't handle this (at all)
                cur_related_dir = ek(os.path.dirname, ek(os.path.abspath, cur_related_file))
                subfolder = cur_related_dir.replace(ek(os.path.dirname, ek(os.path.abspath, self.location)), '')
                # We now have a subfolder. We need to add that to the absolute_proper_path.
                # First get the absolute proper-path dir
                proper_related_dir = ek(os.path.dirname, ek(os.path.abspath, absolute_proper_path + file_ext))
                proper_related_path = absolute_proper_path.replace(proper_related_dir, proper_related_dir + subfolder)

                cur_result = helpers.rename_ep_file(cur_related_file, proper_related_path,
                                                    absolute_current_path_no_ext_length + len(subfolder))
                if not cur_result:
                    logger.log(str(self.indexerid) + ": Unable to rename file " + cur_related_file, logger.ERROR)

            for cur_related_sub in related_subs:
                absolute_proper_subs_path = ek(os.path.join, sickbeard.SUBTITLES_DIR, self.formatted_filename())
                cur_result = helpers.rename_ep_file(cur_related_sub, absolute_proper_subs_path,
                                                    absolute_current_path_no_ext_length)
                if not cur_result:
                    logger.log(str(self.indexerid) + ": Unable to rename file " + cur_related_sub, logger.ERROR)

        # save the ep
        with self.lock:
            if result:
                self.location = absolute_proper_path + file_ext
                for relEp in self.relatedEps:
                    relEp.location = absolute_proper_path + file_ext

        # in case something changed with the metadata just do a quick check
        for curEp in [self] + self.relatedEps:
            curEp.checkForMetaFiles()

        # save any changes to the databas
        sql_l = []
        with self.lock:
            for relEp in [self] + self.relatedEps:
                sql_l.append(relEp.get_sql())

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

    def airdateModifyStamp(self):
        """
        Make the modify date and time of a file reflect the show air date and time.
        Note: Also called from postProcessor

        """
        if not all([sickbeard.AIRDATE_EPISODES, self.airdate, self.location,
                    self.show, self.show.airs, self.show.network]):
            return

        try:
            airdate_ordinal = self.airdate.toordinal()
            if airdate_ordinal < 1:
                return

            airdatetime = network_timezones.parse_date_time(airdate_ordinal, self.show.airs, self.show.network)

            if sickbeard.FILE_TIMESTAMP_TIMEZONE == 'local':
                airdatetime = airdatetime.astimezone(network_timezones.sb_timezone)

            filemtime = datetime.datetime.fromtimestamp(ek(os.path.getmtime, self.location)).replace(tzinfo=network_timezones.sb_timezone)

            if filemtime != airdatetime:
                import time

                airdatetime = airdatetime.timetuple()
                logger.log("{0}: About to modify date of '{1}' to show air date {2}".format
                           (self.show.indexerid, self.location, time.strftime("%b %d,%Y (%H:%M)", airdatetime)), logger.DEBUG)
                try:
                    if helpers.touchFile(self.location, time.mktime(airdatetime)):
                        logger.log("{0}: Changed modify date of '{1}' to show air date {2}".format
                                   (self.show.indexerid, ek(os.path.basename, self.location), time.strftime("%b %d,%Y (%H:%M)", airdatetime)))
                    else:
                        logger.log("{0}: Unable to modify date of '{1}' to show air date {2}".format
                                   (self.show.indexerid, ek(os.path.basename, self.location), time.strftime("%b %d,%Y (%H:%M)", airdatetime)), logger.WARNING)
                except Exception:
                    logger.log("{0}: Failed to modify date of '{1}' to show air date {2}".format
                               (self.show.indexerid, ek(os.path.basename, self.location), time.strftime("%b %d,%Y (%H:%M)", airdatetime)), logger.WARNING)
        except Exception:
            logger.log("{0}: Failed to modify date of '{1}'".format
                       (self.show.indexerid, ek(os.path.basename, self.location)), logger.WARNING)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d[b'lock']
        return d

    def __setstate__(self, d):
        d[b'lock'] = threading.Lock()
        self.__dict__.update(d)
