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


import os.path
import datetime
import threading
import re
import glob
import stat
import traceback

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

try:
    from send2trash import send2trash
except ImportError:
    pass

from imdb import imdb

import sickbeard
from sickbeard import db
from sickbeard import helpers, logger
from sickbeard import image_cache
from sickbeard import notifiers
from sickbeard import postProcessor
from sickbeard import subtitles
from sickbeard.blackandwhitelist import BlackAndWhiteList
from sickbeard import network_timezones
from sickbeard.indexers.indexer_config import INDEXER_TVRAGE
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException
from sickrage.helper.common import dateTimeFormat
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import EpisodeDeletedException, EpisodeNotFoundException, ex
from sickrage.helper.exceptions import MultipleEpisodesInDatabaseException, MultipleShowsInDatabaseException
from sickrage.helper.exceptions import MultipleShowObjectsException, NoNFOException, ShowDirectoryNotFoundException
from sickrage.helper.exceptions import ShowNotFoundException

from sickbeard.common import Quality, Overview, statusStrings
from sickbeard.common import DOWNLOADED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, ARCHIVED, IGNORED, UNAIRED, WANTED, SKIPPED, \
    UNKNOWN, FAILED
from sickbeard.common import NAMING_DUPLICATE, NAMING_EXTEND, NAMING_LIMITED_EXTEND, NAMING_SEPARATED_REPEAT, \
    NAMING_LIMITED_EXTEND_E_PREFIXED

import shutil
import shutil_custom


shutil.copyfile = shutil_custom.copyfile_custom


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
        self._imdbid = ""
        self._network = ""
        self._genre = ""
        self._classification = ""
        self._runtime = 0
        self._imdb_info = {}
        self._quality = int(sickbeard.QUALITY_DEFAULT)
        self._flatten_folders = int(sickbeard.FLATTEN_FOLDERS_DEFAULT)
        self._status = "Unknown"
        self._airs = ""
        self._startyear = 0
        self._paused = 0
        self._air_by_date = 0
        self._subtitles = int(sickbeard.SUBTITLES_DEFAULT)
        self._dvdorder = 0
        self._archive_firstmatch = 0
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

        otherShow = helpers.findCertainShow(sickbeard.showList, self.indexerid)
        if otherShow != None:
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
    default_ep_status = property(lambda self: self._default_ep_status, dirty_setter("_default_ep_status"))

    @property
    def is_anime(self):
        if int(self.anime) > 0:
            return True
        else:
            return False

    @property
    def is_sports(self):
        if int(self.sports) > 0:
            return True
        else:
            return False

    @property
    def is_scene(self):
        if int(self.scene) > 0:
            return True
        else:
            return False

    @property
    def network_logo_name(self):
        return self.network.replace(u'\u00C9', 'e').replace(u'\u00E9', 'e').lower()

    def _getLocation(self):
        # no dir check needed if missing show dirs are created during post-processing
        if sickbeard.CREATE_MISSING_SHOW_DIRS:
            return self._location

        if ek(os.path.isdir, self._location):
            return self._location
        else:
            raise ShowDirectoryNotFoundException("Show folder doesn't exist, you shouldn't be using it")

    def _setLocation(self, newLocation):
        logger.log(u"Setter sets location to " + newLocation, logger.DEBUG)
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
            if not cur_ep:
                continue

            cur_ep.relatedEps = []
            if cur_ep.location:
                # if there is a location, check if it's a multi-episode (share_location > 0) and put them in relatedEps
                if cur_result["share_location"] > 0:
                    related_eps_result = myDB.select(
                        "SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND location = ? AND episode != ? ORDER BY episode ASC",
                        [self.indexerid, cur_ep.season, cur_ep.location, cur_ep.episode])
                    for cur_related_ep in related_eps_result:
                        related_ep = self.getEpisode(int(cur_related_ep["season"]), int(cur_related_ep["episode"]))
                        if related_ep and related_ep not in cur_ep.relatedEps:
                            cur_ep.relatedEps.append(related_ep)
            ep_list.append(cur_ep)

        return ep_list


    def getEpisode(self, season=None, episode=None, file=None, noCreate=False, absolute_number=None, forceUpdate=False):

        # if we get an anime get the real season and episode
        if self.is_anime and absolute_number and not season and not episode:
            myDB = db.DBConnection()
            sql = "SELECT * FROM tv_episodes WHERE showid = ? AND absolute_number = ? AND season != 0"
            sqlResults = myDB.select(sql, [self.indexerid, absolute_number])

            if len(sqlResults) == 1:
                episode = int(sqlResults[0]["episode"])
                season = int(sqlResults[0]["season"])
                logger.log(
                    "Found episode by absolute_number %s which is S%02dE%02d" % (absolute_number, season or 0, episode or 0), logger.DEBUG)
            elif len(sqlResults) > 1:
                logger.log(u"Multiple entries for absolute number: " + str(
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

            # logger.log(str(self.indexerid) + u": An object for episode S%02dE%02d didn't exist in the cache, trying to create it" % (season or 0, episode or 0), logger.DEBUG)

            if file:
                ep = TVEpisode(self, season, episode, file)
            else:
                ep = TVEpisode(self, season, episode)

            if ep != None:
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
        myDB = db.DBConnection()
        sql_result = myDB.select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season > '0' AND airdate > '1' AND status > '1' ORDER BY airdate DESC LIMIT 1",
            [self.indexerid])

        if sql_result:
            last_airdate = datetime.date.fromordinal(sql_result[0]['airdate'])
            if last_airdate >= (update_date - graceperiod) and last_airdate <= (update_date + graceperiod):
                return True

        # get next upcoming UNAIRED episode to compare against today + graceperiod
        sql_result = myDB.select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season > '0' AND airdate > '1' AND status = '1' ORDER BY airdate ASC LIMIT 1",
            [self.indexerid])

        if sql_result:
            next_airdate = datetime.date.fromordinal(sql_result[0]['airdate'])
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
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return False

        logger.log(str(self.indexerid) + u": Writing NFOs for show", logger.DEBUG)
        for cur_provider in sickbeard.metadata_provider_dict.values():
            result = cur_provider.create_show_metadata(self) or result

        return result

    def writeMetadata(self, show_only=False):

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return

        self.getImages()

        self.writeShowNFO()

        if not show_only:
            self.writeEpisodeNFOs()

    def writeEpisodeNFOs(self):

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return

        logger.log(str(self.indexerid) + u": Writing NFOs for all episodes", logger.DEBUG)

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        for epResult in sqlResults:
            logger.log(str(self.indexerid) + u": Retrieving/creating episode S%02dE%02d" % (epResult["season"] or 0, epResult["episode"] or 0), logger.DEBUG)
            curEp = self.getEpisode(epResult["season"], epResult["episode"])
            if not curEp:
                continue

            curEp.createMetaFiles()

    def updateMetadata(self):

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return

        self.updateShowNFO()

    def updateShowNFO(self):

        result = False

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, skipping NFO generation")
            return False

        logger.log(str(self.indexerid) + u": Updating NFOs for show with new indexer info")
        for cur_provider in sickbeard.metadata_provider_dict.values():
            result = cur_provider.update_show_indexer_metadata(self) or result

        return result

    # find all media files in the show folder and create episodes for as many as possible
    def loadEpisodesFromDir(self):

        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + u": Show dir doesn't exist, not loading episodes from disk", logger.DEBUG)
            return

        logger.log(str(self.indexerid) + u": Loading all episodes from the show directory " + self._location, logger.DEBUG)

        # get file list
        mediaFiles = helpers.listMediaFiles(self._location)
        logger.log(u"%s: Found files: %s" %
                   (self.indexerid, mediaFiles), logger.DEBUG)

        # create TVEpisodes from each media file (if possible)
        sql_l = []
        for mediaFile in mediaFiles:
            parse_result = None
            curEpisode = None

            logger.log(str(self.indexerid) + u": Creating episode from " + mediaFile, logger.DEBUG)
            try:
                curEpisode = self.makeEpFromFile(ek(os.path.join, self._location, mediaFile))
            except (ShowNotFoundException, EpisodeNotFoundException), e:
                logger.log(u"Episode " + mediaFile + " returned an exception: " + ex(e), logger.ERROR)
                continue
            except EpisodeDeletedException:
                logger.log(u"The episode deleted itself when I tried making an object for it", logger.DEBUG)

            if curEpisode is None:
                continue

            # see if we should save the release name in the db
            ep_file_name = ek(os.path.basename, curEpisode.location)
            ep_file_name = ek(os.path.splitext, ep_file_name)[0]

            try:
                parse_result = None
                np = NameParser(False, showObj=self, tryIndexers=True)
                parse_result = np.parse(ep_file_name)
            except (InvalidNameException, InvalidShowException):
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
                    except Exception:
                        logger.log(u"%s: Could not refresh subtitles" % self.indexerid, logger.ERROR)
                        logger.log(traceback.format_exc(), logger.DEBUG)

                sql_l.append(curEpisode.get_sql())


        if sql_l:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)


    def loadEpisodesFromDB(self):

        logger.log(u"Loading all episodes from the DB", logger.DEBUG)

        myDB = db.DBConnection()
        sql = "SELECT * FROM tv_episodes WHERE showid = ?"
        sqlResults = myDB.select(sql, [self.indexerid])

        scannedEps = {}

        lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()

        if self.lang:
            lINDEXER_API_PARMS['language'] = self.lang
            logger.log(u"Using language: " + str(self.lang), logger.DEBUG)

        if self.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        # logger.log(u"lINDEXER_API_PARMS: " + str(lINDEXER_API_PARMS), logger.DEBUG)
        # Spamming log
        t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

        cachedShow = t[self.indexerid]
        cachedSeasons = {}

        for curResult in sqlResults:

            curSeason = int(curResult["season"])
            curEpisode = int(curResult["episode"])
            curShowid = int(curResult['showid'])

            logger.log(u"%s: loading Episodes from DB" % curShowid, logger.DEBUG)
            deleteEp = False

            if curSeason not in cachedSeasons:
                try:
                    cachedSeasons[curSeason] = cachedShow[curSeason]
                except sickbeard.indexer_seasonnotfound, e:
                    logger.log(u"%s: Error when trying to load the episode from %s. Message: %s " %
                               (curShowid, sickbeard.indexerApi(self.indexer).name, e.message), logger.WARNING)
                    deleteEp = True

            if not curSeason in scannedEps:
                logger.log(u"Not curSeason in scannedEps", logger.DEBUG)
                scannedEps[curSeason] = {}

            logger.log(u"%s: Loading episode S%02dE%02d from the DB" % (curShowid, curSeason or 0, curEpisode or 0), logger.DEBUG)

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
                logger.log(u"Tried loading an episode from the DB that should have been deleted, skipping it",
                           logger.DEBUG)
                continue

        logger.log(u"Finished loading all episodes from the DB", logger.DEBUG)

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
            logger.log(u"" + sickbeard.indexerApi(self.indexer).name +
                       " timed out, unable to update episodes from " +
                       sickbeard.indexerApi(self.indexer).name, logger.WARNING)
            return None

        logger.log(
            str(self.indexerid) + u": Loading all episodes from " + sickbeard.indexerApi(self.indexer).name + "..", logger.DEBUG)

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
                    logger.log(u"%s: %s object for S%02dE%02d is incomplete, skipping this episode" % (self.indexerid, sickbeard.indexerApi(self.indexer).name, season or 0, episode or 0))
                    continue
                else:
                    try:
                        ep.loadFromIndexer(tvapi=t)
                    except EpisodeDeletedException:
                        logger.log(u"The episode was deleted, skipping the rest of the load")
                        continue

                with ep.lock:
                    logger.log(u"%s: Loading info from %s for episode S%02dE%02d" % (self.indexerid, sickbeard.indexerApi(self.indexer).name, season or 0, episode or 0), logger.DEBUG)
                    ep.loadFromIndexer(season, episode, tvapi=t)

                    sql_l.append(ep.get_sql())

                scannedEps[season][episode] = True

        if len(sql_l) > 0:
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

            # logger.log(u"Running metadata routines for " + cur_provider.name, logger.DEBUG)

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

        if not ek(os.path.isfile, file):
            logger.log(str(self.indexerid) + u": That isn't even a real file dude... " + file)
            return None

        logger.log(str(self.indexerid) + u": Creating episode object from " + file, logger.DEBUG)

        try:
            myParser = NameParser(showObj=self, tryIndexers=True)
            parse_result = myParser.parse(file)
        except InvalidNameException:
            logger.log(u"Unable to parse the filename " + file + " into a valid episode", logger.DEBUG)
            return None
        except InvalidShowException:
            logger.log(u"Unable to parse the filename " + file + " into a valid show", logger.DEBUG)
            return None

        if not len(parse_result.episode_numbers):
            logger.log(u"parse_result: " + str(parse_result))
            logger.log(u"No episode number found in " + file + ", ignoring it", logger.WARNING)
            return None

        # for now lets assume that any episode in the show dir belongs to that show
        season = parse_result.season_number if parse_result.season_number != None else 1
        episodes = parse_result.episode_numbers
        rootEp = None

        sql_l = []
        for curEpNum in episodes:

            episode = int(curEpNum)

            logger.log(u"%s: %s parsed to %s S%02dE%02d" % (self.indexerid, file, self.name, season or 0, episode or 0), logger.DEBUG)

            checkQualityAgain = False
            same_file = False

            curEp = self.getEpisode(season, episode)
            if not curEp:
                try:
                    curEp = self.getEpisode(season, episode, file)
                    if not curEp:
                        raise EpisodeNotFoundException
                except EpisodeNotFoundException:
                    logger.log(str(self.indexerid) + u": Unable to figure out what this file is, skipping",
                               logger.ERROR)
                    continue

            else:
                # if there is a new file associated with this ep then re-check the quality
                if curEp.location and ek(os.path.normpath, curEp.location) != ek(os.path.normpath, file):
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

            # if they replace a file on me I'll make some attempt at re-checking the quality unless I know it's the same file
            if checkQualityAgain and not same_file:
                newQuality = Quality.nameQuality(file, self.is_anime)
                logger.log(u"Since this file has been renamed, I checked " + file + " and found quality " +
                           Quality.qualityStrings[newQuality], logger.DEBUG)
                if newQuality != Quality.UNKNOWN:
                    with curEp.lock:
                        curEp.status = Quality.compositeStatus(DOWNLOADED, newQuality)


            # check for status/quality changes as long as it's a new file
            elif not same_file and sickbeard.helpers.isMediaFile(file) and curEp.status not in Quality.DOWNLOADED + Quality.ARCHIVED + [IGNORED]:
                oldStatus, oldQuality = Quality.splitCompositeStatus(curEp.status)
                newQuality = Quality.nameQuality(file, self.is_anime)
                if newQuality == Quality.UNKNOWN:
                    newQuality = Quality.assumeQuality(file)

                newStatus = None

                # if it was snatched and now exists then set the status correctly
                if oldStatus == SNATCHED and oldQuality <= newQuality:
                    logger.log(u"STATUS: this ep used to be snatched with quality " + Quality.qualityStrings[oldQuality] +
                               u" but a file exists with quality " + Quality.qualityStrings[newQuality] +
                               u" so I'm setting the status to DOWNLOADED", logger.DEBUG)
                    newStatus = DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif oldStatus == SNATCHED_PROPER and oldQuality < newQuality:
                    logger.log(u"STATUS: this ep used to be snatched proper with quality " + Quality.qualityStrings[oldQuality] +
                               u" but a file exists with quality " + Quality.qualityStrings[newQuality] +
                               u" so I'm setting the status to DOWNLOADED", logger.DEBUG)
                    newStatus = DOWNLOADED

                elif oldStatus not in (SNATCHED, SNATCHED_PROPER):
                    newStatus = DOWNLOADED

                if newStatus is not None:
                    with curEp.lock:
                        logger.log(u"STATUS: we have an associated file, so setting the status from " + str(
                            curEp.status) + u" to DOWNLOADED/" + str(Quality.statusFromName(file, anime=self.is_anime)),
                                   logger.DEBUG)
                        curEp.status = Quality.compositeStatus(newStatus, newQuality)

            with curEp.lock:
                sql_l.append(curEp.get_sql())

        if len(sql_l) > 0:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)


        # creating metafiles on the root should be good enough
        if rootEp:
            with rootEp.lock:
                rootEp.createMetaFiles()

        return rootEp

    def loadFromDB(self, skipNFO=False):

        logger.log(str(self.indexerid) + u": Loading show info from database", logger.DEBUG)

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_shows WHERE indexer_id = ?", [self.indexerid])

        if len(sqlResults) > 1:
            raise MultipleShowsInDatabaseException()
        elif len(sqlResults) == 0:
            logger.log(str(self.indexerid) + ": Unable to find the show in the database")
            return
        else:
            self.indexer = int(sqlResults[0]["indexer"] or 0)

            if not self.name:
                self.name = sqlResults[0]["show_name"]
            if not self.network:
                self.network = sqlResults[0]["network"]
            if not self.genre:
                self.genre = sqlResults[0]["genre"]
            if not self.classification:
                self.classification = sqlResults[0]["classification"]

            self.runtime = sqlResults[0]["runtime"]

            self.status = sqlResults[0]["status"]
            if self.status is None:
                self.status = "Unknown"

            self.airs = sqlResults[0]["airs"]
            if self.airs is None:
                self.airs = ""

            self.startyear = int(sqlResults[0]["startyear"] or 0)
            self.air_by_date = int(sqlResults[0]["air_by_date"] or 0)
            self.anime = int(sqlResults[0]["anime"] or 0)
            self.sports = int(sqlResults[0]["sports"] or 0)
            self.scene = int(sqlResults[0]["scene"] or 0)
            self.subtitles = int(sqlResults[0]["subtitles"] or 0)
            self.dvdorder = int(sqlResults[0]["dvdorder"] or 0)
            self.archive_firstmatch = int(sqlResults[0]["archive_firstmatch"] or 0)
            self.quality = int(sqlResults[0]["quality"] or UNKNOWN)
            self.flatten_folders = int(sqlResults[0]["flatten_folders"] or 0)
            self.paused = int(sqlResults[0]["paused"] or 0)

            try:
                self.location = sqlResults[0]["location"]
            except Exception:
                dirty_setter("_location")(self, sqlResults[0]["location"])

            if not self.lang:
                self.lang = sqlResults[0]["lang"]

            self.last_update_indexer = sqlResults[0]["last_update_indexer"]

            self.rls_ignore_words = sqlResults[0]["rls_ignore_words"]
            self.rls_require_words = sqlResults[0]["rls_require_words"]

            self.default_ep_status = int(sqlResults[0]["default_ep_status"] or SKIPPED)

            if not self.imdbid:
                self.imdbid = sqlResults[0]["imdb_id"]

            if self.is_anime:
                self.release_groups = BlackAndWhiteList(self.indexerid)

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

        if self.indexer is not INDEXER_TVRAGE:
            logger.log(str(self.indexerid) + u": Loading show info from " + sickbeard.indexerApi(self.indexer).name, logger.DEBUG)

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

            if self.airs is None:
                self.airs = ''

            if getattr(myEp, 'firstaired', None) is not None:
                self.startyear = int(str(myEp["firstaired"]).split('-')[0])

            self.status = getattr(myEp, 'status', 'Unknown')
        else:
            logger.log(str(self.indexerid) + u": NOT loading info from " + sickbeard.indexerApi(self.indexer).name + " as it is temporarily disabled.", logger.WARNING)

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
                     'last_update': ''}

        i = imdb.IMDb()
        if not self.imdbid:
            self.imdbid = i.title2imdbID(self.name, kind='tv series')

        if self.imdbid:
            logger.log(str(self.indexerid) + u": Loading show info from IMDb", logger.DEBUG)

            imdbTv = i.get_movie(str(re.sub(r"[^0-9]", "", self.imdbid)))

            for key in [x for x in imdb_info.keys() if x.replace('_', ' ') in imdbTv.keys()]:
                # Store only the first value for string type
                if isinstance(imdb_info[key], basestring) and isinstance(imdbTv.get(key.replace('_', ' ')), list):
                    imdb_info[key] = imdbTv.get(key.replace('_', ' '))[0]
                else:
                    imdb_info[key] = imdbTv.get(key.replace('_', ' '))

            # Filter only the value
            if imdb_info['runtimes']:
                imdb_info['runtimes'] = re.search(r'\d+', imdb_info['runtimes']).group(0)
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
                except Exception:
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
                (k.replace(' ', '_'), k(v) if hasattr(v, 'keys') else v) for k, v in imdb_info.iteritems())
            logger.log(str(self.indexerid) + u": Obtained info from IMDb ->" + str(self.imdb_info), logger.DEBUG)

    def nextEpisode(self):
        logger.log(str(self.indexerid) + ": Finding the episode which airs next", logger.DEBUG)

        curDate = datetime.date.today().toordinal()
        if not self.nextaired or self.nextaired and curDate > self.nextaired:
            myDB = db.DBConnection()
            sqlResults = myDB.select(
                "SELECT airdate, season, episode FROM tv_episodes WHERE showid = ? AND airdate >= ? AND status IN (?,?) ORDER BY airdate ASC LIMIT 1",
                [self.indexerid, datetime.date.today().toordinal(), UNAIRED, WANTED])

            if sqlResults == None or len(sqlResults) == 0:
                logger.log(str(self.indexerid) + u": No episode found... need to implement a show status", logger.DEBUG)
                self.nextaired = ""
            else:
                logger.log(u"%s: Found episode S%02dE%02d" % (self.indexerid, sqlResults[0]["season"] or 0, sqlResults[0]["episode"] or 0), logger.DEBUG)
                self.nextaired = sqlResults[0]['airdate']

        return self.nextaired

    def deleteShow(self, full=False):

        sql_l = [["DELETE FROM tv_episodes WHERE showid = ?", [self.indexerid]],
                 ["DELETE FROM tv_shows WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM imdb_info WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM xem_refresh WHERE indexer_id = ?", [self.indexerid]],
                 ["DELETE FROM scene_numbering WHERE indexer_id = ?", [self.indexerid]]]

        myDB = db.DBConnection()
        myDB.mass_action(sql_l)

        action = ('delete', 'trash')[sickbeard.TRASH_REMOVE_SHOW]

        # remove self from show list
        sickbeard.showList = [x for x in sickbeard.showList if int(x.indexerid) != self.indexerid]

        # clear the cache
        image_cache_dir = ek(os.path.join, sickbeard.CACHE_DIR, 'images')
        for cache_file in ek(glob.glob, ek(os.path.join, image_cache_dir, str(self.indexerid) + '.*')):
            logger.log(u'Attempt to %s cache file %s' % (action, cache_file))
            try:
                if sickbeard.TRASH_REMOVE_SHOW:
                    send2trash(cache_file)
                else:
                    os.remove(cache_file)

            except OSError, e:
                logger.log(u'Unable to %s %s: %s / %s' % (action, cache_file, repr(e), str(e)), logger.WARNING)

        # remove entire show folder
        if full:
            try:
                logger.log(u'Attempt to %s show folder %s' % (action, self._location))
                # check first the read-only attribute
                file_attribute = ek(os.stat, self.location)[0]
                if not file_attribute & stat.S_IWRITE:
                    # File is read-only, so make it writeable
                    logger.log(u'Attempting to make writeable the read only folder %s' % self._location, logger.DEBUG)
                    try:
                        ek(os.chmod, self.location, stat.S_IWRITE)
                    except Exception:
                        logger.log(u'Unable to change permissions of %s' % self._location, logger.WARNING)

                if sickbeard.TRASH_REMOVE_SHOW:
                    send2trash(self.location)
                else:
                    ek(shutil.rmtree, self.location)

                logger.log(u'%s show folder %s' %
                           (('Deleted', 'Trashed')[sickbeard.TRASH_REMOVE_SHOW],
                            self._location))

            except ShowDirectoryNotFoundException:
                logger.log(u"Show folder does not exist, no need to %s %s" % (action, self._location), logger.WARNING)
            except OSError, e:
                logger.log(u'Unable to %s %s: %s / %s' % (action, self._location, repr(e), str(e)), logger.WARNING)

        if sickbeard.USE_TRAKT and sickbeard.TRAKT_SYNC_WATCHLIST:
            logger.log(u"Removing show: indexerid " + str(self.indexerid) + ", Title " + str(self.name) + " from Watchlist", logger.DEBUG)
            notifiers.trakt_notifier.update_watchlist(self, update="remove")

    def populateCache(self):
        cache_inst = image_cache.ImageCache()

        logger.log(u"Checking & filling cache for show " + self.name, logger.DEBUG)
        cache_inst.fill_cache(self)

    def refreshDir(self):

        # make sure the show dir is where we think it is unless dirs are created on the fly
        if not ek(os.path.isdir, self._location) and not sickbeard.CREATE_MISSING_SHOW_DIRS:
            return False

        # load from dir
        self.loadEpisodesFromDir()

        # run through all locations from DB, check that they exist
        logger.log(str(self.indexerid) + u": Loading all episodes with a location from the database", logger.DEBUG)

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        sql_l = []
        for ep in sqlResults:
            curLoc = os.path.normpath(ep["location"])
            season = int(ep["season"])
            episode = int(ep["episode"])

            try:
                curEp = self.getEpisode(season, episode)
                if not curEp:
                    raise EpisodeDeletedException
            except EpisodeDeletedException:
                logger.log(u"The episode was deleted while we were refreshing it, moving on to the next one",
                           logger.DEBUG)
                continue

            # if the path doesn't exist or if it's not in our show dir
            if not ek(os.path.isfile, curLoc) or not os.path.normpath(curLoc).startswith(
                    os.path.normpath(self.location)):

                # check if downloaded files still exist, update our data if this has changed
                if not sickbeard.SKIP_REMOVED_FILES:
                    with curEp.lock:
                        # if it used to have a file associated with it and it doesn't anymore then set it to sickbeard.EP_DEFAULT_DELETED_STATUS
                        if curEp.location and curEp.status in Quality.DOWNLOADED:

                            if sickbeard.EP_DEFAULT_DELETED_STATUS == ARCHIVED:
                                _, oldQuality = Quality.splitCompositeStatus(curEp.status)
                                new_status = Quality.compositeStatus(ARCHIVED, oldQuality)
                            else:
                                new_status = sickbeard.EP_DEFAULT_DELETED_STATUS

                            logger.log(u"%s: Location for S%02dE%02d doesn't exist, removing it and changing our status to %s" %
                                       (self.indexerid, season or 0, episode or 0, statusStrings[new_status]), logger.DEBUG)
                            curEp.status = new_status
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
                    with curEp.lock:
                        curEp.airdateModifyStamp()

        if sql_l:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)

    def downloadSubtitles(self, force=False):
        # TODO: Add support for force option
        if not ek(os.path.isdir, self._location):
            logger.log(str(self.indexerid) + ": Show dir doesn't exist, can't download subtitles", logger.DEBUG)
            return

        logger.log(u"%s: Downloading subtitles" % self.indexerid, logger.DEBUG)

        try:
            episodes = self.getAllEpisodes(has_location=True)
            if not episodes:
                logger.log(u"%s: No episodes to download subtitles for %s" % (self.indexerid, self.name), logger.DEBUG)
                return

            for episode in episodes:
                episode.downloadSubtitles(force=force)

        except Exception:
            logger.log(u"%s: Error occurred when downloading subtitles for %s" % (self.indexerid, self.name), logger.DEBUG)
            logger.log(traceback.format_exc(), logger.ERROR)

    def saveToDB(self, forceSave=False):

        if not self.dirty and not forceSave:
            # logger.log(str(self.indexerid) + ": Not saving show to db - record is not dirty", logger.DEBUG)
            return

        logger.log(u"%i: Saving to database: %s" % (self.indexerid, self.name), logger.DEBUG)

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
                        "rls_require_words": self.rls_require_words,
                        "default_ep_status": self.default_ep_status}

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


    def qualitiesToString(self, qualities=[]):
        result = u''
        for quality in qualities:
            if Quality.qualityStrings.has_key(quality):
                result += Quality.qualityStrings[quality] + u', '
            else:
                logger.log(u"Bad quality value: " + str(quality))

        result = re.sub(', $', '', result)

        if not len(result):
            result = u'None'

        return result


    def wantEpisode(self, season, episode, quality, manualSearch=False, downCurQuality=False):

        logger.log(u"Checking if found episode %s S%02dE%02d is wanted at quality %s" % (self.name, season or 0, episode or 0, Quality.qualityStrings[quality]), logger.DEBUG)

        # if the quality isn't one we want under any circumstances then just say no
        anyQualities, bestQualities = Quality.splitQuality(self.quality)
        logger.log(u"Any,Best = [ %s ] [ %s ] Found = [ %s ]" %
                   (self.qualitiesToString(anyQualities),
                    self.qualitiesToString(bestQualities),
                    self.qualitiesToString([quality])), logger.DEBUG)

        if quality not in anyQualities + bestQualities or quality is UNKNOWN:
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
        if epStatus in Quality.ARCHIVED + [UNAIRED, SKIPPED, IGNORED] and not manualSearch:
            logger.log(u"Existing episode status is unaired/skipped/ignored/archived, ignoring found episode", logger.DEBUG)
            return False

        curStatus, curQuality = Quality.splitCompositeStatus(epStatus)

        # if it's one of these then we want it as long as it's in our allowed initial qualities
        if epStatus in (WANTED, SKIPPED, UNKNOWN):
            logger.log(u"Existing episode status is wanted/skipped/unknown, getting found episode", logger.DEBUG)
            return True
        elif manualSearch:
            if (downCurQuality and quality >= curQuality) or (not downCurQuality and quality > curQuality):
                logger.log(
                    u"Usually ignoring found episode, but forced search allows the quality, getting found episode",
                    logger.DEBUG)
                return True

        # if we are re-downloading then we only want it if it's in our bestQualities list and better than what we have, or we only have one bestQuality and we do not have that quality yet
        if epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER and quality in bestQualities and (quality > curQuality or curQuality not in bestQualities):
            logger.log(u"Episode already exists but the found episode quality is wanted more, getting found episode",
                       logger.DEBUG)
            return True
        elif curQuality == Quality.UNKNOWN and manualSearch:
            logger.log(u"Episode already exists but quality is Unknown, getting found episode",
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
        elif epStatus in Quality.ARCHIVED:
            return Overview.GOOD
        elif epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.FAILED + Quality.SNATCHED_BEST:

            _, bestQualities = Quality.splitQuality(self.quality)  # @UnusedVariable
            if bestQualities:
                maxBestQuality = max(bestQualities)
                minBestQuality = min(bestQualities)
            else:
                maxBestQuality = None
                minBestQuality = None

            epStatus, curQuality = Quality.splitCompositeStatus(epStatus)

            if epStatus == FAILED:
                return Overview.WANTED
            if epStatus == DOWNLOADED and curQuality == Quality.UNKNOWN:
                return Overview.QUAL
            elif epStatus in (SNATCHED, SNATCHED_PROPER, SNATCHED_BEST):
                return Overview.SNATCHED
            # if they don't want re-downloads then we call it good if they have anything
            elif maxBestQuality == None:
                return Overview.GOOD
            # if the want only first match and already have one call it good
            elif self.archive_firstmatch and curQuality in bestQualities:
                return Overview.GOOD
            # if they want only first match and current quality is higher than minimal best quality call it good
            elif self.archive_firstmatch and minBestQuality != None and curQuality > minBestQuality:
                return Overview.GOOD
            # if they have one but it's not the best they want then mark it as qual
            elif curQuality < maxBestQuality:
                return Overview.QUAL
            # if it's >= maxBestQuality then it's good
            else:
                return Overview.GOOD

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['lock']
        return d

    def __setstate__(self, d):
        d['lock'] = threading.Lock()
        self.__dict__.update(d)


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
        self._version = 0
        self._release_group = ''

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
        logger.log(u"Setter sets location to " + new_location, logger.DEBUG)

        # self._location = newLocation
        dirty_setter("_location")(self, new_location)

        if new_location and ek(os.path.isfile, new_location):
            self.file_size = ek(os.path.getsize, new_location)
        else:
            self.file_size = 0

    location = property(lambda self: self._location, _set_location)

    def refreshSubtitles(self):
        """Look for subtitles files and refresh the subtitles property"""
        self.subtitles, save_subtitles = subtitles.subtitlesLanguages(self.location)
        if save_subtitles:
            self.saveToDB()

    def downloadSubtitles(self, force=False):
        if not ek(os.path.isfile, self.location):
            logger.log(u"%s: Episode file doesn't exist, can't download subtitles for S%02dE%02d" %
                       (self.show.indexerid, self.season or 0, self.episode or 0), logger.DEBUG)
            return

        logger.log(u"%s: Downloading subtitles for S%02dE%02d" % (self.show.indexerid, self.season or 0, self.episode or 0), logger.DEBUG)

        # logging.getLogger('subliminal.api').addHandler(logging.StreamHandler())
        # logging.getLogger('subliminal.api').setLevel(logging.DEBUG)
        # logging.getLogger('subliminal').addHandler(logging.StreamHandler())
        # logging.getLogger('subliminal').setLevel(logging.DEBUG)

        subtitles_info = {'location': self.location, 'subtitles': self.subtitles, 'show.indexerid': self.show.indexerid, 'season': self.season,
                          'episode': self.episode, 'name': self.name, 'show.name': self.show.name, 'status': self.status}

        self.subtitles, newSubtitles = subtitles.downloadSubtitles(subtitles_info)

        self.subtitles_searchcount += 1 if self.subtitles_searchcount else 1
        self.subtitles_lastsearch = datetime.datetime.now().strftime(dateTimeFormat)
        self.saveToDB()

        if newSubtitles:
            subtitleList = ", ".join([subtitles.fromietf(newSub).name for newSub in newSubtitles])
            logger.log(u"%s: Downloaded %s subtitles for S%02dE%02d" %
                       (self.show.indexerid, subtitleList, self.season or 0, self.episode or 0), logger.DEBUG)

            notifiers.notify_subtitle_download(self.prettyName(), subtitleList)
        else:
            logger.log(u"%s: No subtitles downloaded for S%02dE%02d" %
                       (self.show.indexerid, self.season or 0, self.episode or 0), logger.DEBUG)

    def checkForMetaFiles(self):

        oldhasnfo = self.hasnfo
        oldhastbn = self.hastbn

        cur_nfo = False
        cur_tbn = False

        # check for nfo and tbn
        if ek(os.path.isfile, self.location):
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
            if ek(os.path.isfile, self.location):
                try:
                    self.loadFromNFO(self.location)
                except NoNFOException:
                    logger.log(u"%s: There was an error loading the NFO for episode S%02dE%02d" % (self.show.indexerid, season or 0, episode or 0), logger.ERROR)

                # if we tried loading it from NFO and didn't find the NFO, try the Indexers
                if not self.hasnfo:
                    try:
                        result = self.loadFromIndexer(season, episode)
                    except EpisodeDeletedException:
                        result = False

                    # if we failed SQL *and* NFO, Indexers then fail
                    if not result:
                        raise EpisodeNotFoundException("Couldn't find episode S%02dE%02d" % (season or 0, episode or 0))

    def loadFromDB(self, season, episode):
        logger.log(u"%s: Loading episode details from DB for episode %s S%02dE%02d" % (self.show.indexerid, self.show.name, season or 0, episode or 0), logger.DEBUG)

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                                 [self.show.indexerid, season, episode])

        if len(sqlResults) > 1:
            raise MultipleEpisodesInDatabaseException("Your DB has two records for the same show somehow.")
        elif len(sqlResults) == 0:
            logger.log(u"%s: Episode S%02dE%02d not found in the database" % (self.show.indexerid, self.season or 0, self.episode or 0), logger.DEBUG)
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
            self.status = int(sqlResults[0]["status"] or -1)

            # don't overwrite my location
            if sqlResults[0]["location"] and sqlResults[0]["location"]:
                self.location = os.path.normpath(sqlResults[0]["location"])
            if sqlResults[0]["file_size"]:
                self.file_size = int(sqlResults[0]["file_size"])
            else:
                self.file_size = 0

            self.indexerid = int(sqlResults[0]["indexerid"])
            self.indexer = int(sqlResults[0]["indexer"])

            sickbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

            self.scene_season = helpers.tryInt(sqlResults[0]["scene_season"], 0)
            self.scene_episode = helpers.tryInt(sqlResults[0]["scene_episode"], 0)
            self.scene_absolute_number = helpers.tryInt(sqlResults[0]["scene_absolute_number"], 0)

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

            if sqlResults[0]["release_name"] is not None:
                self.release_name = sqlResults[0]["release_name"]

            if sqlResults[0]["is_proper"]:
                self.is_proper = int(sqlResults[0]["is_proper"])

            if sqlResults[0]["version"]:
                self.version = int(sqlResults[0]["version"])

            if sqlResults[0]["release_group"] is not None:
                self.release_group = sqlResults[0]["release_group"]

            self.dirty = False
            return True

    def loadFromIndexer(self, season=None, episode=None, cache=True, tvapi=None, cachedSeason=None):

        if season is None:
            season = self.season
        if episode is None:
            episode = self.episode

        logger.log(u"%s: Loading episode details from %s for episode S%02dE%02d" %
                   (self.show.indexerid, sickbeard.indexerApi(self.show.indexer).name, season or 0, episode or 0), logger.DEBUG)

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
            logger.log(u"This episode %s - S%02dE%02d has no name on %s. Setting to an empty string" % (self.show.name, season or 0, episode or 0, sickbeard.indexerApi(self.indexer).name))
            setattr(myEp, 'episodename', '')
            # # if I'm incomplete on TVDB but I once was complete then just delete myself from the DB for now
            # if self.indexerid != -1:
            #     self.deleteEpisode()
            # return False

        if getattr(myEp, 'absolute_number', None) is None:
            logger.log(u"This episode %s - S%02dE%02d has no absolute number on %s" %(self.show.name, season or 0, episode or 0, sickbeard.indexerApi(self.indexer).name), logger.DEBUG)
        else:
            logger.log(u"%s: The absolute_number for S%02dE%02d is: %s " % (self.show.indexerid, season or 0, episode or 0, myEp["absolute_number"]), logger.DEBUG)
            self.absolute_number = int(myEp["absolute_number"])

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
            logger.log(u"Malformed air date of %s retrieved from %s for (%s - S%02dE%02d)" % (firstaired, sickbeard.indexerApi(self.indexer).name, self.show.name, season or 0, episode or 0), logger.WARNING)
            # if I'm incomplete on the indexer but I once was complete then just delete myself from the DB for now
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
        if not ek(os.path.isdir, self.show._location) and not sickbeard.CREATE_MISSING_SHOW_DIRS and not sickbeard.ADD_SHOWS_WO_DIR:
            logger.log(u"The show dir %s is missing, not bothering to change the episode statuses since it'd probably be invalid" % self.show._location)
            return

        if self.location:
            logger.log(u"%s: Setting status for S%02dE%02d based on status %s and location %s" %
                       (self.show.indexerid, season or 0, episode or 0, statusStrings[self.status], self.location), logger.DEBUG)

        if not ek(os.path.isfile, self.location):
            if self.airdate >= datetime.date.today() or self.airdate == datetime.date.fromordinal(1):
                logger.log(u"Episode airs in the future or has no airdate, marking it %s" % statusStrings[UNAIRED], logger.DEBUG)
                self.status = UNAIRED
            elif self.status in [UNAIRED, UNKNOWN]:
                # Only do UNAIRED/UNKNOWN, it could already be snatched/ignored/skipped, or downloaded/archived to disconnected media
                logger.log(u"Episode has already aired, marking it %s" % statusStrings[self.show.default_ep_status], logger.DEBUG)
                self.status = self.show.default_ep_status if self.season > 0 else SKIPPED # auto-skip specials
            else:
                logger.log(u"Not touching status [ %s ] It could be skipped/ignored/snatched/archived" % statusStrings[self.status], logger.DEBUG)

        # if we have a media file then it's downloaded
        elif sickbeard.helpers.isMediaFile(self.location):
            # leave propers alone, you have to either post-process them or manually change them back
            if self.status not in Quality.SNATCHED_PROPER + Quality.DOWNLOADED + Quality.SNATCHED + Quality.ARCHIVED:
                logger.log(
                    u"5 Status changes from " + str(self.status) + " to " + str(Quality.statusFromName(self.location)),
                    logger.DEBUG)
                self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

        # shouldn't get here probably
        else:
            logger.log(u"6 Status changes from " + str(self.status) + " to " + str(UNKNOWN), logger.DEBUG)
            self.status = UNKNOWN

    def loadFromNFO(self, location):

        if not ek(os.path.isdir, self.show._location):
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
                        Quality.statusFromName(self.location, anime=self.show.is_anime)), logger.DEBUG)
                    self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

            nfoFile = sickbeard.helpers.replaceExtension(self.location, "nfo")
            logger.log(str(self.show.indexerid) + u": Using NFO name " + nfoFile, logger.DEBUG)

            if ek(os.path.isfile, nfoFile):
                try:
                    showXML = etree.ElementTree(file=nfoFile)
                except (SyntaxError, ValueError), e:
                    logger.log(u"Error loading the NFO, backing up the NFO and skipping for now: " + ex(e), logger.ERROR)
                    try:
                        ek(os.rename, nfoFile, nfoFile + ".old")
                    except Exception, e:
                        logger.log(
                            u"Failed to rename your episode's NFO file - you need to delete it or fix it: " + ex(e), logger.ERROR)
                    raise NoNFOException("Error in NFO format")

                for epDetails in showXML.getiterator('episodedetails'):
                    if epDetails.findtext('season') is None or int(epDetails.findtext('season')) != self.season or \
                       epDetails.findtext('episode') is None or int(epDetails.findtext('episode')) != self.episode:
                        logger.log(u"%s: NFO has an <episodedetails> block for a different episode - wanted S%02dE%02d but got S%02dE%02d" %
                                   (self.show.indexerid, self.season or 0, self.episode or 0, epDetails.findtext('season') or 0, epDetails.findtext('episode') or 0), logger.DEBUG)
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

            if ek(os.path.isfile, sickbeard.helpers.replaceExtension(nfoFile, "tbn")):
                self.hastbn = True
            else:
                self.hastbn = False

    def __str__(self):

        toReturn = u""
        toReturn += u"%r - S%02rE%02r - %r\n" % (self.show.name, self.season, self.episode, self.name)
        toReturn += u"location: %r\n" % self.location
        toReturn += u"description: %r\n" % self.description
        toReturn += u"subtitles: %r\n" % u",".join(self.subtitles)
        toReturn += u"subtitles_searchcount: %r\n" % self.subtitles_searchcount
        toReturn += u"subtitles_lastsearch: %r\n" % self.subtitles_lastsearch
        toReturn += u"airdate: %r (%r)\n" % (self.airdate.toordinal(), self.airdate)
        toReturn += u"hasnfo: %r\n" % self.hasnfo
        toReturn += u"hastbn: %r\n" % self.hastbn
        toReturn += u"status: %r\n" % self.status
        return toReturn

    def createMetaFiles(self):

        if not ek(os.path.isdir, self.show._location):
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

        logger.log(u"Deleting %s S%02dE%02d from the DB" % (self.show.name, self.season or 0, self.episode or 0), logger.DEBUG)

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

        raise EpisodeDeletedException()

    def get_sql(self, forceSave=False):
        """
        Creates SQL queue for this episode if any of its data has been changed since the last save.

        forceSave: If True it will create SQL queue even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """
        try:
            if not self.dirty and not forceSave:
                logger.log(str(self.show.indexerid) + u": Not creating SQL queue - record is not dirty", logger.DEBUG)
                return

            myDB = db.DBConnection()
            rows = myDB.select(
                'SELECT episode_id, subtitles FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?',
                [self.show.indexerid, self.season, self.episode])

            epID = None
            if rows:
                epID = int(rows[0]['episode_id'])

            if epID:
                # use a custom update method to get the data into the DB for existing records.
                # Multi or added subtitle or removed subtitles
                if sickbeard.SUBTITLES_MULTI or not rows[0]['subtitles'] or not self.subtitles:
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
        except Exception as e:
            logger.log(u"Error while updating database: %s" %
                       (repr(e)), logger.ERROR)

    def saveToDB(self, forceSave=False):
        """
        Saves this episode to the database if any of its data has been changed since the last save.

        forceSave: If True it will save to the database even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """

        if not self.dirty and not forceSave:
            # logger.log(str(self.show.indexerid) + u": Not saving episode to db - record is not dirty", logger.DEBUG)
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

        # logger.log(u"%s: Saving episode details to database %rx%r: %s" %
        #            (self.show.indexerid, self.season, self.episode, statusStrings[self.status]), logger.DEBUG)

        # use a custom update/insert method to get the data into the DB
        myDB = db.DBConnection()
        myDB.upsert("tv_episodes", newValueDict, controlValueDict)

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

        multiNameRegex = r"(.*) \(\d{1,2}\)"

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
            if name:
                name = helpers.remove_non_release_groups(helpers.remove_extension(name))
            return name

        def release_group(show, name):
            if name:
                name = helpers.remove_non_release_groups(helpers.remove_extension(name))
            else:
                return ""

            try:
                np = NameParser(name, showObj=show, naming_pattern=True)
                parse_result = np.parse(name)
            except (InvalidNameException, InvalidShowException), e:
                logger.log(u"Unable to get parse release_group: " + ex(e), logger.DEBUG)
                return ''

            if not parse_result.release_group:
                return ''
            return parse_result.release_group

        _, epQual = Quality.splitCompositeStatus(self.status)  # @UnusedVariable

        if sickbeard.NAMING_STRIP_YEAR:
            show_name = re.sub(r"\(\d+\)$", "", self.show.name).rstrip()
        else:
            show_name = self.show.name

        # try to get the release group
        rel_grp = {}
        rel_grp["SiCKRAGE"] = 'SiCKRAGE'
        if hasattr(self, 'location'):  # from the location name
            rel_grp['location'] = release_group(self.show, self.location)
            if not rel_grp['location']:
                del rel_grp['location']
        if hasattr(self, '_release_group'):  # from the release group field in db
            rel_grp['database'] = self._release_group
            if not rel_grp['database']:
                del rel_grp['database']
        if hasattr(self, 'release_name'):  # from the release name field in db
            rel_grp['release_name'] = release_group(self.show, self.release_name)
            if not rel_grp['release_name']:
                del rel_grp['release_name']

        # use release_group, release_name, location in that order
        if 'database' in rel_grp:
            relgrp = 'database'
        elif 'release_name' in rel_grp:
            relgrp = 'release_name'
        elif 'location' in rel_grp:
            relgrp = 'location'
        else: relgrp = 'SiCKRAGE'

        # try to get the release encoder to comply with scene naming standards
        encoder = Quality.sceneQualityFromName(self.release_name.replace(rel_grp[relgrp], ""), epQual)
        if encoder:
            logger.log(u"Found codec for '" + show_name + ": " + ep_name + "'.", logger.DEBUG)

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
            '%RG': rel_grp[relgrp],
            '%CRG': rel_grp[relgrp].upper(),
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

        if sickbeard.NAMING_CUSTOM_ANIME:
            if anime_type == None:
                anime_type = sickbeard.NAMING_ANIME
        else:
            anime_type = 3

        replace_map = self._replace_map()

        result_name = pattern

        # if there's no release group in the db, let the user know we replaced it
        if replace_map['%RG'] and replace_map['%RG'] != 'SiCKRAGE':
            if not hasattr(self, '_release_group'):
                logger.log(u"Episode has no release group, replacing it with '" + replace_map['%RG'] + "'", logger.DEBUG)
                self._release_group = replace_map['%RG']  # if release_group is not in the db, put it there
            elif not self._release_group:
                logger.log(u"Episode has no release group, replacing it with '" + replace_map['%RG'] + "'", logger.DEBUG)
                self._release_group = replace_map['%RG']  # if release_group is not in the db, put it there

        # if there's no release name then replace it with a reasonable facsimile
        if not replace_map['%RN']:

            if self.show.air_by_date or self.show.sports:
                result_name = result_name.replace('%RN', '%S.N.%A.D.%E.N-' + replace_map['%RG'])
                result_name = result_name.replace('%rn', '%s.n.%A.D.%e.n-' + replace_map['%RG'].lower())

            elif anime_type != 3:
                result_name = result_name.replace('%RN', '%S.N.%AB.%E.N-' + replace_map['%RG'])
                result_name = result_name.replace('%rn', '%s.n.%ab.%e.n-' + replace_map['%RG'].lower())

            else:
                result_name = result_name.replace('%RN', '%S.N.S%0SE%0E.%E.N-' + replace_map['%RG'])
                result_name = result_name.replace('%rn', '%s.n.s%0se%0e.%e.n-' + replace_map['%RG'].lower())

            # logger.log(u"Episode has no release name, replacing it with a generic one: " + result_name, logger.DEBUG)

        if not replace_map['%RT']:
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

                ep_string += other_ep._format_string(ep_format.upper(), other_ep._replace_map())

            if anime_type != 3:
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

        anime_type = sickbeard.NAMING_ANIME
        if not self.show.is_anime:
            anime_type = 3

        result = self.formatted_filename(anime_type=anime_type)

        # if they want us to flatten it and we're allowed to flatten it then we will
        if self.show.flatten_folders and not sickbeard.NAMING_FORCE_FOLDERS:
            return result

        # if not we append the folder on and use that
        else:
            result = ek(os.path.join, self.formatted_dir(), result)

        return result

    def formatted_dir(self, pattern=None, multi=None):
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
            elif self.show.anime and sickbeard.NAMING_CUSTOM_ANIME:
                pattern = sickbeard.NAMING_ANIME_PATTERN
            else:
                pattern = sickbeard.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        return helpers.sanitizeFileName(self._format_pattern(name_groups[-1], multi, anime_type))

    def rename(self):
        """
        Renames an episode file and all related files to the location and filename as specified
        in the naming settings.
        """

        if not ek(os.path.isfile, self.location):
            logger.log(u"Can't perform rename on " + self.location + " when it doesn't exist, skipping", logger.WARNING)
            return

        proper_path = self.proper_path()
        absolute_proper_path = ek(os.path.join, self.show.location, proper_path)
        absolute_current_path_no_ext, file_ext = ek(os.path.splitext, self.location)
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
            self.location, base_name_only=True, subfolders=True)

        # This is wrong. Cause of pp not moving subs.
        if self.show.subtitles and sickbeard.SUBTITLES_DIR != '':
            related_subs = postProcessor.PostProcessor(self.location).list_associated_files(sickbeard.SUBTITLES_DIR,
                                                                                            subtitles_only=True, subfolders=True)
            absolute_proper_subs_path = ek(os.path.join, sickbeard.SUBTITLES_DIR, self.formatted_filename())

        logger.log(u"Files associated to " + self.location + ": " + str(related_files), logger.DEBUG)

        # move the ep file
        result = helpers.rename_ep_file(self.location, absolute_proper_path, absolute_current_path_no_ext_length)

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
                logger.log(str(self.indexerid) + u": Unable to rename file " + cur_related_file, logger.ERROR)

        for cur_related_sub in related_subs:
            absolute_proper_subs_path = ek(os.path.join, sickbeard.SUBTITLES_DIR, self.formatted_filename())
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

        if len(sql_l) > 0:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)

    def airdateModifyStamp(self):
        """
        Make the modify date and time of a file reflect the show air date and time.
        Note: Also called from postProcessor

        """

        if not self.show.airs and self.show.network:
            return

        airdate_ordinal = self.airdate.toordinal()
        if airdate_ordinal < 1:
            return

        airdatetime = network_timezones.parse_date_time(airdate_ordinal, self.show.airs, self.show.network)

        if sickbeard.FILE_TIMESTAMP_TIMEZONE == 'local':
            airdatetime = airdatetime.astimezone(network_timezones.sb_timezone)

        filemtime = datetime.datetime.fromtimestamp(os.path.getmtime(self.location)).replace(tzinfo=network_timezones.sb_timezone)

        if filemtime != airdatetime:
            import time

            airdatetime = airdatetime.timetuple()
            logger.log(str(self.show.indexerid) + u": About to modify date of '" + self.location +
                       "' to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime), logger.DEBUG)
            try:
                if helpers.touchFile(self.location, time.mktime(airdatetime)):
                    logger.log(str(self.show.indexerid) + u": Changed modify date of " + os.path.basename(self.location)
                               + " to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))
                else:
                    logger.log(str(self.show.indexerid) + u": Unable to modify date of " + os.path.basename(self.location)
                               + " to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime), logger.ERROR)
            except Exception:
                logger.log(str(self.show.indexerid) + u": Failed to modify date of '" + os.path.basename(self.location)
                           + "' to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime), logger.ERROR)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['lock']
        return d

    def __setstate__(self, d):
        d['lock'] = threading.Lock()
        self.__dict__.update(d)
