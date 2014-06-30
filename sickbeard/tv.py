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

import os.path
import datetime
import threading
import re
import glob
import traceback

import sickbeard

import xml.etree.cElementTree as etree

from name_parser.parser import NameParser, InvalidNameException

from lib import subliminal

from lib.imdb import imdb

from sickbeard import db
from sickbeard import helpers, exceptions, logger
from sickbeard.exceptions import ex
from sickbeard import image_cache
from sickbeard import notifiers
from sickbeard import postProcessor
from sickbeard import subtitles
from sickbeard import history

from sickbeard import encodingKludge as ek

from common import Quality, Overview, statusStrings
from common import DOWNLOADED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, ARCHIVED, IGNORED, UNAIRED, WANTED, SKIPPED, \
    UNKNOWN, FAILED
from common import NAMING_DUPLICATE, NAMING_EXTEND, NAMING_LIMITED_EXTEND, NAMING_SEPARATED_REPEAT, \
    NAMING_LIMITED_EXTEND_E_PREFIXED


def dirty_setter(attr_name):
    def wrapper(self, val):
        if getattr(self, attr_name) != val:
            setattr(self, attr_name, val)
            self.dirty = True

    return wrapper

class TVShow(object):
    def __init__(self, indexer, indexerid, lang=""):
        self._indexerid = int(indexerid)
        self._indexer = int(indexer)
        self._name = ""
        self._location = ""
        self._imdbid = ""
        self._network = ""
        self._genre = ""
        self._classification = ""
        self._runtime = 0
        self._imdb_info = {}
        self._quality = int(sickbeard.QUALITY_DEFAULT)
        self._flatten_folders = int(sickbeard.FLATTEN_FOLDERS_DEFAULT)
        self._status = ""
        self._airs = ""
        self._startyear = 0
        self._paused = 0
        self._air_by_date = 0
        self._subtitles = int(sickbeard.SUBTITLES_DEFAULT if sickbeard.SUBTITLES_DEFAULT else 0)
        self._dvdorder = 0
        self._archive_firstmatch = 0
        self._lang = lang
        self._last_update_indexer = 1
        self._sports = 0
        self._anime = 0
        self._scene = 0
        self._rls_ignore_words = ""
        self._rls_require_words = ""

        self.dirty = True

        self.lock = threading.Lock()
        self.isDirGood = False
        self.episodes = {}

        otherShow = helpers.findCertainShow(sickbeard.showList, self.indexerid)
        if otherShow != None:
            raise exceptions.MultipleShowObjectsException("Can't create a show if it already exists")

        self.loadFromDB()

    def __del__(self):
        pass

    name = property(lambda self: self._name, dirty_setter("_name"))
    indexerid = property(lambda self: self._indexerid, dirty_setter("_indexerid"))
    indexer = property(lambda self: self._indexer, dirty_setter("_indexer"))
    #location = property(lambda self: self._location, dirty_setter("_location"))
    imdbid = property(lambda self: self._imdbid, dirty_setter("_imdbid"))
    network = property(lambda self: self._network, dirty_setter("_network"))
    genre = property(lambda self: self._genre, dirty_setter("_genre"))
    classification = property(lambda self: self._classification, dirty_setter("_classification"))
    runtime = property(lambda self: self._runtime, dirty_setter("_runtime"))
    imdb_info = property(lambda self: self._imdb_info, dirty_setter("_imdb_info"))
    quality = property(lambda self: self._quality, dirty_setter("_quality"))
    flatten_folders = property(lambda self: self._flatten_folders, dirty_setter("_flatten_folders"))
    status = property(lambda self: self._status, dirty_setter("_status"))
    airs = property(lambda self: self._airs, dirty_setter("_airs"))
    startyear = property(lambda self: self._startyear, dirty_setter("_startyear"))
    paused = property(lambda self: self._paused, dirty_setter("_paused"))
    air_by_date = property(lambda self: self._air_by_date, dirty_setter("_air_by_date"))
    subtitles = property(lambda self: self._subtitles, dirty_setter("_subtitles"))
    dvdorder = property(lambda self: self._dvdorder, dirty_setter("_dvdorder"))
    archive_firstmatch = property(lambda self: self._archive_firstmatch, dirty_setter("_archive_firstmatch"))
    lang = property(lambda self: self._lang, dirty_setter("_lang"))
    last_update_indexer = property(lambda self: self._last_update_indexer, dirty_setter("_last_update_indexer"))
    sports = property(lambda self: self._sports, dirty_setter("_sports"))
    anime = property(lambda self: self._anime, dirty_setter("_anime"))
    scene = property(lambda self: self._scene, dirty_setter("_scene"))
    rls_ignore_words = property(lambda self: self._rls_ignore_words, dirty_setter("_rls_ignore_words"))
    rls_require_words = property(lambda self: self._rls_require_words, dirty_setter("_rls_require_words"))
    
    def _is_anime(self):
        if (self.anime > 0):
            return True
        else:
            return False

    is_anime = property(_is_anime)

    def _is_sports(self):
        if (self.sports > 0):
            return True
        else:
            return False

    is_sports = property(_is_sports)

    def _is_scene(self):
        if (self.scene > 0):
            return True
        else:
            return False

    is_scene = property(_is_scene)

    def _getLocation(self):
        # no dir check needed if missing show dirs are created during post-processing
        if sickbeard.CREATE_MISSING_SHOW_DIRS:
            return self._location

        if ek.ek(os.path.isdir, self._location):
            return self._location
        else:
            raise exceptions.ShowDirNotFoundException("Show folder doesn't exist, you shouldn't be using it")

    def _setLocation(self, newLocation):
        logger.log(u"Setter sets location to " + newLocation, logger.DEBUG)
        # Don't validate dir if user wants to add shows without creating a dir
        if sickbeard.ADD_SHOWS_WO_DIR or ek.ek(os.path.isdir, newLocation):
            self._location = newLocation
            self._isDirGood = True
        else:
            raise exceptions.NoNFOException("Invalid folder for the show!")
    location = property(_getLocation, _setLocation)

    # delete references to anything that's not in the internal lists
    def flushEpisodes(self):

        for curSeason in self.episodes:
            for curEp in self.episodes[curSeason]:
                myEp = self.episodes[curSeason][curEp]
                self.episodes[curSeason][curEp] = None
                del myEp

    def getAllEpisodes(self, season=None, has_location=False):

        sql_selection = "SELECT season, episode, "

        # subselection to detect multi-episodes early, share_location > 0
        sql_selection = sql_selection + " (SELECT COUNT (*) FROM tv_episodes WHERE showid = tve.showid AND season = tve.season AND location != '' AND location = tve.location AND episode != tve.episode) AS share_location "

        sql_selection = sql_selection + " FROM tv_episodes tve WHERE showid = " + str(self.indexerid)

        if season is not None:
            sql_selection = sql_selection + " AND season = " + str(season)

        if has_location:
            sql_selection = sql_selection + " AND location != '' "

        # need ORDER episode ASC to rename multi-episodes in order S01E01-02
        sql_selection = sql_selection + " ORDER BY season ASC, episode ASC"

        myDB = db.DBConnection()
        results = myDB.select(sql_selection)

        ep_list = []
        for cur_result in results:
            cur_ep = self.getEpisode(int(cur_result["season"]), int(cur_result["episode"]))
            if cur_ep:
                cur_ep.relatedEps = []
                if cur_ep.location:
                    # if there is a location, check if it's a multi-episode (share_location > 0) and put them in relatedEps
                    if cur_result["share_location"] > 0:
                        related_eps_result = myDB.select(
                            "SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND location = ? AND episode != ? ORDER BY episode ASC",
                            [self.indexerid, cur_ep.season, cur_ep.location, cur_ep.episode])
                        for cur_related_ep in related_eps_result:
                            related_ep = self.getEpisode(int(cur_related_ep["season"]), int(cur_related_ep["episode"]))
                            if related_ep not in cur_ep.relatedEps:
                                cur_ep.relatedEps.append(related_ep)
                ep_list.append(cur_ep)

        return ep_list


    def getEpisode(self, season=None, episode=None, file=None, noCreate=False, absolute_number=None, forceUpdate=False):

        # Load XEM data to DB for show
        sickbeard.scene_numbering.xem_refresh(self.indexerid, self.indexer, force=forceUpdate)

        ep = None

        # if we get an anime get the real season and episode
        if self.is_anime and absolute_number and not season and not episode:
            myDB = db.DBConnection()
            sql = "SELECT * FROM tv_episodes WHERE showid = ? and absolute_number = ? and season != 0"
            sqlResults = myDB.select(sql, [self.indexerid, absolute_number])

            if len(sqlResults) == 1:
                episode = int(sqlResults[0]["episode"])
                season = int(sqlResults[0]["season"])
                logger.log(
                    "Found episode by absolute_number:" + str(absolute_number) + " which is " + str(season) + "x" + str(
                        episode), logger.DEBUG)
            elif len(sqlResults) > 1:
                logger.log("Multiple entries for absolute number: " + str(
                    absolute_number) + " in show: " + self.name + " found ", logger.ERROR)
                return None
            else:
                logger.log(
                    "No entries for absolute number: " + str(absolute_number) + " in show: " + self.name + " found.",
                    logger.DEBUG)
                return None

        if not season in self.episodes:
            self.episodes[season] = {}

        if not episode in self.episodes[season] or self.episodes[season][episode] is None:
            if noCreate:
                return None

            logger.log(str(self.indexerid) + u": An object for episode " + str(season) + "x" + str(
                episode) + " didn't exist in the cache, trying to create it", logger.DEBUG)

            if file:
                ep = TVEpisode(self, season, episode, file)
            else:
                ep = TVEpisode(self, season, episode)

            # get scene absolute numbering
            ep.scene_absolute_number = sickbeard.scene_numbering.get_scene_absolute_numbering(self.indexerid,
                                                                                              self.indexer,
                                                                                              ep.absolute_number)

            # get scene season and episode numbering
            ep.scene_season, ep.scene_episode = sickbeard.scene_numbering.get_scene_numbering(self.indexerid,
                                                                                              self.indexer,
                                                                                              season, episode)

            if ep != None:
                self.episodes[season][episode] = ep

        epObj = self.episodes[season][episode]
        return epObj

    def should_update(self, update_date=datetime.date.today()):

        # if show is not 'Ended' always update (status 'Continuing' or '')
        if 'Ended' not in self.status:
            return True

        # run logic against the current show latest aired and next unaired data to see if we should bypass 'Ended' status
        cur_indexerid = self.indexerid

        graceperiod = datetime.timedelta(days=30)

        last_airdate = datetime.date.fromordinal(1)

        # get latest aired episode to compare against today - graceperiod and today + graceperiod
        myDB = db.DBConnection()
        sql_result = myDB.select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season > '0' AND airdate > '1' AND status > '1' ORDER BY airdate DESC LIMIT 1",
            [cur_indexerid])

        if sql_result:
            last_airdate = datetime.date.fromordinal(sql_result[0]['airdate'])
            if last_airdate >= (update_date - graceperiod) and last_airdate <= (update_date + graceperiod):
                return True

        # get next upcoming UNAIRED episode to compare against today + graceperiod
        sql_result = myDB.select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season > '0' AND airdate > '1' AND status = '1' ORDER BY airdate ASC LIMIT 1",
            [cur_indexerid])

        if sql_result:
            next_airdate = datetime.date.fromordinal(sql_result[0]['airdate'])
            if next_airdate <= (update_date + graceperiod):
                return True

        last_update_indexer = datetime.date.fromordinal(self.last_update_indexer)

        # in the first year after ended (last airdate), update every 30 days
        if (update_date - last_airdate) < datetime.timedelta(days=450) and (
                    update_date - last_update_indexer) > datetime.timedelta(days=30):
            return True

        return False

    def writeShowNFO(self):

        result = False

        if not ek.ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return False

        logger.log(str(self.indexerid) + u": Writing NFOs for show")
        for cur_provider in sickbeard.metadata_provider_dict.values():
            result = cur_provider.create_show_metadata(self) or result

        return result

    def writeMetadata(self, show_only=False):

        if not ek.ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return

        self.getImages()

        self.writeShowNFO()

        if not show_only:
            self.writeEpisodeNFOs()

    def writeEpisodeNFOs(self):

        if not ek.ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return

        logger.log(str(self.indexerid) + u": Writing NFOs for all episodes")

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        for epResult in sqlResults:
            logger.log(str(self.indexerid) + u": Retrieving/creating episode " + str(epResult["season"]) + "x" + str(
                epResult["episode"]), logger.DEBUG)
            curEp = self.getEpisode(epResult["season"], epResult["episode"])
            curEp.createMetaFiles()


    def updateMetadata(self):

        if not ek.ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return

        self.updateShowNFO()

    def updateShowNFO(self):

        result = False

        if not ek.ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return False

        logger.log(str(self.indexerid) + u": Updating NFOs for show with new indexer info")
        for cur_provider in sickbeard.metadata_provider_dict.values():
            result = cur_provider.update_show_indexer_metadata(self) or result

        return result

    # find all media files in the show folder and create episodes for as many as possible
    def loadEpisodesFromDir(self):

        if not ek.ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, not loading episodes from disk")
            return

        logger.log(str(self.indexerid) + u": Loading all episodes from the show directory " + self._location)

        # get file list
        mediaFiles = helpers.listMediaFiles(self._location)

        # create TVEpisodes from each media file (if possible)
        sql_l = []
        for mediaFile in mediaFiles:
            parse_result = None
            curEpisode = None

            logger.log(str(self.indexerid) + u": Creating episode from " + mediaFile, logger.DEBUG)
            try:
                curEpisode = self.makeEpFromFile(ek.ek(os.path.join, self._location, mediaFile))
            except (exceptions.ShowNotFoundException, exceptions.EpisodeNotFoundException), e:
                logger.log(u"Episode " + mediaFile + " returned an exception: " + ex(e), logger.ERROR)
                continue
            except exceptions.EpisodeDeletedException:
                logger.log(u"The episode deleted itself when I tried making an object for it", logger.DEBUG)

            if curEpisode is None:
                continue

            # see if we should save the release name in the db
            ep_file_name = ek.ek(os.path.basename, curEpisode.location)
            ep_file_name = ek.ek(os.path.splitext, ep_file_name)[0]

            try:
                parse_result = None
                np = NameParser(False)
                parse_result = np.parse(ep_file_name)
            except InvalidNameException:
                pass

            if not ' ' in ep_file_name and parse_result and parse_result.release_group:
                logger.log(
                    u"Name " + ep_file_name + u" gave release group of " + parse_result.release_group + ", seems valid",
                    logger.DEBUG)
                curEpisode.release_name = ep_file_name

            # store the reference in the show
            if curEpisode != None:
                if self.subtitles:
                    try:
                        curEpisode.refreshSubtitles()
                    except:
                        logger.log(str(self.indexerid) + ": Could not refresh subtitles", logger.ERROR)
                        logger.log(traceback.format_exc(), logger.DEBUG)

                sql_l.append(curEpisode.get_sql())

        if sql_l:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)


    def loadEpisodesFromDB(self):

        logger.log(u"Loading all episodes from the DB")

        myDB = db.DBConnection()
        sql = "SELECT * FROM tv_episodes WHERE showid = ?"
        sqlResults = myDB.select(sql, [self.indexerid])

        scannedEps = {}

        lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

        if self.lang:
            lINDEXER_API_PARMS['language'] = self.lang

        if self.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

        cachedShow = t[self.indexerid]
        cachedSeasons = {}

        for curResult in sqlResults:

            deleteEp = False

            curSeason = int(curResult["season"])
            curEpisode = int(curResult["episode"])

            if curSeason not in cachedSeasons:
                try:
                    cachedSeasons[curSeason] = cachedShow[curSeason]
                except sickbeard.indexer_seasonnotfound, e:
                    logger.log(u"Error when trying to load the episode from " + sickbeard.indexerApi(
                        self.indexer).name + ": " + e.message, logger.WARNING)
                    deleteEp = True

            if not curSeason in scannedEps:
                scannedEps[curSeason] = {}

            logger.log(u"Loading episode " + str(curSeason) + "x" + str(curEpisode) + " from the DB", logger.DEBUG)

            try:
                curEp = self.getEpisode(curSeason, curEpisode)

                # if we found out that the ep is no longer on TVDB then delete it from our database too
                if deleteEp:
                    curEp.deleteEpisode()

                curEp.loadFromDB(curSeason, curEpisode)
                curEp.loadFromIndexer(tvapi=t, cachedSeason=cachedSeasons[curSeason])
                scannedEps[curSeason][curEpisode] = True
            except exceptions.EpisodeDeletedException:
                logger.log(u"Tried loading an episode from the DB that should have been deleted, skipping it",
                           logger.DEBUG)
                continue

        return scannedEps

    def loadEpisodesFromIndexer(self, cache=True):

        lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

        if not cache:
            lINDEXER_API_PARMS['cache'] = False

        if self.lang:
            lINDEXER_API_PARMS['language'] = self.lang

        if self.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        try:
            t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
            showObj = t[self.indexerid]
        except sickbeard.indexer_error:
            logger.log(u"" + sickbeard.indexerApi(
                self.indexer).name + " timed out, unable to update episodes from " + sickbeard.indexerApi(
                self.indexer).name, logger.ERROR)
            return None

        logger.log(
            str(self.indexerid) + u": Loading all episodes from " + sickbeard.indexerApi(self.indexer).name + "..")

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
                except exceptions.EpisodeNotFoundException:
                    logger.log(
                        str(self.indexerid) + ": " + sickbeard.indexerApi(self.indexer).name + " object for " + str(
                            season) + "x" + str(episode) + " is incomplete, skipping this episode")
                    continue
                else:
                    try:
                        ep.loadFromIndexer(tvapi=t)
                    except exceptions.EpisodeDeletedException:
                        logger.log(u"The episode was deleted, skipping the rest of the load")
                        continue

                with ep.lock:
                    logger.log(str(self.indexerid) + u": Loading info from " + sickbeard.indexerApi(
                        self.indexer).name + " for episode " + str(season) + "x" + str(episode), logger.DEBUG)
                    ep.loadFromIndexer(season, episode, tvapi=t)

                    sql_l.append(ep.get_sql())

                scannedEps[season][episode] = True

        if sql_l:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)


        # Done updating save last update date
        self.last_update_indexer = datetime.date.today().toordinal()
        self.saveToDB()

        return scannedEps

    def getImages(self, fanart=None, poster=None):
        fanart_result = poster_result = banner_result = False
        season_posters_result = season_banners_result = season_all_poster_result = season_all_banner_result = False

        for cur_provider in sickbeard.metadata_provider_dict.values():
            # FIXME: Needs to not show this message if the option is not enabled?
            logger.log(u"Running metadata routines for " + cur_provider.name, logger.DEBUG)

            fanart_result = cur_provider.create_fanart(self) or fanart_result
            poster_result = cur_provider.create_poster(self) or poster_result
            banner_result = cur_provider.create_banner(self) or banner_result

            season_posters_result = cur_provider.create_season_posters(self) or season_posters_result
            season_banners_result = cur_provider.create_season_banners(self) or season_banners_result
            season_all_poster_result = cur_provider.create_season_all_poster(self) or season_all_poster_result
            season_all_banner_result = cur_provider.create_season_all_banner(self) or season_all_banner_result

        return fanart_result or poster_result or banner_result or season_posters_result or season_banners_result or season_all_poster_result or season_all_banner_result

    # make a TVEpisode object from a media file
    def makeEpFromFile(self, file):

        if not ek.ek(os.path.isfile, file):
            logger.log(str(self.indexerid) + u": That isn't even a real file dude... " + file)
            return None

        logger.log(str(self.indexerid) + u": Creating episode object from " + file, logger.DEBUG)

        try:
            myParser = NameParser(showObj=self, useIndexers=True)
            parse_result = myParser.parse(file)
        except InvalidNameException:
            logger.log(u"Unable to parse the filename " + file + " into a valid episode", logger.ERROR)
            return None

        if not len(parse_result.episode_numbers) and not (parse_result.air_by_date or parse_result.sports):
            logger.log("parse_result: " + str(parse_result))
            logger.log(u"No episode number found in " + file + ", ignoring it", logger.ERROR)
            return None

        # for now lets assume that any episode in the show dir belongs to that show
        season = parse_result.season_number if parse_result.season_number != None else 1
        episodes = parse_result.episode_numbers
        rootEp = None

        # if we have an air-by-date show then get the real season/episode numbers
        if parse_result.air_by_date or parse_result.sports:
            logger.log(
                u"Looks like this is an air-by-date or sports show, attempting to convert the date to season/episode",
                logger.DEBUG)
            airdate = parse_result.air_date.toordinal() if parse_result.air_date else parse_result.sports_event_date.toordinal()
            myDB = db.DBConnection()
            sql_result = myDB.select(
                "SELECT season, episode FROM tv_episodes WHERE showid = ? and indexer = ? and airdate = ?",
                [self.indexerid, self.indexer, airdate])

            if sql_result:
                season = int(sql_result[0][0])
                episodes = [int(sql_result[0][1])]
            else:
                logger.log(u"Unable to find episode with date " + str(
                    parse_result.air_date) + " for show " + self.name + ", skipping", logger.WARNING)
                return None

        sql_l = []
        for curEpNum in episodes:

            episode = int(curEpNum)

            logger.log(
                str(self.indexerid) + ": " + file + " parsed to " + self.name + " " + str(season) + "x" + str(episode),
                logger.DEBUG)

            checkQualityAgain = False
            same_file = False
            curEp = self.getEpisode(season, episode)

            if curEp == None:
                try:
                    curEp = self.getEpisode(season, episode, file)
                except exceptions.EpisodeNotFoundException:
                    logger.log(str(self.indexerid) + u": Unable to figure out what this file is, skipping",
                               logger.ERROR)
                    continue

            else:
                # if there is a new file associated with this ep then re-check the quality
                if curEp.location and ek.ek(os.path.normpath, curEp.location) != ek.ek(os.path.normpath, file):
                    logger.log(
                        u"The old episode had a different file associated with it, I will re-check the quality based on the new filename " + file,
                        logger.DEBUG)
                    checkQualityAgain = True

                with curEp.lock:
                    old_size = curEp.file_size
                    curEp.location = file
                    # if the sizes are the same then it's probably the same file
                    if old_size and curEp.file_size == old_size:
                        same_file = True
                    else:
                        same_file = False

                    curEp.checkForMetaFiles()

            if rootEp == None:
                rootEp = curEp
            else:
                if curEp not in rootEp.relatedEps:
                    rootEp.relatedEps.append(curEp)

            # if it's a new file then
            if not same_file:
                curEp.release_name = ''

            # if they replace a file on me I'll make some attempt at re-checking the quality unless I know it's the same file
            if checkQualityAgain and not same_file:
                newQuality = Quality.nameQuality(file, self.is_anime)
                logger.log(u"Since this file has been renamed, I checked " + file + " and found quality " +
                           Quality.qualityStrings[newQuality], logger.DEBUG)
                if newQuality != Quality.UNKNOWN:
                    curEp.status = Quality.compositeStatus(DOWNLOADED, newQuality)


            # check for status/quality changes as long as it's a new file
            elif not same_file and sickbeard.helpers.isMediaFile(file) and curEp.status not in Quality.DOWNLOADED + [
                ARCHIVED, IGNORED]:

                oldStatus, oldQuality = Quality.splitCompositeStatus(curEp.status)
                newQuality = Quality.nameQuality(file, self.is_anime)
                if newQuality == Quality.UNKNOWN:
                    newQuality = Quality.assumeQuality(file)

                newStatus = None

                # if it was snatched and now exists then set the status correctly
                if oldStatus == SNATCHED and oldQuality <= newQuality:
                    logger.log(u"STATUS: this ep used to be snatched with quality " + Quality.qualityStrings[
                        oldQuality] + u" but a file exists with quality " + Quality.qualityStrings[
                                   newQuality] + u" so I'm setting the status to DOWNLOADED", logger.DEBUG)
                    newStatus = DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif oldStatus == SNATCHED_PROPER and oldQuality < newQuality:
                    logger.log(u"STATUS: this ep used to be snatched proper with quality " + Quality.qualityStrings[
                        oldQuality] + u" but a file exists with quality " + Quality.qualityStrings[
                                   newQuality] + u" so I'm setting the status to DOWNLOADED", logger.DEBUG)
                    newStatus = DOWNLOADED

                elif oldStatus not in (SNATCHED, SNATCHED_PROPER):
                    newStatus = DOWNLOADED

                if newStatus != None:
                    with curEp.lock:
                        logger.log(u"STATUS: we have an associated file, so setting the status from " + str(
                            curEp.status) + u" to DOWNLOADED/" + str(Quality.statusFromName(file)), logger.DEBUG)
                        curEp.status = Quality.compositeStatus(newStatus, newQuality)

            with curEp.lock:
                sql_l.append(curEp.get_sql())

        if sql_l:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)


        # creating metafiles on the root should be good enough
        if sickbeard.USE_FAILED_DOWNLOADS and rootEp is not None:
            with rootEp.lock:
                rootEp.createMetaFiles()

        return rootEp

    def loadFromDB(self, skipNFO=False):

        logger.log(str(self.indexerid) + u": Loading show info from database")

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_shows WHERE indexer_id = ?", [self.indexerid])

        if len(sqlResults) > 1:
            raise exceptions.MultipleDBShowsException()
        elif len(sqlResults) == 0:
            logger.log(str(self.indexerid) + ": Unable to find the show in the database")
            return
        else:
            if not self.indexer:
                self.indexer = int(sqlResults[0]["indexer"])
            if not self.name:
                self.name = sqlResults[0]["show_name"]
            if not self.network:
                self.network = sqlResults[0]["network"]
            if not self.genre:
                self.genre = sqlResults[0]["genre"]
            if self.classification is None:
                self.classification = sqlResults[0]["classification"]

            self.runtime = sqlResults[0]["runtime"]

            self.status = sqlResults[0]["status"]
            if not self.status:
                self.status = ""
            self.airs = sqlResults[0]["airs"]
            if not self.airs:
                self.airs = ""
            self.startyear = sqlResults[0]["startyear"]
            if not self.startyear:
                self.startyear = 0

            self.air_by_date = sqlResults[0]["air_by_date"]
            if not self.air_by_date:
                self.air_by_date = 0

            self.anime = sqlResults[0]["anime"]
            if self.anime == None:
                self.anime = 0

            self.sports = sqlResults[0]["sports"]
            if not self.sports:
                self.sports = 0

            self.scene = sqlResults[0]["scene"]
            if not self.scene:
                self.scene = 0

            self.subtitles = sqlResults[0]["subtitles"]
            if self.subtitles:
                self.subtitles = 1
            else:
                self.subtitles = 0

            self.dvdorder = sqlResults[0]["dvdorder"]
            if not self.dvdorder:
                self.dvdorder = 0

            self.archive_firstmatch = sqlResults[0]["archive_firstmatch"]
            if not self.archive_firstmatch:
                self.archive_firstmatch = 0

            self.quality = int(sqlResults[0]["quality"])
            self.flatten_folders = int(sqlResults[0]["flatten_folders"])
            self.paused = int(sqlResults[0]["paused"])

            self._location = sqlResults[0]["location"]

            if not self.lang:
                self.lang = sqlResults[0]["lang"]

            self.last_update_indexer = sqlResults[0]["last_update_indexer"]

            self.rls_ignore_words = sqlResults[0]["rls_ignore_words"]
            self.rls_require_words = sqlResults[0]["rls_require_words"]

            if not self.imdbid:
                self.imdbid = sqlResults[0]["imdb_id"]

        # Get IMDb_info from database
        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM imdb_info WHERE indexer_id = ?", [self.indexerid])

        if len(sqlResults) == 0:
            logger.log(str(self.indexerid) + ": Unable to find IMDb show info in the database")
            return
        else:
            self.imdb_info = dict(zip(sqlResults[0].keys(), sqlResults[0]))

        self.dirty = False
        return True

    def loadFromIndexer(self, cache=True, tvapi=None, cachedSeason=None):

        logger.log(str(self.indexerid) + u": Loading show info from " + sickbeard.indexerApi(self.indexer).name)

        # There's gotta be a better way of doing this but we don't wanna
        # change the cache value elsewhere
        if tvapi is None:
            lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

            if not cache:
                lINDEXER_API_PARMS['cache'] = False

            if self.lang:
                lINDEXER_API_PARMS['language'] = self.lang

            if self.dvdorder != 0:
                lINDEXER_API_PARMS['dvdorder'] = True

            t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

        else:
            t = tvapi

        myEp = t[self.indexerid]

        try:
            self.name = myEp['seriesname'].strip()
        except AttributeError:
            raise sickbeard.indexer_attributenotfound(
                "Found %s, but attribute 'seriesname' was empty." % (self.indexerid))

        self.classification = getattr(myEp, 'classification', 'Scripted')
        self.genre = getattr(myEp, 'genre', '')
        self.network = getattr(myEp, 'network', '')
        self.runtime = getattr(myEp, 'runtime', '')

        self.imdbid = getattr(myEp, 'imdb_id', '')

        if getattr(myEp, 'airs_dayofweek', None) is not None and getattr(myEp, 'airs_time', None) is not None:
            self.airs = myEp["airs_dayofweek"] + " " + myEp["airs_time"]

        if getattr(myEp, 'firstaired', None) is not None:
            self.startyear = int(str(myEp["firstaired"]).split('-')[0])

        self.status = getattr(myEp, 'status', '')

    def loadIMDbInfo(self, imdbapi=None):

        imdb_info = {'imdb_id': self.imdbid,
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

        if self.imdbid:
            logger.log(str(self.indexerid) + u": Loading show info from IMDb")

            i = imdb.IMDb()
            imdbTv = i.get_movie(str(re.sub("[^0-9]", "", self.imdbid)))

            for key in filter(lambda x: x.replace('_', ' ') in imdbTv.keys(), imdb_info.keys()):
                # Store only the first value for string type
                if type(imdb_info[key]) == type('') and type(imdbTv.get(key)) == type([]):
                    imdb_info[key] = imdbTv.get(key.replace('_', ' '))[0]
                else:
                    imdb_info[key] = imdbTv.get(key.replace('_', ' '))

            # Filter only the value
            if imdb_info['runtimes']:
                imdb_info['runtimes'] = re.search('\d+', imdb_info['runtimes']).group(0)
            else:
                imdb_info['runtimes'] = self.runtime

            if imdb_info['akas']:
                imdb_info['akas'] = '|'.join(imdb_info['akas'])
            else:
                imdb_info['akas'] = ''

            # Join all genres in a string
            if imdb_info['genres']:
                imdb_info['genres'] = '|'.join(imdb_info['genres'])
            else:
                imdb_info['genres'] = ''

            # Get only the production country certificate if any
            if imdb_info['certificates'] and imdb_info['countries']:
                dct = {}
                try:
                    for item in imdb_info['certificates']:
                        dct[item.split(':')[0]] = item.split(':')[1]

                    imdb_info['certificates'] = dct[imdb_info['countries']]
                except:
                    imdb_info['certificates'] = ''

            else:
                imdb_info['certificates'] = ''

            if imdb_info['country_codes']:
                imdb_info['country_codes'] = '|'.join(imdb_info['country_codes'])
            else:
                imdb_info['country_codes'] = ''

            imdb_info['last_update'] = datetime.date.today().toordinal()

            # Rename dict keys without spaces for DB upsert
            self.imdb_info = dict(
                (k.replace(' ', '_'), k(v) if hasattr(v, 'keys') else v) for k, v in imdb_info.items())
            logger.log(str(self.indexerid) + u": Obtained info from IMDb ->" + str(self.imdb_info), logger.DEBUG)

    def nextEpisode(self):
        logger.log(str(self.indexerid) + ": Finding the episode which airs next", logger.DEBUG)

        myDB = db.DBConnection()
        innerQuery = "SELECT airdate FROM tv_episodes WHERE showid = ? AND airdate >= ? AND status in (?,?) ORDER BY airdate ASC LIMIT 1"
        innerParams = [self.indexerid, datetime.date.today().toordinal(), UNAIRED, WANTED]
        query = "SELECT * FROM tv_episodes WHERE showid = ? AND airdate >= ? AND airdate <= (" + innerQuery + ") and status in (?,?)"
        params = [self.indexerid, datetime.date.today().toordinal()] + innerParams + [UNAIRED, WANTED]
        sqlResults = myDB.select(query, params)

        if sqlResults == None or len(sqlResults) == 0:
            logger.log(str(self.indexerid) + u": No episode found... need to implement a show status",
                       logger.DEBUG)
            return []
        else:
            logger.log(str(self.indexerid) + u": Found episode " + str(sqlResults[0]["season"]) + "x" + str(
                sqlResults[0]["episode"]), logger.DEBUG)
            foundEps = []
            for sqlEp in sqlResults:
                curEp = self.getEpisode(int(sqlEp["season"]), int(sqlEp["episode"]))
                foundEps.append(curEp)
            return foundEps

    def deleteShow(self):

        sql_l = [["DELETE FROM tv_episodes WHERE showid = ?", [self.indexerid]],
                 ["DELETE FROM tv_shows WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM imdb_info WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM xem_refresh WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM scene_numbering WHERE indexer_id = ?", [self.indexerid]]]

        myDB = db.DBConnection()
        myDB.mass_action(sql_l)


        # remove self from show list
        sickbeard.showList = [x for x in sickbeard.showList if int(x.indexerid) != self.indexerid]

        # clear the cache
        image_cache_dir = ek.ek(os.path.join, sickbeard.CACHE_DIR, 'images')
        for cache_file in ek.ek(glob.glob, ek.ek(os.path.join, image_cache_dir, str(self.indexerid) + '.*')):
            logger.log(u"Deleting cache file " + cache_file)
            os.remove(cache_file)

    def populateCache(self):
        cache_inst = image_cache.ImageCache()

        logger.log(u"Checking & filling cache for show " + self.name)
        cache_inst.fill_cache(self)

    def refreshDir(self):

        # make sure the show dir is where we think it is unless dirs are created on the fly
        if not ek.ek(os.path.isdir, self._location) and not sickbeard.CREATE_MISSING_SHOW_DIRS:
            return False

        # load from dir
        self.loadEpisodesFromDir()

        # run through all locations from DB, check that they exist
        logger.log(str(self.indexerid) + u": Loading all episodes with a location from the database")

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        sql_l = []
        for ep in sqlResults:
            curLoc = os.path.normpath(ep["location"])
            season = int(ep["season"])
            episode = int(ep["episode"])

            try:
                curEp = self.getEpisode(season, episode)
            except exceptions.EpisodeDeletedException:
                logger.log(u"The episode was deleted while we were refreshing it, moving on to the next one",
                           logger.DEBUG)
                continue

            # if the path doesn't exist or if it's not in our show dir
            if not ek.ek(os.path.isfile, curLoc) or not os.path.normpath(curLoc).startswith(
                    os.path.normpath(self.location)):

                # check if downloaded files still exist, update our data if this has changed
                if not sickbeard.SKIP_REMOVED_FILES:
                    with curEp.lock:
                        # if it used to have a file associated with it and it doesn't anymore then set it to IGNORED
                        if curEp.location and curEp.status in Quality.DOWNLOADED:
                            logger.log(str(self.indexerid) + u": Location for " + str(season) + "x" + str(
                                episode) + " doesn't exist, removing it and changing our status to IGNORED",
                                       logger.DEBUG)
                            curEp.status = IGNORED
                            curEp.subtitles = list()
                            curEp.subtitles_searchcount = 0
                            curEp.subtitles_lastsearch = str(datetime.datetime.min)
                        curEp.location = ''
                        curEp.hasnfo = False
                        curEp.hastbn = False
                        curEp.release_name = ''

                        sql_l.append(curEp.get_sql())
            else:
                # the file exists, set its modify file stamp
                if sickbeard.AIRDATE_EPISODES:
                    self.airdateModifyStamp(curEp)

        if sql_l:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)


    def airdateModifyStamp(self, ep_obj):
        """
        Make the modify date and time of a file reflect the show air date and time.
        Note: Also called from postProcessor

        """
        hr = min = 0
        airs = re.search('.*?(\d{1,2})(?::\s*?(\d{2}))?\s*(pm)?', ep_obj.show.airs, re.I)
        if airs:
            hr = int(airs.group(1))
            hr = (12 + hr, hr)[None is airs.group(3)]
            min = int((airs.group(2), min)[None is airs.group(2)])
        airtime = datetime.time(hr, min)

        airdatetime = datetime.datetime.combine(ep_obj.airdate, airtime)

        filemtime = datetime.datetime.fromtimestamp(os.path.getmtime(ep_obj.location))

        if filemtime != airdatetime:
            import time

            airdatetime = airdatetime.timetuple()
            if self.touch(ep_obj.location, time.mktime(airdatetime)):
                logger.log(str(self.indexerid) + u": Changed modify date of " + os.path.basename(ep_obj.location)
                           + " to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))

    def touch(self, fname, atime=None):

        if None != atime:
            try:
                with file(fname, 'a'):
                    os.utime(fname, (atime, atime))
                    return True
            except:
                logger.log(u"File air date stamping not available on your OS", logger.DEBUG)
                pass

        return False

    def downloadSubtitles(self, force=False):
        # TODO: Add support for force option
        if not ek.ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, can't download subtitles", logger.DEBUG)
            return
        logger.log(str(self.indexerid) + ": Downloading subtitles", logger.DEBUG)

        try:
            myDB = db.DBConnection()
            episodes = myDB.select(
                "SELECT location FROM tv_episodes WHERE showid = ? AND location NOT LIKE '' ORDER BY season DESC, episode DESC",
                [self.indexerid])

            for episodeLoc in episodes:
                episode = self.makeEpFromFile(episodeLoc['location'])
                subtitles = episode.downloadSubtitles(force=force)
        except Exception as e:
            logger.log("Error occurred when downloading subtitles: " + traceback.format_exc(), logger.DEBUG)
            return


    def saveToDB(self, forceSave=False):

        if not self.dirty and not forceSave:
            logger.log(str(self.indexerid) + u": Not saving show to db - record is not dirty", logger.DEBUG)
            return

        logger.log(str(self.indexerid) + u": Saving show info to database", logger.DEBUG)

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
                        "flatten_folders": self.flatten_folders,
                        "paused": self.paused,
                        "air_by_date": self.air_by_date,
                        "anime": self.anime,
                        "scene": self.scene,
                        "sports": self.sports,
                        "subtitles": self.subtitles,
                        "dvdorder": self.dvdorder,
                        "archive_firstmatch": self.archive_firstmatch,
                        "startyear": self.startyear,
                        "lang": self.lang,
                        "imdb_id": self.imdbid,
                        "last_update_indexer": self.last_update_indexer,
                        "rls_ignore_words": self.rls_ignore_words,
                        "rls_require_words": self.rls_require_words
        }

        myDB = db.DBConnection()
        myDB.upsert("tv_shows", newValueDict, controlValueDict)

        helpers.update_anime_support()

        if self.imdbid:
            controlValueDict = {"indexer_id": self.indexerid}
            newValueDict = self.imdb_info

            myDB = db.DBConnection()
            myDB.upsert("imdb_info", newValueDict, controlValueDict)

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
        if self.status:
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


    def wantEpisode(self, season, episode, quality, manualSearch=False):

        logger.log(u"Checking if found episode " + str(season) + "x" + str(episode) + " is wanted at quality " +
                   Quality.qualityStrings[quality], logger.DEBUG)

        # if the quality isn't one we want under any circumstances then just say no
        anyQualities, bestQualities = Quality.splitQuality(self.quality)
        logger.log(u"any,best = " + str(anyQualities) + " " + str(bestQualities) + " and found " + str(quality),
                   logger.DEBUG)

        if quality not in anyQualities + bestQualities:
            logger.log(u"Don't want this quality, ignoring found episode", logger.DEBUG)
            return False

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                                 [self.indexerid, season, episode])

        if not sqlResults or not len(sqlResults):
            logger.log(u"Unable to find a matching episode in database, ignoring found episode", logger.DEBUG)
            return False

        epStatus = int(sqlResults[0]["status"])
        epStatus_text = statusStrings[epStatus]

        logger.log(u"Existing episode status: " + str(epStatus) + " (" + epStatus_text + ")", logger.DEBUG)

        # if we know we don't want it then just say no
        if epStatus in (SKIPPED, IGNORED, ARCHIVED) and not manualSearch:
            logger.log(u"Existing episode status is skipped/ignored/archived, ignoring found episode", logger.DEBUG)
            return False

        # if it's one of these then we want it as long as it's in our allowed initial qualities
        if quality in anyQualities + bestQualities:
            if epStatus in (WANTED, UNAIRED, SKIPPED):
                logger.log(u"Existing episode status is wanted/unaired/skipped, getting found episode", logger.DEBUG)
                return True
            elif manualSearch:
                logger.log(
                    u"Usually ignoring found episode, but forced search allows the quality, getting found episode",
                    logger.DEBUG)
                return True
            else:
                logger.log(u"Quality is on wanted list, need to check if it's better than existing quality",
                           logger.DEBUG)

        curStatus, curQuality = Quality.splitCompositeStatus(epStatus)

        # if we are re-downloading then we only want it if it's in our bestQualities list and better than what we have
        if curStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST and quality in bestQualities and quality > curQuality:
            logger.log(u"Episode already exists but the found episode has better quality, getting found episode",
                       logger.DEBUG)
            return True
        else:
            logger.log(u"Episode already exists and the found episode has same/lower quality, ignoring found episode",
                       logger.DEBUG)

        logger.log(u"None of the conditions were met, ignoring found episode", logger.DEBUG)
        return False

    def getOverview(self, epStatus):

        if epStatus == WANTED:
            return Overview.WANTED
        elif epStatus in (UNAIRED, UNKNOWN):
            return Overview.UNAIRED
        elif epStatus in (SKIPPED, IGNORED):
            return Overview.SKIPPED
        elif epStatus == ARCHIVED:
            return Overview.GOOD
        elif epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.FAILED + Quality.SNATCHED_BEST:

            anyQualities, bestQualities = Quality.splitQuality(self.quality)  # @UnusedVariable
            if bestQualities:
                maxBestQuality = max(bestQualities)
            else:
                maxBestQuality = None

            epStatus, curQuality = Quality.splitCompositeStatus(epStatus)

            if epStatus == FAILED:
                return Overview.WANTED
            elif epStatus in (SNATCHED, SNATCHED_PROPER, SNATCHED_BEST):
                return Overview.SNATCHED
            # if they don't want re-downloads then we call it good if they have anything
            elif maxBestQuality == None:
                return Overview.GOOD
            # if they have one but it's not the best they want then mark it as qual
            elif curQuality < maxBestQuality:
                return Overview.QUAL
            # if it's >= maxBestQuality then it's good
            else:
                return Overview.GOOD

class TVEpisode(object):
    def __init__(self, show, season, episode, file=""):
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

        # setting any of the above sets the dirty flag
        self.dirty = True

        self.show = show

        self.scene_season = 0
        self.scene_episode = 0
        self.scene_absolute_number = 0

        self._location = file

        self._indexer = int(self.show.indexer)

        self.lock = threading.Lock()

        self.specifyEpisode(self.season, self.episode)

        self.relatedEps = []

        self.checkForMetaFiles()

    def __del__(self):
        pass

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

    def _set_location(self, new_location):
        logger.log(u"Setter sets location to " + new_location, logger.DEBUG)

        # self._location = newLocation
        dirty_setter("_location")(self, new_location)

        if new_location and ek.ek(os.path.isfile, new_location):
            self.file_size = ek.ek(os.path.getsize, new_location)
        else:
            self.file_size = 0

    location = property(lambda self: self._location, _set_location)

    def refreshSubtitles(self):
        """Look for subtitles files and refresh the subtitles property"""
        self.subtitles = subtitles.subtitlesLanguages(self.location)

    def downloadSubtitles(self, force=False):
        # TODO: Add support for force option
        if not ek.ek(os.path.isfile, self.location):
            logger.log(
                str(self.show.indexerid) + ": Episode file doesn't exist, can't download subtitles for episode " + str(
                    self.season) + "x" + str(self.episode), logger.DEBUG)
            return
        logger.log(str(self.show.indexerid) + ": Downloading subtitles for episode " + str(self.season) + "x" + str(
            self.episode), logger.DEBUG)

        previous_subtitles = self.subtitles

        try:
            need_languages = set(sickbeard.SUBTITLES_LANGUAGES) - set(self.subtitles)
            subtitles = subliminal.download_subtitles([self.location], languages=need_languages,
                                                      services=sickbeard.subtitles.getEnabledServiceList(), force=force,
                                                      multi=True, cache_dir=sickbeard.CACHE_DIR)

            if sickbeard.SUBTITLES_DIR:
                for video in subtitles:
                    subs_new_path = ek.ek(os.path.join, os.path.dirname(video.path), sickbeard.SUBTITLES_DIR)
                    dir_exists = helpers.makeDir(subs_new_path)
                    if not dir_exists:
                        logger.log(u"Unable to create subtitles folder " + subs_new_path, logger.ERROR)
                    else:
                        helpers.chmodAsParent(subs_new_path)

                    for subtitle in subtitles.get(video):
                        new_file_path = ek.ek(os.path.join, subs_new_path, os.path.basename(subtitle.path))
                        helpers.moveFile(subtitle.path, new_file_path)
                        helpers.chmodAsParent(new_file_path)
            else:
                for video in subtitles:
                    for subtitle in subtitles.get(video):
                        helpers.chmodAsParent(subtitle.path)

        except Exception as e:
            logger.log("Error occurred when downloading subtitles: " + traceback.format_exc(), logger.ERROR)
            return

        self.refreshSubtitles()
        self.subtitles_searchcount = self.subtitles_searchcount + 1 if self.subtitles_searchcount else 1  # added the if because sometime it raise an error
        self.subtitles_lastsearch = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.saveToDB()

        newsubtitles = set(self.subtitles).difference(set(previous_subtitles))

        if newsubtitles:
            subtitleList = ", ".join(subliminal.language.Language(x).name for x in newsubtitles)
            logger.log(str(self.show.indexerid) + u": Downloaded " + subtitleList + " subtitles for episode " + str(
                self.season) + "x" + str(self.episode), logger.DEBUG)

            notifiers.notify_subtitle_download(self.prettyName(), subtitleList)

        else:
            logger.log(
                str(self.show.indexerid) + u": No subtitles downloaded for episode " + str(self.season) + "x" + str(
                    self.episode), logger.DEBUG)

        if sickbeard.SUBTITLES_HISTORY:
            for video in subtitles:
                for subtitle in subtitles.get(video):
                    history.logSubtitle(self.show.indexerid, self.season, self.episode, self.status, subtitle)

        return subtitles

    def checkForMetaFiles(self):

        oldhasnfo = self.hasnfo
        oldhastbn = self.hastbn

        cur_nfo = False
        cur_tbn = False

        # check for nfo and tbn
        if ek.ek(os.path.isfile, self.location):
            for cur_provider in sickbeard.metadata_provider_dict.values():
                if cur_provider.episode_metadata:
                    new_result = cur_provider._has_episode_metadata(self)
                else:
                    new_result = False
                cur_nfo = new_result or cur_nfo

                if cur_provider.episode_thumbnails:
                    new_result = cur_provider._has_episode_thumb(self)
                else:
                    new_result = False
                cur_tbn = new_result or cur_tbn

        self.hasnfo = cur_nfo
        self.hastbn = cur_tbn

        # if either setting has changed return true, if not return false
        return oldhasnfo != self.hasnfo or oldhastbn != self.hastbn

    def specifyEpisode(self, season, episode):

        sqlResult = self.loadFromDB(season, episode)

        if not sqlResult:
            # only load from NFO if we didn't load from DB
            if ek.ek(os.path.isfile, self.location):
                try:
                    self.loadFromNFO(self.location)
                except exceptions.NoNFOException:
                    logger.log(str(self.show.indexerid) + u": There was an error loading the NFO for episode " + str(
                        season) + "x" + str(episode), logger.ERROR)
                    pass

                # if we tried loading it from NFO and didn't find the NFO, try the Indexers
                if not self.hasnfo:
                    try:
                        result = self.loadFromIndexer(season, episode)
                    except exceptions.EpisodeDeletedException:
                        result = False

                    # if we failed SQL *and* NFO, Indexers then fail
                    if not result:
                        raise exceptions.EpisodeNotFoundException(
                            "Couldn't find episode " + str(season) + "x" + str(episode))

    def loadFromDB(self, season, episode):
        logger.log(
            str(self.show.indexerid) + u": Loading episode details from DB for episode " + str(season) + "x" + str(
                episode), logger.DEBUG)

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                                 [self.show.indexerid, season, episode])

        if len(sqlResults) > 1:
            raise exceptions.MultipleDBEpisodesException("Your DB has two records for the same show somehow.")
        elif len(sqlResults) == 0:
            logger.log(str(self.show.indexerid) + u": Episode " + str(self.season) + "x" + str(
                self.episode) + " not found in the database", logger.DEBUG)
            return False
        else:
            # NAMEIT logger.log(u"AAAAA from" + str(self.season)+"x"+str(self.episode) + " -" + self.name + " to " + str(sqlResults[0]["name"]))
            if sqlResults[0]["name"]:
                self.name = sqlResults[0]["name"]

            self.season = season
            self.episode = episode
            self.absolute_number = sqlResults[0]["absolute_number"]
            self.description = sqlResults[0]["description"]
            if not self.description:
                self.description = ""
            if sqlResults[0]["subtitles"] and sqlResults[0]["subtitles"]:
                self.subtitles = sqlResults[0]["subtitles"].split(",")
            self.subtitles_searchcount = sqlResults[0]["subtitles_searchcount"]
            self.subtitles_lastsearch = sqlResults[0]["subtitles_lastsearch"]
            self.airdate = datetime.date.fromordinal(int(sqlResults[0]["airdate"]))
            # logger.log(u"1 Status changes from " + str(self.status) + " to " + str(sqlResults[0]["status"]), logger.DEBUG)
            self.status = int(sqlResults[0]["status"])

            # don't overwrite my location
            if sqlResults[0]["location"] and sqlResults[0]["location"]:
                self.location = os.path.normpath(sqlResults[0]["location"])
            if sqlResults[0]["file_size"]:
                self.file_size = int(sqlResults[0]["file_size"])
            else:
                self.file_size = 0

            self.indexerid = int(sqlResults[0]["indexerid"])
            self.indexer = int(sqlResults[0]["indexer"])

            # does one now a better way to test for NULL in the db field ?
            try:
                self.scene_season = int(sqlResults[0]["scene_season"])
            except:
                self.scene_season = 0

            try:
                self.scene_episode = int(sqlResults[0]["scene_episode"])
            except:
                self.scene_episode = 0

            try:
                self.scene_absolute_number = int(sqlResults[0]["scene_absolute_number"])
            except:
                self.scene_absolute_number = 0

            if sqlResults[0]["release_name"] is not None:
                self.release_name = sqlResults[0]["release_name"]

            if sqlResults[0]["is_proper"]:
                self.is_proper = int(sqlResults[0]["is_proper"])

            self.dirty = False
            return True

    def loadFromIndexer(self, season=None, episode=None, cache=True, tvapi=None, cachedSeason=None):

        if season is None:
            season = self.season
        if episode is None:
            episode = self.episode

        logger.log(str(self.show.indexerid) + u": Loading episode details from " + sickbeard.indexerApi(
            self.show.indexer).name + " for episode " + str(season) + "x" + str(episode), logger.DEBUG)

        indexer_lang = self.show.lang

        try:
            if cachedSeason is None:
                if tvapi is None:
                    lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

                    if not cache:
                        lINDEXER_API_PARMS['cache'] = False

                    if indexer_lang:
                        lINDEXER_API_PARMS['language'] = indexer_lang

                    if self.show.dvdorder != 0:
                        lINDEXER_API_PARMS['dvdorder'] = True

                    t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
                else:
                    t = tvapi
                myEp = t[self.show.indexerid][season][episode]
            else:
                myEp = cachedSeason[episode]

        except (sickbeard.indexer_error, IOError), e:
            logger.log(u"" + sickbeard.indexerApi(self.indexer).name + " threw up an error: " + ex(e), logger.DEBUG)
            # if the episode is already valid just log it, if not throw it up
            if self.name:
                logger.log(u"" + sickbeard.indexerApi(
                    self.indexer).name + " timed out but we have enough info from other sources, allowing the error",
                           logger.DEBUG)
                return
            else:
                logger.log(u"" + sickbeard.indexerApi(self.indexer).name + " timed out, unable to create the episode",
                           logger.ERROR)
                return False
        except (sickbeard.indexer_episodenotfound, sickbeard.indexer_seasonnotfound):
            logger.log(u"Unable to find the episode on " + sickbeard.indexerApi(
                self.indexer).name + "... has it been removed? Should I delete from db?", logger.DEBUG)
            # if I'm no longer on the Indexers but I once was then delete myself from the DB
            if self.indexerid != -1:
                self.deleteEpisode()
            return

        if getattr(myEp, 'episodename', None) is None:
            logger.log(u"This episode (" + self.show.name + " - " + str(season) + "x" + str(
                episode) + ") has no name on " + sickbeard.indexerApi(self.indexer).name + "")
            # if I'm incomplete on TVDB but I once was complete then just delete myself from the DB for now
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        if getattr(myEp, 'absolute_number', None) is None:
            logger.log(u"This episode (" + self.show.name + " - " + str(season) + "x" + str(
                episode) + ") has no absolute number on " + sickbeard.indexerApi(
                self.indexer).name
                       , logger.DEBUG)
        else:
            logger.log(
                str(self.show.indexerid) + ": The absolute_number for " + str(season) + "x" + str(episode) + " is : " +
                str(myEp["absolute_number"]), logger.DEBUG)
            self.absolute_number = int(myEp["absolute_number"])

        self.name = getattr(myEp, 'episodename', "")
        self.season = season
        self.episode = episode

        self.description = getattr(myEp, 'overview', "")

        firstaired = getattr(myEp, 'firstaired', None)
        if firstaired is None or firstaired in "0000-00-00":
            firstaired = str(datetime.date.fromordinal(1))
        rawAirdate = [int(x) for x in firstaired.split("-")]

        try:
            self.airdate = datetime.date(rawAirdate[0], rawAirdate[1], rawAirdate[2])
        except (ValueError, IndexError):
            logger.log(u"Malformed air date retrieved from " + sickbeard.indexerApi(
                self.indexer).name + " (" + self.show.name + " - " + str(season) + "x" + str(episode) + ")",
                       logger.ERROR)
            # if I'm incomplete on TVDB but I once was complete then just delete myself from the DB for now
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        # early conversion to int so that episode doesn't get marked dirty
        self.indexerid = getattr(myEp, 'id', None)
        if self.indexerid is None:
            logger.log(u"Failed to retrieve ID from " + sickbeard.indexerApi(self.indexer).name, logger.ERROR)
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        # don't update show status if show dir is missing, unless it's missing on purpose
        if not ek.ek(os.path.isdir, self.show._location) and not sickbeard.CREATE_MISSING_SHOW_DIRS and not sickbeard.ADD_SHOWS_WO_DIR:
            logger.log(
                u"The show dir is missing, not bothering to change the episode statuses since it'd probably be invalid")
            return

        if self.location:
            logger.log(str(self.show.indexerid) + u": Setting status for " + str(season) + "x" + str(
                episode) + " based on status " + str(self.status) + " and existence of " + self.location, logger.DEBUG)

        # if we don't have the file
        if not ek.ek(os.path.isfile, self.location):

            # if it hasn't aired yet set the status to UNAIRED
            if self.airdate >= datetime.date.today() and self.status in [SKIPPED, UNAIRED, UNKNOWN, WANTED]:
                logger.log(u"Episode airs in the future, marking it " + str(UNAIRED), logger.DEBUG)
                self.status = UNAIRED

            # if there's no airdate then set it to skipped (and respect ignored)
            elif self.airdate == datetime.date.fromordinal(1):
                if self.status == IGNORED:
                    logger.log(u"Episode has no air date, but it's already marked as ignored", logger.DEBUG)
                else:
                    logger.log(u"Episode has no air date, automatically marking it skipped", logger.DEBUG)
                    self.status = SKIPPED

            # if we don't have the file and the airdate is in the past
            else:
                if self.status == UNAIRED:
                    self.status = WANTED

                # if we somehow are still UNKNOWN then just skip it
                elif self.status == UNKNOWN:
                    self.status = SKIPPED

                else:
                    logger.log(
                        u"Not touching status because we have no ep file, the airdate is in the past, and the status is " + str(
                            self.status), logger.DEBUG)

        # if we have a media file then it's downloaded
        elif sickbeard.helpers.isMediaFile(self.location):
            # leave propers alone, you have to either post-process them or manually change them back
            if self.status not in Quality.SNATCHED_PROPER + Quality.DOWNLOADED + Quality.SNATCHED + [ARCHIVED]:
                logger.log(
                    u"5 Status changes from " + str(self.status) + " to " + str(Quality.statusFromName(self.location)),
                    logger.DEBUG)
                self.status = Quality.statusFromName(self.location)

        # shouldn't get here probably
        else:
            logger.log(u"6 Status changes from " + str(self.status) + " to " + str(UNKNOWN), logger.DEBUG)
            self.status = UNKNOWN

    def loadFromNFO(self, location):

        if not ek.ek(os.path.isdir, self.show._location):
            logger.log(
                str(self.show.indexerid) + u": The show dir is missing, not bothering to try loading the episode NFO")
            return

        logger.log(
            str(self.show.indexerid) + u": Loading episode details from the NFO file associated with " + location,
            logger.DEBUG)

        self.location = location

        if self.location != "":

            if self.status == UNKNOWN:
                if sickbeard.helpers.isMediaFile(self.location):
                    logger.log(u"7 Status changes from " + str(self.status) + " to " + str(
                        Quality.statusFromName(self.location)), logger.DEBUG)
                    self.status = Quality.statusFromName(self.location)

            nfoFile = sickbeard.helpers.replaceExtension(self.location, "nfo")
            logger.log(str(self.show.indexerid) + u": Using NFO name " + nfoFile, logger.DEBUG)

            if ek.ek(os.path.isfile, nfoFile):
                try:
                    showXML = etree.ElementTree(file=nfoFile)
                except (SyntaxError, ValueError), e:
                    logger.log(u"Error loading the NFO, backing up the NFO and skipping for now: " + ex(e),
                               logger.ERROR)  # TODO: figure out what's wrong and fix it
                    try:
                        ek.ek(os.rename, nfoFile, nfoFile + ".old")
                    except Exception, e:
                        logger.log(
                            u"Failed to rename your episode's NFO file - you need to delete it or fix it: " + ex(e),
                            logger.ERROR)
                    raise exceptions.NoNFOException("Error in NFO format")

                for epDetails in showXML.getiterator('episodedetails'):
                    if epDetails.findtext('season') is None or int(epDetails.findtext('season')) != self.season or \
                                    epDetails.findtext('episode') is None or int(
                            epDetails.findtext('episode')) != self.episode:
                        logger.log(str(
                            self.show.indexerid) + u": NFO has an <episodedetails> block for a different episode - wanted " + str(
                            self.season) + "x" + str(self.episode) + " but got " + str(
                            epDetails.findtext('season')) + "x" + str(epDetails.findtext('episode')), logger.DEBUG)
                        continue

                    if epDetails.findtext('title') is None or epDetails.findtext('aired') is None:
                        raise exceptions.NoNFOException("Error in NFO format (missing episode title or airdate)")

                    self.name = epDetails.findtext('title')
                    self.episode = int(epDetails.findtext('episode'))
                    self.season = int(epDetails.findtext('season'))

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

            if ek.ek(os.path.isfile, sickbeard.helpers.replaceExtension(nfoFile, "tbn")):
                self.hastbn = True
            else:
                self.hastbn = False

    def __str__(self):

        toReturn = ""
        toReturn += str(self.show.name) + " - " + str(self.season) + "x" + str(self.episode) + " - " + str(
            self.name) + "\n"
        toReturn += "location: " + str(self.location) + "\n"
        toReturn += "description: " + str(self.description) + "\n"
        toReturn += "subtitles: " + str(",".join(self.subtitles)) + "\n"
        toReturn += "subtitles_searchcount: " + str(self.subtitles_searchcount) + "\n"
        toReturn += "subtitles_lastsearch: " + str(self.subtitles_lastsearch) + "\n"
        toReturn += "airdate: " + str(self.airdate.toordinal()) + " (" + str(self.airdate) + ")\n"
        toReturn += "hasnfo: " + str(self.hasnfo) + "\n"
        toReturn += "hastbn: " + str(self.hastbn) + "\n"
        toReturn += "status: " + str(self.status) + "\n"
        return toReturn

    def createMetaFiles(self):

        if not ek.ek(os.path.isdir, self.show._location):
            logger.log(str(self.show.indexerid) + u": The show dir is missing, not bothering to try to create metadata")
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

        logger.log(u"Deleting " + self.show.name + " " + str(self.season) + "x" + str(self.episode) + " from the DB",
                   logger.DEBUG)

        # remove myself from the show dictionary
        if self.show.getEpisode(self.season, self.episode, noCreate=True) == self:
            logger.log(u"Removing myself from my show's list", logger.DEBUG)
            del self.show.episodes[self.season][self.episode]

        # delete myself from the DB
        logger.log(u"Deleting myself from the database", logger.DEBUG)
        myDB = db.DBConnection()
        sql = "DELETE FROM tv_episodes WHERE showid=" + str(self.show.indexerid) + " AND season=" + str(
            self.season) + " AND episode=" + str(self.episode)
        myDB.action(sql)

        raise exceptions.EpisodeDeletedException()

    def get_sql(self, forceSave=False):
        """
        Creates SQL queue for this episode if any of its data has been changed since the last save.

        forceSave: If True it will create SQL queue even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """

        if not self.dirty and not forceSave:
            logger.log(str(self.show.indexerid) + u": Not creating SQL queue - record is not dirty", logger.DEBUG)
            return

        myDB = db.DBConnection()
        rows = myDB.select(
            'SELECT episode_id FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?',
            [self.show.indexerid, self.season, self.episode])

        epID = None
        if rows:
            epID = int(rows[0]['episode_id'])

        if epID:
            # use a custom update method to get the data into the DB for existing records.
            return [
                "UPDATE tv_episodes SET indexerid = ?, indexer = ?, name = ?, description = ?, subtitles = ?, "
                "subtitles_searchcount = ?, subtitles_lastsearch = ?, airdate = ?, hasnfo = ?, hastbn = ?, status = ?, "
                "location = ?, file_size = ?, release_name = ?, is_proper = ?, showid = ?, season = ?, episode = ?, "
                "absolute_number = ? WHERE episode_id = ?",
                [self.indexerid, self.indexer, self.name, self.description, ",".join([sub for sub in self.subtitles]),
                 self.subtitles_searchcount, self.subtitles_lastsearch, self.airdate.toordinal(), self.hasnfo,
                 self.hastbn,
                 self.status, self.location, self.file_size, self.release_name, self.is_proper, self.show.indexerid,
                 self.season, self.episode, self.absolute_number, epID]]
        else:
            # use a custom insert method to get the data into the DB.
            return [
                "INSERT OR IGNORE INTO tv_episodes (episode_id, indexerid, indexer, name, description, subtitles, subtitles_searchcount, subtitles_lastsearch, airdate, hasnfo, hastbn, status, location, file_size, release_name, is_proper, showid, season, episode, absolute_number) VALUES "
                "((SELECT episode_id FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?),?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
                [self.show.indexerid, self.season, self.episode, self.indexerid, self.indexer, self.name,
                 self.description,
                 ",".join([sub for sub in self.subtitles]), self.subtitles_searchcount, self.subtitles_lastsearch,
                 self.airdate.toordinal(), self.hasnfo, self.hastbn, self.status, self.location, self.file_size,
                 self.release_name, self.is_proper, self.show.indexerid, self.season, self.episode,
                 self.absolute_number]]

    def saveToDB(self, forceSave=False):
        """
        Saves this episode to the database if any of its data has been changed since the last save.
        
        forceSave: If True it will save to the database even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """

        if not self.dirty and not forceSave:
            logger.log(str(self.show.indexerid) + u": Not saving episode to db - record is not dirty", logger.DEBUG)
            return

        logger.log(str(self.show.indexerid) + u": Saving episode details to database", logger.DEBUG)

        logger.log(u"STATUS IS " + str(self.status), logger.DEBUG)

        newValueDict = {"indexerid": self.indexerid,
                        "indexer": self.indexer,
                        "name": self.name,
                        "description": self.description,
                        "subtitles": ",".join([sub for sub in self.subtitles]),
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
                        "absolute_number": self.absolute_number
        }
        controlValueDict = {"showid": self.show.indexerid,
                            "season": self.season,
                            "episode": self.episode}

        # use a custom update/insert method to get the data into the DB
        myDB = db.DBConnection()
        myDB.upsert("tv_episodes", newValueDict, controlValueDict)

    def fullPath(self):
        if self.location == None or self.location == "":
            return None
        else:
            return ek.ek(os.path.join, self.show.location, self.location)

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

    def prettyName(self):
        """
        Returns the name of this episode in a "pretty" human-readable format. Used for logging
        and notifications and such.

        Returns: A string representing the episode's name and season/ep numbers 
        """

        if self.show.anime and not self.show.scene:
            return self._format_pattern('%SN - %AB - %EN')
        elif self.show.air_by_date:
            return self._format_pattern('%SN - %AD - %EN')

        return self._format_pattern('%SN - %Sx%0E - %EN')

    def _ep_name(self):
        """
        Returns the name of the episode to use during renaming. Combines the names of related episodes.
        Eg. "Ep Name (1)" and "Ep Name (2)" becomes "Ep Name"
            "Ep Name" and "Other Ep Name" becomes "Ep Name & Other Ep Name"
        """

        multiNameRegex = "(.*) \(\d{1,2}\)"

        self.relatedEps = sorted(self.relatedEps, key=lambda x: x.episode)

        if len(self.relatedEps) == 0:
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

                if curGoodName == None:
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

    def _replace_map(self):
        """
        Generates a replacement map for this episode which maps all possible custom naming patterns to the correct
        value for this episode.
        
        Returns: A dict with patterns as the keys and their replacement values as the values.
        """

        ep_name = self._ep_name()

        def dot(name):
            return helpers.sanitizeSceneName(name)

        def us(name):
            return re.sub('[ -]', '_', name)

        def release_name(name):
            if name and name.lower().endswith('.nzb'):
                name = name.rpartition('.')[0]
            return name

        def release_group(name):
            if not name:
                return ''

            try:
                np = NameParser(name, naming_pattern=True)
                parse_result = np.parse(name)
            except InvalidNameException, e:
                logger.log(u"Unable to get parse release_group: " + ex(e), logger.DEBUG)
                return ''

            if not parse_result.release_group:
                return ''
            return parse_result.release_group

        epStatus, epQual = Quality.splitCompositeStatus(self.status)  # @UnusedVariable

        if sickbeard.NAMING_STRIP_YEAR:
            show_name = re.sub("\(\d+\)$", "", self.show.name).rstrip()
        else:
            show_name = self.show.name

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
            '%S': str(self.season),
            '%0S': '%02d' % self.season,
            '%E': str(self.episode),
            '%0E': '%02d' % self.episode,
            '%XS': str(self.scene_season),
            '%0XS': '%02d' % self.scene_season,
            '%XE': str(self.scene_episode),
            '%0XE': '%02d' % self.scene_episode,
            '%AB': '%(#)03d' % {'#': self.absolute_number},
            '%XAB': '%(#)03d' % {'#': self.scene_absolute_number},
            '%RN': release_name(self.release_name),
            '%RG': release_group(self.release_name),
            '%AD': str(self.airdate).replace('-', ' '),
            '%A.D': str(self.airdate).replace('-', '.'),
            '%A_D': us(str(self.airdate)),
            '%A-D': str(self.airdate),
            '%Y': str(self.airdate.year),
            '%M': str(self.airdate.month),
            '%D': str(self.airdate.day),
            '%0M': '%02d' % self.airdate.month,
            '%0D': '%02d' % self.airdate.day,
            '%RT': "PROPER" if self.is_proper else "",
        }

    def _format_string(self, pattern, replace_map):
        """
        Replaces all template strings with the correct value
        """

        result_name = pattern

        # do the replacements
        for cur_replacement in sorted(replace_map.keys(), reverse=True):
            result_name = result_name.replace(cur_replacement, helpers.sanitizeFileName(replace_map[cur_replacement]))
            result_name = result_name.replace(cur_replacement.lower(),
                                              helpers.sanitizeFileName(replace_map[cur_replacement].lower()))

        return result_name

    def _format_pattern(self, pattern=None, multi=None, anime_type=None):
        """
        Manipulates an episode naming pattern and then fills the template in
        """

        if pattern == None:
            pattern = sickbeard.NAMING_PATTERN

        if multi == None:
            multi = sickbeard.NAMING_MULTI_EP

        if anime_type == None:
            anime_type = sickbeard.NAMING_ANIME

        replace_map = self._replace_map()

        result_name = pattern

        # if there's no release group then replace it with a reasonable facsimile
        if not replace_map['%RN']:
            if self.show.air_by_date or self.show.sports:
                result_name = result_name.replace('%RN', '%S.N.%A.D.%E.N-SiCKRAGE')
                result_name = result_name.replace('%rn', '%s.n.%A.D.%e.n-sickrage')
            elif self.show.anime:
                result_name = result_name.replace('%RN', '%S.N.%AB.%E.N-SiCKRAGE')
                result_name = result_name.replace('%rn', '%s.n.%ab.%e.n-sickrage')
            else:
                result_name = result_name.replace('%RN', '%S.N.S%0SE%0E.%E.N-SiCKRAGE')
                result_name = result_name.replace('%rn', '%s.n.s%0se%0e.%e.n-sickrage')

            result_name = result_name.replace('%RG', 'SICKRAGE')
            result_name = result_name.replace('%rg', 'sickrage')
            logger.log(u"Episode has no release name, replacing it with a generic one: " + result_name, logger.DEBUG)

        if not replace_map['%RT']:
            result_name = re.sub('([ _.-]*)%RT([ _.-]*)', r'\2', result_name)

        # split off ep name part only
        name_groups = re.split(r'[\\/]', result_name)

        # figure out the double-ep numbering style for each group, if applicable
        for cur_name_group in name_groups:

            season_format = sep = ep_sep = ep_format = None

            season_ep_regex = '''
                                (?P<pre_sep>[ _.-]*)
                                ((?:s(?:eason|eries)?\s*)?%0?S(?![._]?N))
                                (.*?)
                                (%0?E(?![._]?N))
                                (?P<post_sep>[ _.-]*)
                              '''
            ep_only_regex = '(E?%0?E(?![._]?N))'

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
                if multi in (NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED) and other_ep != self.relatedEps[
                    -1]:
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

                ep_string += other_ep._format_string(ep_format.upper(), other_ep._replace_map())

            if self.show.anime and anime_type != 3:
                if self.absolute_number == 0:
                    curAbsolute_number = self.episode
                else:
                    curAbsolute_number = self.absolute_number

                if self.season != 0:  # dont set absolute numbers if we are on specials !
                    if anime_type == 1:  # this crazy person wants both ! (note: +=)
                        ep_string += sep + "%(#)03d" % {
                            "#": curAbsolute_number}
                    elif anime_type == 2:  # total anime freak only need the absolute number ! (note: =)
                        ep_string = "%(#)03d" % {"#": curAbsolute_number}

                    for relEp in self.relatedEps:
                        if relEp.absolute_number != 0:
                            ep_string += '-' + "%(#)03d" % {"#": relEp.absolute_number}
                        else:
                            ep_string += '-' + "%(#)03d" % {"#": relEp.episode}

            regex_replacement = None
            if anime_type == 2:
                regex_replacement = r'\g<pre_sep>' + ep_string + r'\g<post_sep>'
            elif season_ep_match:
                regex_replacement = r'\g<pre_sep>\g<2>\g<3>' + ep_string + r'\g<post_sep>'
            elif ep_only_match:
                regex_replacement = ep_string

            if regex_replacement:
                # fill out the template for this piece and then insert this piece into the actual pattern
                cur_name_group_result = re.sub('(?i)(?x)' + regex_used, regex_replacement, cur_name_group)
                # cur_name_group_result = cur_name_group.replace(ep_format, ep_string)
                # logger.log(u"found "+ep_format+" as the ep pattern using "+regex_used+" and replaced it with "+regex_replacement+" to result in "+cur_name_group_result+" from "+cur_name_group, logger.DEBUG)
                result_name = result_name.replace(cur_name_group, cur_name_group_result)

        result_name = self._format_string(result_name, replace_map)

        logger.log(u"formatting pattern: " + pattern + " -> " + result_name, logger.DEBUG)

        return result_name

    def proper_path(self):
        """    
        Figures out the path where this episode SHOULD live according to the renaming rules, relative from the show dir
        """

        result = self.formatted_filename()

        # if they want us to flatten it and we're allowed to flatten it then we will
        if self.show.flatten_folders and not sickbeard.NAMING_FORCE_FOLDERS:
            return result

        # if not we append the folder on and use that
        else:
            result = ek.ek(os.path.join, self.formatted_dir(), result)

        return result

    def formatted_dir(self, pattern=None, multi=None):
        """
        Just the folder name of the episode
        """

        if pattern == None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and sickbeard.NAMING_CUSTOM_ABD and not self.relatedEps:
                pattern = sickbeard.NAMING_ABD_PATTERN
            elif self.show.sports and sickbeard.NAMING_CUSTOM_SPORTS and not self.relatedEps:
                pattern = sickbeard.NAMING_SPORTS_PATTERN
            else:
                pattern = sickbeard.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        if len(name_groups) == 1:
            return ''
        else:
            return self._format_pattern(os.sep.join(name_groups[:-1]), multi)

    def formatted_filename(self, pattern=None, multi=None, anime_type=None):
        """
        Just the filename of the episode, formatted based on the naming settings
        """

        if pattern == None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and sickbeard.NAMING_CUSTOM_ABD and not self.relatedEps:
                pattern = sickbeard.NAMING_ABD_PATTERN
            elif self.show.sports and sickbeard.NAMING_CUSTOM_SPORTS and not self.relatedEps:
                pattern = sickbeard.NAMING_SPORTS_PATTERN
            else:
                pattern = sickbeard.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        return self._format_pattern(name_groups[-1], multi, anime_type)

    def rename(self):
        """
        Renames an episode file and all related files to the location and filename as specified
        in the naming settings.
        """

        if not ek.ek(os.path.isfile, self.location):
            logger.log(u"Can't perform rename on " + self.location + " when it doesn't exist, skipping", logger.WARNING)
            return

        proper_path = self.proper_path()
        absolute_proper_path = ek.ek(os.path.join, self.show.location, proper_path)
        absolute_current_path_no_ext, file_ext = ek.ek(os.path.splitext, self.location)
        absolute_current_path_no_ext_length = len(absolute_current_path_no_ext)

        related_subs = []

        current_path = absolute_current_path_no_ext

        if absolute_current_path_no_ext.startswith(self.show.location):
            current_path = absolute_current_path_no_ext[len(self.show.location):]

        logger.log(u"Renaming/moving episode from the base path " + self.location + " to " + absolute_proper_path,
                   logger.DEBUG)

        # if it's already named correctly then don't do anything
        if proper_path == current_path:
            logger.log(str(self.indexerid) + u": File " + self.location + " is already named correctly, skipping",
                       logger.DEBUG)
            return

        related_files = postProcessor.PostProcessor(self.location).list_associated_files(
            self.location)

        if self.show.subtitles and sickbeard.SUBTITLES_DIR != '':
            related_subs = postProcessor.PostProcessor(self.location).list_associated_files(sickbeard.SUBTITLES_DIR,
                                                                                            subtitles_only=True)
            absolute_proper_subs_path = ek.ek(os.path.join, sickbeard.SUBTITLES_DIR, self.formatted_filename())

        logger.log(u"Files associated to " + self.location + ": " + str(related_files), logger.DEBUG)

        # move the ep file
        result = helpers.rename_ep_file(self.location, absolute_proper_path, absolute_current_path_no_ext_length)

        # move related files
        for cur_related_file in related_files:
            cur_result = helpers.rename_ep_file(cur_related_file, absolute_proper_path,
                                                absolute_current_path_no_ext_length)
            if not cur_result:
                logger.log(str(self.indexerid) + u": Unable to rename file " + cur_related_file, logger.ERROR)

        for cur_related_sub in related_subs:
            absolute_proper_subs_path = ek.ek(os.path.join, sickbeard.SUBTITLES_DIR, self.formatted_filename())
            cur_result = helpers.rename_ep_file(cur_related_sub, absolute_proper_subs_path,
                                                absolute_current_path_no_ext_length)
            if not cur_result:
                logger.log(str(self.indexerid) + u": Unable to rename file " + cur_related_sub, logger.ERROR)

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
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)

