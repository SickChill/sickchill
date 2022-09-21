import datetime
import glob
import os.path
import re
import shutil
import stat
import threading
import time
import traceback
from pathlib import Path
from sqlite3 import OperationalError
from weakref import WeakKeyDictionary
from xml.etree import ElementTree

import imdb
from unidecode import unidecode
from urllib3.exceptions import MaxRetryError, NewConnectionError

import sickchill
import sickchill.oldbeard.providers
import sickchill.oldbeard.scene_numbering
from sickchill import logger, settings
from sickchill.helper.common import dateTimeFormat, episode_num, is_media_file, remove_extension, replace_extension, sanitize_filename, try_int
from sickchill.helper.exceptions import (
    EpisodeDeletedException,
    EpisodeNotFoundException,
    MultipleEpisodesInDatabaseException,
    MultipleShowObjectsException,
    MultipleShowsInDatabaseException,
    NoNFOException,
    ShowDirectoryNotFoundException,
    ShowNotFoundException,
)
from sickchill.oldbeard import db, helpers, network_timezones, notifiers, postProcessor, subtitles
from sickchill.oldbeard.blackandwhitelist import BlackAndWhiteList
from sickchill.oldbeard.common import (
    ARCHIVED,
    DOWNLOADED,
    FAILED,
    IGNORED,
    NAMING_DUPLICATE,
    NAMING_EXTEND,
    NAMING_LIMITED_EXTEND,
    NAMING_LIMITED_EXTEND_E_PREFIXED,
    NAMING_SEPARATED_REPEAT,
    Overview,
    Quality,
    SKIPPED,
    SNATCHED,
    SNATCHED_PROPER,
    statusStrings,
    UNAIRED,
    UNKNOWN,
    WANTED,
)
from sickchill.oldbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickchill.show.Show import Show

try:
    from send2trash import send2trash
except ModuleNotFoundError:

    def send2trash(path):
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)


class DirtySetter(object):
    """A descriptor that forbids negative values"""

    def __init__(self, default):
        self.default = default
        self.data = WeakKeyDictionary()

    def __get__(self, instance, owner):
        try:
            return self.data.get(instance, self.default)
        except Exception:
            return None

    def __set__(self, instance, value):
        if value != self.data.get(instance):
            instance.dirty = True

        self.data[instance] = value


class TVShow(object):
    indexerid = DirtySetter(0)
    indexer = DirtySetter(0)
    show_name = DirtySetter("")
    imdb_id = DirtySetter("")
    network = DirtySetter("")
    genre: list = DirtySetter([])
    classification = DirtySetter("")
    runtime = DirtySetter(0)
    imdb_info = DirtySetter({})
    quality = DirtySetter(int(settings.QUALITY_DEFAULT))
    season_folders = DirtySetter(int(settings.SEASON_FOLDERS_DEFAULT))
    status = DirtySetter("Unknown")
    airs = DirtySetter("")
    startyear = DirtySetter(0)
    paused = DirtySetter(0)
    air_by_date = DirtySetter(0)
    subtitles = DirtySetter(int(settings.SUBTITLES_DEFAULT))
    subtitles_sr_metadata = DirtySetter(0)
    dvdorder = DirtySetter(0)
    lang = DirtySetter("en")
    last_update_indexer = DirtySetter(1)
    sports = DirtySetter(0)
    anime = DirtySetter(0)
    scene = DirtySetter(0)
    rls_ignore_words = DirtySetter("")
    rls_require_words = DirtySetter("")
    rls_prefer_words = DirtySetter("")
    default_ep_status = DirtySetter(SKIPPED)
    custom_name = DirtySetter("")

    def __init__(self, indexer, indexerid: int, lang=""):
        self.dirty = True

        self.lock = threading.Lock()
        self.episodes = {}
        self.nextaired = ""
        self.release_groups = None
        self._location = ""
        self.indexer = indexer
        self.indexerid = indexerid
        self.lang = lang

        otherShow = Show.find(settings.showList, self.indexerid)
        if otherShow is not None:
            raise MultipleShowObjectsException("Can't create a show if it already exists")

        self.loadFromDB()

    @property
    def name(self):
        return self.custom_name or self.show_name

    @name.setter
    def name(self, name):
        self.show_name = name

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

    @property
    def idxr(self):
        return sickchill.indexer[self.indexer]

    @property
    def indexer_name(self):
        return self.idxr.name

    @property
    def network_image_url(self):
        return f"images/network/{unidecode(self.network or 'nonetwork').lower()}.png"

    def show_image_url(self, which):
        return settings.IMAGE_CACHE.image_url(self.indexerid, which)

    def _getLocation(self):
        # no dir check needed if missing show dirs are created during post-processing
        if settings.CREATE_MISSING_SHOW_DIRS or os.path.isdir(self._location):
            return self._location

        raise ShowDirectoryNotFoundException("Show folder doesn't exist, you shouldn't be using it")

    def _setLocation(self, newLocation):
        logger.debug(f"Setter sets location to {newLocation}")
        # Don't validate dir if user wants to add shows without creating a dir
        if settings.ADD_SHOWS_WO_DIR or os.path.isdir(newLocation):
            if self._location != newLocation:
                self.dirty = True
            self._location = newLocation
        else:
            raise NoNFOException("Invalid folder for the show!")

    location = property(_getLocation, _setLocation)

    def flushEpisodes(self):

        for curSeason in self.episodes:
            self.episodes[curSeason].clear()

        self.episodes.clear()

    def getAllEpisodes(self, season=None, has_location=False):

        # detect multi-episodes
        sql_selection = "SELECT season, episode, "
        sql_selection += "(SELECT COUNT (*) FROM tv_episodes WHERE showid = tve.showid "
        sql_selection += "AND season = tve.season AND location != '' AND location = tve.location "
        sql_selection += "AND episode != tve.episode) AS share_location "
        sql_selection += f"FROM tv_episodes tve WHERE showid = {self.indexerid} "

        if season is not None:
            sql_selection += f"AND season = {season} "

        if has_location:
            sql_selection += "AND location != '' "

        # need ORDER episode ASC to rename multi-episodes in order S01E01-02
        sql_selection += "ORDER BY season ASC, episode ASC "

        main_db_con = db.DBConnection()
        results = main_db_con.select(sql_selection)

        ep_list = []
        for cur_result in results:
            cur_ep = self.getEpisode(cur_result["season"], cur_result["episode"])
            if not cur_ep:
                continue

            cur_ep.relatedEps = []
            if cur_ep.location:
                # if there is a location, check if it's a multi-episode and put them in relatedEps
                if cur_result["share_location"] > 0:
                    related_eps_result = main_db_con.select(
                        "SELECT season, episode FROM tv_episodes WHERE showid = ? AND season = ? AND location = ? AND episode != ? ORDER BY episode",
                        [self.indexerid, cur_ep.season, cur_ep.location, cur_ep.episode],
                    )
                    for cur_related_ep in related_eps_result:
                        related_ep = self.getEpisode(cur_related_ep["season"], cur_related_ep["episode"])
                        if related_ep and related_ep not in cur_ep.relatedEps:
                            cur_ep.relatedEps.append(related_ep)
            ep_list.append(cur_ep)

        return ep_list

    def getEpisode(self, season=None, episode=None, ep_file=None, noCreate=False, absolute_number=None):
        season = try_int(season, None)
        episode = try_int(episode, None)
        absolute_number = try_int(absolute_number, None)

        if season in self.episodes and episode in self.episodes[season] and self.episodes[season][episode]:
            return self.episodes[season][episode]

        # if we get an anime get the real season and episode
        if self.is_anime and absolute_number and not season and not episode:
            main_db_con = db.DBConnection()
            sql = "SELECT season, episode FROM tv_episodes WHERE showid = ? AND absolute_number = ? AND season != 0"
            sql_results = main_db_con.select(sql, [self.indexerid, absolute_number])

            if len(sql_results) == 1:
                episode = int(sql_results[0]["episode"])
                season = int(sql_results[0]["season"])
                logger.debug("Found episode by absolute number {absolute} which is {ep}".format(absolute=absolute_number, ep=episode_num(season, episode)))
            elif len(sql_results) > 1:
                logger.error("Multiple entries for absolute number: {absolute} in show: {name} found ".format(absolute=absolute_number, name=self.name))

                return None
            else:
                logger.debug(f"No entries for absolute number: {absolute_number} in show: {self.name} found.")
                return None

        if season not in self.episodes:
            self.episodes[season] = {}

        if not self.episodes[season].get(episode):
            if noCreate:
                return None

            if ep_file:
                ep = TVEpisode(self, season, episode, ep_file)
            else:
                ep = TVEpisode(self, season, episode)

            if ep:
                self.episodes[season][episode] = ep

        return self.episodes[season][episode]

    def should_update(self, update_date=datetime.date.today()):
        """
        Check current show last and next episode air date
        Decide if we should update Ended status
        """

        # if show is not 'Ended' always update (status 'Continuing')
        if self.status == "Continuing":
            return True

        graceperiod = datetime.timedelta(days=30)

        last_airdate = datetime.date.min

        # get the last aired episode and compare against grace period
        main_db_con = db.DBConnection()
        sql_result = main_db_con.select(
            "SELECT IFNULL(MAX(airdate), 0) as last_aired FROM tv_episodes WHERE showid = ? AND season > 0 AND airdate > 1 AND status > 1", [self.indexerid]
        )

        if sql_result and sql_result[0]["last_aired"] != 0:
            last_airdate = datetime.date.fromordinal(sql_result[0]["last_aired"])
            if (update_date - graceperiod) <= last_airdate <= (update_date + graceperiod):
                return True

        # get next unaired episode and compare against grace period
        sql_result = main_db_con.select(
            "SELECT IFNULL(MIN(airdate), 0) as airing_next FROM tv_episodes WHERE showid = ? AND season > 0 AND airdate > 1 AND status = 1", [self.indexerid]
        )

        if sql_result and sql_result[0]["airing_next"] != 0:
            next_airdate = datetime.date.fromordinal(sql_result[0]["airing_next"])
            if next_airdate <= (update_date + graceperiod):
                return True

        last_update_indexer = datetime.date.fromordinal(self.last_update_indexer)

        # Check between 30 and 450 days
        if (update_date - last_airdate) < datetime.timedelta(days=450) and (update_date - last_update_indexer) > datetime.timedelta(days=30):
            return True

        return False

    def writeShowNFO(self):

        result = False

        if not os.path.isdir(self._location):
            logger.info(f"{self.indexerid}: Show dir doesn't exist, skipping NFO generation")
            return False

        logger.debug(f"{self.indexerid}: Writing NFOs for show")
        for cur_provider in settings.metadata_provider_dict.values():
            result = cur_provider.create_show_metadata(self) or result

        return result

    def writeMetadata(self, show_only=False):

        if not os.path.isdir(self._location):
            logger.info(f"{self.indexerid}: Show dir doesn't exist, skipping NFO generation")
            return

        self.getImages()

        self.writeShowNFO()

        if not show_only:
            self.writeEpisodeNFOs()

    def writeEpisodeNFOs(self):

        if not os.path.isdir(self._location):
            logger.info(f"{self.indexerid}: Show dir doesn't exist, skipping NFO generation")
            return

        logger.debug(f"{self.indexerid}: Writing NFOs for all episodes")

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT season, episode FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        for epResult in sql_results:
            logger.debug("{id}: Retrieving/creating episode {ep}".format(id=self.indexerid, ep=episode_num(epResult["season"], epResult["episode"])))
            curEp = self.getEpisode(epResult["season"], epResult["episode"])
            if not curEp:
                continue

            curEp.createMetaFiles()

    def updateMetadata(self):

        if not os.path.isdir(self._location):
            logger.info(f"{self.indexerid}: Show dir doesn't exist, skipping NFO generation")
            return

        result = False

        if not os.path.isdir(self._location):
            logger.info(f"{self.indexerid}: Show dir doesn't exist, skipping NFO generation")
            return False

        logger.info(f"{self.indexerid}: Updating NFOs for show with new indexer info")
        for cur_provider in settings.metadata_provider_dict.values():
            result = cur_provider.update_show_indexer_metadata(self) or result

        return result

    def loadEpisodesFromDir(self):
        """Find all media files in the show folder and create episodes"""

        if not os.path.isdir(self._location):
            logger.debug(f"{self.indexerid}: Show dir doesn't exist, not loading episodes from disk")
            return

        logger.debug(f"{self.indexerid}: Loading all episodes from the show directory {self._location}")

        media_files = helpers.list_media_files(self._location)

        # create TVEpisodes from each media file if possible
        sql_l = []
        for media_file in media_files:
            logger.debug("{tvdbid}: Creating episode from {filename}".format(tvdbid=str(self.indexerid), filename=os.path.basename(media_file)))
            curEpisode = None
            try:
                curEpisode = self.makeEpFromFile(media_file)
            except (ShowNotFoundException, EpisodeNotFoundException) as error:
                media_file_name = os.path.basename(media_file)
                logger.error(f"Episode {media_file_name} returned an exception: {error}")
                continue
            except EpisodeDeletedException:
                logger.debug("The episode deleted itself when I tried making an object for it")

            if curEpisode is None:
                continue

            # see if we should save the release name in the db
            ep_filename = os.path.basename(curEpisode.location)
            ep_filename = os.path.splitext(ep_filename)[0]

            try:
                parse_result = NameParser(False, showObj=self, tryIndexers=True).parse(ep_filename)
            except (InvalidNameException, InvalidShowException):
                parse_result = None

            if " " not in ep_filename and parse_result and parse_result.release_group:
                logger.debug(f"Name {ep_filename} gave release group of {parse_result.release_group}, seems valid")
                curEpisode.release_name = ep_filename
                curEpisode.release_group = parse_result.release_group

            # store the reference in the show
            if curEpisode is not None:
                if self.subtitles:
                    try:
                        curEpisode.refreshSubtitles()
                    except Exception:
                        logger.error(f"{self.indexerid}: Could not refresh subtitles")
                        logger.debug(traceback.format_exc())

                sql_l.append(curEpisode.get_sql())

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

    def loadEpisodesFromDB(self):

        logger.debug("Loading all episodes from the database")
        scannedEps = {}

        try:
            main_db_con = db.DBConnection()
            sql = "SELECT season, episode, showid, show_name FROM tv_episodes JOIN tv_shows WHERE showid = indexer_id and showid = ?"
            sql_results = main_db_con.select(sql, [self.indexerid])
        except OperationalError as error:
            logger.error(f"Could not load episodes from the DB. Error: {error}")
            return scannedEps

        curShowid = None
        curShowName = None

        for curResult in sql_results:

            curSeason = int(curResult["season"])
            curEpisode = int(curResult["episode"])
            curShowid = int(curResult["showid"])
            curShowName = str(curResult["show_name"])

            if curSeason not in scannedEps:
                logger.debug("{id}: Not curSeason in scannedEps".format(id=curShowid))
                scannedEps[curSeason] = {}

            logger.debug("{id}: Loading {show} {ep} from the DB".format(id=curShowid, show=curShowName, ep=episode_num(curSeason, curEpisode)))

            try:
                curEp = self.getEpisode(curSeason, curEpisode)
                if not curEp:
                    raise EpisodeNotFoundException

                curEp.loadFromDB(curSeason, curEpisode)
                scannedEps[curSeason][curEpisode] = True
            except EpisodeDeletedException:
                logger.debug(
                    "{id}: Tried loading {show} {ep} from the DB that should have been deleted, skipping it".format(
                        id=curShowid, show=curShowName, ep=episode_num(curSeason, curEpisode)
                    )
                )
                continue

        if curShowName and curShowid:
            logger.debug("{id}: Finished loading all episodes for {show} from the DB".format(show=curShowName, id=curShowid))

        return scannedEps

    def loadEpisodesFromIndexer(self):
        logger.debug(_("{show_id}: Loading all episodes from {indexer_name}...").format(show_id=self.indexerid, indexer_name=self.indexer_name))

        scannedEps = {}

        for series_episode in self.idxr.episodes(self):
            if series_episode["airedSeason"] not in scannedEps:
                scannedEps[series_episode["airedSeason"]] = {}

            season_episode = series_episode["airedSeason"], series_episode["airedEpisodeNumber"]
            try:
                show_episode = self.getEpisode(*season_episode)
                if not show_episode:
                    raise EpisodeNotFoundException
            except EpisodeNotFoundException:
                logger.info(
                    "{id}: {indexer} object for {ep} is incomplete, skipping this episode".format(
                        id=self.indexerid, indexer=self.indexer_name, ep=episode_num(*season_episode)
                    )
                )
                continue
            else:
                try:
                    with show_episode.lock:
                        show_episode.loadFromIndexer(*season_episode)
                        show_episode.saveToDB()
                        # sql_l.append(show_episode.get_sql())
                except EpisodeDeletedException:
                    logger.info("The episode was deleted, skipping the rest of the load")
                    continue

            scannedEps[series_episode["airedSeason"]][series_episode["airedEpisodeNumber"]] = True

        # Done updating save last update date
        self.last_update_indexer = datetime.datetime.now().toordinal()

        self.saveToDB()

        return scannedEps

    def getImages(self):
        fanart_result = poster_result = banner_result = False
        season_posters_result = season_banners_result = season_all_poster_result = season_all_banner_result = False

        for cur_provider in settings.metadata_provider_dict.values():

            fanart_result = cur_provider.create_fanart(self) or fanart_result
            poster_result = cur_provider.create_poster(self) or poster_result
            banner_result = cur_provider.create_banner(self) or banner_result

            season_posters_result = cur_provider.create_season_posters(self) or season_posters_result
            season_banners_result = cur_provider.create_season_banners(self) or season_banners_result
            season_all_poster_result = cur_provider.create_season_all_poster(self) or season_all_poster_result
            season_all_banner_result = cur_provider.create_season_all_banner(self) or season_all_banner_result

        return (
            fanart_result
            or poster_result
            or banner_result
            or season_posters_result
            or season_banners_result
            or season_all_poster_result
            or season_all_banner_result
        )

    def makeEpFromFile(self, filepath):
        """make a TVEpisode object from a media file"""

        if not os.path.isfile(filepath):
            logger.info(f"{self.indexerid}: That isn't even a real file dude... {filepath}")
            return None

        logger.debug(f"{self.indexerid}: Creating episode object from {filepath}")

        try:
            parse_result = NameParser(showObj=self, tryIndexers=True, parse_method=("normal", "anime")[self.is_anime]).parse(filepath, True, True)
        except (InvalidNameException, InvalidShowException) as error:
            logger.debug(f"{self.indexerid}: {error}")
            return None

        episodes = [ep for ep in parse_result.episode_numbers if ep is not None]
        if not episodes:
            logger.info(f"{self.indexerid}: parse_result: {parse_result}")
            logger.info(f"{self.indexerid}: No episode number found in {filepath}, ignoring it")
            return None

        # for now let's assume that any episode in the show dir belongs to that show
        season = parse_result.season_number if parse_result.season_number is not None else 1
        rootEp = None

        sql_l = []
        for current_ep in episodes:
            logger.debug(f"{self.indexerid}: {filepath} parsed to {self.name} {episode_num(season, current_ep)}")

            checkQualityAgain = False
            same_file = False

            curEp = self.getEpisode(season, current_ep)
            if not curEp:
                try:
                    curEp = self.getEpisode(season, current_ep, filepath)
                    if not curEp:
                        raise EpisodeNotFoundException
                except EpisodeNotFoundException:
                    logger.error(f"{self.indexerid}: Unable to figure out what this file is, skipping {filepath}")
                    continue

            else:
                # if there is a new file associated with this ep then re-check the quality
                if curEp.location and os.path.normpath(curEp.location) != os.path.normpath(filepath):
                    logger.debug(
                        f"{self.indexerid}: The old episode had a different file associated with it, "
                        f"re-checking the quality using the new filename {filepath}"
                    )
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
                    curEp.release_name = ""
                    curEp.release_group = ""

            # if they replace a file on me I'll make some attempt at re-checking the quality unless I know it's the same file
            if checkQualityAgain and not same_file:
                newQuality = Quality.nameQuality(filepath, self.is_anime)
                logger.debug(f"{self.indexerid}: Since this file has been renamed, I checked {filepath} and found quality {Quality.qualityStrings[newQuality]}")

                with curEp.lock:
                    curEp.status = Quality.compositeStatus(DOWNLOADED, newQuality)

            # check for status/quality changes as long as it's a new file
            elif not same_file and is_media_file(filepath) and curEp.status not in Quality.DOWNLOADED + Quality.ARCHIVED + [IGNORED]:
                oldStatus, oldQuality = Quality.splitCompositeStatus(curEp.status)
                newQuality = Quality.nameQuality(filepath, self.is_anime)

                newStatus = None

                # if it was snatched and now exists then set the status correctly
                if oldStatus == SNATCHED and oldQuality <= newQuality:
                    logger.debug(
                        f"{self.indexerid}: This ep used to be snatched with quality {Quality.qualityStrings[oldQuality]} but a "
                        f"file exists with quality {Quality.qualityStrings[newQuality]} so I'm setting the status to DOWNLOADED"
                    )
                    newStatus = DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif oldStatus == SNATCHED_PROPER and oldQuality < newQuality:
                    logger.debug(
                        f"{self.indexerid}: This ep used to be snatched proper with quality {Quality.qualityStrings[oldQuality]} "
                        f"but a file exists with quality {Quality.qualityStrings[newQuality]} so I'm setting the status to DOWNLOADED"
                    )
                    newStatus = DOWNLOADED

                elif oldStatus not in (SNATCHED, SNATCHED_PROPER):
                    newStatus = DOWNLOADED

                if newStatus is not None:
                    with curEp.lock:
                        logger.debug(
                            f"{self.indexerid}: We have an associated file, so setting the status from {curEp.status} "
                            f"to DOWNLOADED/{Quality.statusFromName(filepath, anime=self.is_anime)}"
                        )
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

    def loadFromDB(self):
        """Get Indexer information from database"""

        main_db_con = db.DBConnection(row_type="dict")
        sql_results = main_db_con.select("SELECT * FROM tv_shows WHERE indexer_id = ?", [self.indexerid])

        if len(sql_results) > 1:
            raise MultipleShowsInDatabaseException()
        elif not sql_results:
            return
        else:
            self.indexer = int(sql_results[0]["indexer"] or 0)

            if not self.show_name:
                self.name = sql_results[0]["show_name"]
            if not self.custom_name:
                self.custom_name = sql_results[0]["custom_name"]
            if not self.network:
                self.network = sql_results[0]["network"]
            if not self.genre:
                self.genre = [x.strip() for x in sql_results[0]["genre"].split("|") if x.strip()]

            if not self.classification:
                self.classification = sql_results[0]["classification"]

            self.runtime = sql_results[0]["runtime"]

            self.status = sql_results[0]["status"]
            if self.status is None:
                self.status = "Unknown"

            self.airs = sql_results[0]["airs"]
            if self.airs is None:
                self.airs = ""

            self.startyear = int(sql_results[0]["startyear"] or 0)
            self.air_by_date = int(sql_results[0]["air_by_date"] or 0)
            self.anime = int(sql_results[0]["anime"] or 0)
            self.sports = int(sql_results[0]["sports"] or 0)
            self.scene = int(sql_results[0]["scene"] or 0)
            self.subtitles = int(sql_results[0]["subtitles"] or 0)
            self.dvdorder = int(sql_results[0]["dvdorder"] or 0)
            self.quality = int(sql_results[0]["quality"] or UNKNOWN)
            self.season_folders = int(not int(sql_results[0]["flatten_folders"] or 0))
            self.paused = int(sql_results[0]["paused"] or 0)
            self.paused = int(sql_results[0]["paused"] or 0)

            self._location = sql_results[0]["location"]

            if not self.lang:
                self.lang = sql_results[0]["lang"]

            self.last_update_indexer = sql_results[0]["last_update_indexer"]

            self.rls_ignore_words = sql_results[0]["rls_ignore_words"]
            self.rls_require_words = sql_results[0]["rls_require_words"]
            self.rls_prefer_words = sql_results[0]["rls_prefer_words"]

            self.default_ep_status = int(sql_results[0]["default_ep_status"] or SKIPPED)

            if not self.imdb_id:
                self.imdb_id = sql_results[0]["imdb_id"]

            if self.is_anime:
                self.release_groups = BlackAndWhiteList(self.indexerid)

            self.subtitles_sr_metadata = int(sql_results[0]["sub_use_sr_metadata"] or 0)

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT * FROM imdb_info WHERE indexer_id = ?", [self.indexerid])

        if not sql_results:
            self.load_imdb_info()
            sql_results = main_db_con.select("SELECT * FROM imdb_info WHERE indexer_id = ?", [self.indexerid])
            if not sql_results:
                logger.info(f"{self.indexerid}: Unable to find IMDb show info in the database")
                return

        self.imdb_info = dict(zip(sql_results[0].keys(), sql_results[0]))
        self.dirty = False
        return True

    def loadFromIndexer(self):
        logger.debug(f"{self.indexerid}: Loading show info from {self.indexer_name}")

        myShow = sickchill.indexer.series(self)
        if not myShow or not getattr(myShow, "seriesName"):
            raise AttributeError(f"Found {self.indexerid}, but attribute 'seriesName' was empty.")

        self.name = myShow.seriesName.strip()
        self.classification = getattr(myShow, "classification", "Scripted")
        self.genre = getattr(myShow, "genre", [])
        self.network = getattr(myShow, "network", "")
        self.runtime = getattr(myShow, "runtime", "")

        self.imdb_id = getattr(myShow, "imdbId", "")

        if hasattr(myShow, "airsDayOfWeek") and hasattr(myShow, "airsTime"):
            if myShow.airsTime and myShow.airsDayOfWeek:
                self.airs = f"{myShow.airsDayOfWeek} {myShow.airsTime}".strip()
            else:
                self.airs = self.airs.strip() if self.airs else ""

        if self.airs is None:
            self.airs = ""

        if hasattr(myShow, "firstAired") and myShow.firstAired:
            self.startyear = int(myShow.firstAired.split("-")[0])

        self.status = getattr(myShow, "status", "Unknown")

    def check_imdb_id(self):
        if self.imdb_id:
            self.imdb_id = re.sub(r"[^\d]", "", self.imdb_id)

        if self.imdb_id:
            self.imdb_id = "tt" + self.imdb_id

        try:
            int(self.imdb_id.lstrip("t"))
        except (ValueError, TypeError, AttributeError):
            self.imdb_id = ""

    def load_imdb_info(self):
        try:
            client = imdb.IMDb()

            # Check that the imdb_id we have is valid for searching
            self.check_imdb_id()

            if self.name and not self.imdb_id:
                # Add regular name and custom name to be searched first
                attempts = {self.show_name}
                if self.custom_name:
                    attempts.add(self.custom_name)

                # Now the generated name/year search string types for normal name
                attempts.update({f"{self.show_name} ({self.startyear})", f'"{self.show_name}" ({self.startyear})'})

                if self.custom_name:
                    # Now the generated name/year search string types for custom name
                    attempts.update({f"{self.custom_name} ({self.startyear})", f'"{self.custom_name}" ({self.startyear})'})

                for attempt in attempts:
                    results = [x for x in client.search_movie(attempt) if x["kind"] == "tv series" and x["title"] == attempt]
                    if self.startyear:
                        results = [x for x in results if x["year"] == self.startyear]
                    if len(results) == 1:
                        self.imdb_id = results[0]["imdbID"]

                    if self.imdb_id:
                        break

            # Make sure the lib didn't give us back something bogus
            self.check_imdb_id()

            if not self.imdb_id:
                logger.debug(f"{self.indexerid}: Not loading show info from IMDb, because we don't know the imdb_id")
                return

            logger.debug(f"{self.indexerid}: Loading show info from IMDb")
            imdb_title: dict = client.get_movie(self.imdb_id.strip("t"))

            self.imdb_info = {
                "indexer_id": self.indexerid,
                "imdb_id": imdb_title.setdefault("imdbID", self.imdb_id),
                "title": imdb_title.setdefault("title", self.name),
                "year": imdb_title.setdefault("year", self.startyear),
                "akas": "|".join(imdb_title.setdefault("akas", [])),
                "runtimes": imdb_title.setdefault("runtimes", [self.runtime])[0],
                "genres": "|".join(imdb_title.setdefault("genres", [])),
                "countries": "|".join(imdb_title.get("countries", [])),
                "country_codes": "|".join(imdb_title.get("country codes", [])),
                "certificates": "|".join(imdb_title.setdefault("certificates", [])),
                "rating": str(imdb_title.setdefault("rating", 0.0)),
                "votes": str(imdb_title.setdefault("votes", 0)),
                "last_update": datetime.date.today().toordinal(),
            }

            logger.debug(f"{self.indexerid}: Obtained info from IMDb ->{self.imdb_info}")
        except (ValueError, LookupError, OperationalError, imdb.IMDbError, NewConnectionError, MaxRetryError) as error:
            logger.info(f"Could not get IMDB info: {error}")
        except (SyntaxError, KeyError):
            logger.info("Could not get info from IDMb, pip install lxml")

    def nextEpisode(self):
        curDate = datetime.date.today().toordinal()
        if not self.nextaired or self.nextaired and curDate > self.nextaired:
            main_db_con = db.DBConnection()
            sql_results = main_db_con.select(
                "SELECT airdate, season, episode FROM tv_episodes WHERE showid = ? AND airdate >= ? AND status IN (?,?) ORDER BY airdate LIMIT 1",
                [self.indexerid, datetime.date.today().toordinal(), UNAIRED, WANTED],
            )

            self.nextaired = sql_results[0]["airdate"] if sql_results else ""

        return self.nextaired

    def deleteShow(self, full=False):
        main_db_con = db.DBConnection()

        episodes_locations = main_db_con.select("SELECT location FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        sql_l = [
            ["DELETE FROM tv_episodes WHERE showid = ?", [self.indexerid]],
            ["DELETE FROM tv_shows WHERE indexer_id = ?", [self.indexerid]],
            ["DELETE FROM imdb_info WHERE indexer_id = ?", [self.indexerid]],
            ["DELETE FROM xem_refresh WHERE indexer_id = ?", [self.indexerid]],
            ["DELETE FROM scene_numbering WHERE indexer_id = ?", [self.indexerid]],
            ["DELETE FROM history WHERE showid = ?", [self.indexerid]],
            ["DELETE FROM indexer_mapping WHERE indexer_id = ?", [self.indexerid]],
            ["DELETE FROM blacklist WHERE show_id = ?", [self.indexerid]],
            ["DELETE FROM whitelist WHERE show_id = ?", [self.indexerid]],
        ]

        main_db_con.mass_action(sql_l)

        cache_db_con = db.DBConnection("cache.db")
        sql_l = [["DELETE FROM scene_exceptions WHERE indexer_id = ?", [self.indexerid]], ["DELETE FROM scene_names WHERE indexer_id = ?", [self.indexerid]]]

        cache_db_con.mass_action(sql_l)

        for provider in sickchill.oldbeard.providers.__all__:
            if cache_db_con.has_table(provider) and cache_db_con.has_column(provider, "indexerid"):
                cache_db_con.action("delete from {} WHERE indexerid = ?".format(provider), [self.indexerid])

        failed_db_con = db.DBConnection("failed.db")
        sql_l = [
            ["DELETE FROM history WHERE showid = ?", [self.indexerid]],
        ]

        failed_db_con.mass_action(sql_l)

        action = ("delete", "trash")[settings.TRASH_REMOVE_SHOW]

        # remove self from show list
        settings.showList = [x for x in settings.showList if int(x.indexerid) != self.indexerid]

        # clear the cache
        image_cache_dir = os.path.join(settings.CACHE_DIR, "images")
        for cache_file in glob.glob(os.path.join(glob.escape(image_cache_dir), f"{self.indexerid}.*")):
            logger.info(f"Attempt to {action} cache file {cache_file}")
            try:
                if settings.TRASH_REMOVE_SHOW:
                    send2trash(cache_file)
                else:
                    os.remove(cache_file)

            except OSError as error:
                logger.warning(f"Unable to {action} {cache_file}: {error}")

        # remove entire show folder
        if full:
            try:
                logger.info(f"Attempt to {action} show folder {self._location}")
                # check first the read-only attribute
                file_attribute = os.stat(self.location)[0]
                if not file_attribute & stat.S_IWRITE:
                    # File is read-only, so make it writeable
                    logger.debug(f"Attempting to make writeable the read only folder {self._location}")
                    try:
                        os.chmod(self.location, stat.S_IWRITE)
                    except OSError as error:
                        logger.warning(f"Unable to change permissions of {self._location}: {error}")

                shows_in_folder = main_db_con.select(
                    "SELECT location from tv_shows WHERE location LIKE ? AND indexer_id != ?", ["{}%".format(self.location), self.indexerid]
                )

                num_shows_in_folder = len(shows_in_folder)
                if num_shows_in_folder:
                    logger.info(
                        "Cannot delete the show folder from disk, because this location is the root dir for {num} other shows!".format(num=num_shows_in_folder)
                    )
                    logger.info("Deleting individual episodes. There may be some related files or folders left behind afterwards.")
                    for ep_file in episodes_locations:
                        path_ep_file = Path(ep_file["location"])
                        for show_file in path_ep_file.parent.glob(f"{path_ep_file.stem}.*"):
                            logger.info(f"Attempt to {action} related file {show_file}")
                            try:
                                if settings.TRASH_REMOVE_SHOW:
                                    send2trash(show_file)
                                else:
                                    os.remove(show_file)
                            except OSError as error:
                                logger.warning(f"Unable to {action} {show_file}: {error}")
                else:
                    if settings.TRASH_REMOVE_SHOW:
                        send2trash(self.location)
                    else:
                        shutil.rmtree(self.location)

                    action_string = ("Deleted", "Trashed")[settings.TRASH_REMOVE_SHOW]
                    logger.info(f"{action_string} show folder {self._location}")

            except ShowDirectoryNotFoundException:
                logger.warning(f"Show folder does not exist, no need to {action} {self._location}")
            except OSError as error:
                logger.warning(f"Unable to {action} {self._location}: {error}")

        if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
            logger.debug(f"Removing show: indexerid {self.indexerid}, Title {self.name} from Watchlist")
            notifiers.trakt_notifier.update_watchlist(self, update="remove")

    def populateCache(self):
        logger.debug(f"Checking & filling cache for show {self.name}")
        settings.IMAGE_CACHE.fill_cache(self)

    def refreshDir(self):

        if not os.path.isdir(self._location) and not settings.CREATE_MISSING_SHOW_DIRS:
            logger.info(
                "Show dir does not exist, and `create missing show dirs` is disabled. Skipping refresh (statuses will not be updated): {}".format(
                    self._location
                )
            )
            return False

        # load from dir
        self.loadEpisodesFromDir()

        # run through all locations from DB, check that they exist
        logger.debug(f"{self.indexerid}: Loading all episodes with a location from the database")

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT season, episode, location FROM tv_episodes WHERE showid = ? AND location != ''", [self.indexerid])

        sql_l = []
        for ep in sql_results:
            curLoc = os.path.normpath(ep["location"])
            season = int(ep["season"])
            episode = int(ep["episode"])

            try:
                curEp = self.getEpisode(season, episode)
                if not curEp:
                    raise EpisodeDeletedException
            except EpisodeDeletedException:
                logger.debug("The episode was deleted while we were refreshing it, moving on to the next one")
                continue

            # if the path doesn't exist or if it's not in our show dir
            if not os.path.isfile(curLoc) or not os.path.normpath(curLoc).startswith(os.path.normpath(self._location)):

                # check if downloaded files still exist, update our data if this has changed
                if not settings.SKIP_REMOVED_FILES:
                    with curEp.lock:
                        # if it used to have a file associated with it and it doesn't anymore then set it to oldbeard.EP_DEFAULT_DELETED_STATUS
                        if curEp.status in Quality.DOWNLOADED:

                            if settings.EP_DEFAULT_DELETED_STATUS == ARCHIVED:
                                oldStatus_, oldQuality = Quality.splitCompositeStatus(curEp.status)
                                new_status = Quality.compositeStatus(ARCHIVED, oldQuality)
                            else:
                                new_status = settings.EP_DEFAULT_DELETED_STATUS

                            logger.debug(
                                "{id}: Location for {ep} doesn't exist, removing it and changing our status to {status}".format(
                                    id=self.indexerid, ep=episode_num(season, episode), status=statusStrings[new_status]
                                )
                            )
                            curEp.status = new_status
                            curEp.subtitles = list()
                            curEp.subtitles_searchcount = 0
                            curEp.subtitles_lastsearch = str(datetime.datetime.min)
                        curEp.location = ""
                        curEp.hasnfo = False
                        curEp.hastbn = False
                        curEp.release_name = ""
                        curEp.release_group = ""

                        sql_l.append(curEp.get_sql())
                else:
                    logger.info("Skipping updating removed file because `skip removed files` is enabled: {}".format(curLoc))

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

    def download_subtitles(self, force=False):
        if not os.path.isdir(self._location):
            logger.debug(f"{self.indexerid}: Show dir doesn't exist, can't download subtitles")
            return

        logger.debug(f"{self.indexerid}: Downloading subtitles")

        try:
            episodes = self.getAllEpisodes(has_location=True)
            if not episodes:
                logger.debug(f"{self.indexerid}: No episodes to download subtitles for {self.name}")
                return

            for episode in episodes:
                episode.download_subtitles(force=force)

        except Exception:
            logger.debug(f"{self.indexerid}: Error occurred when downloading subtitles for {self.name}")
            logger.error(traceback.format_exc())

    def saveToDB(self, forceSave=False):

        if not self.dirty and not forceSave:
            return

        logger.debug("{0:d}: Saving to database: {1}".format(self.indexerid, self.name))

        controlValueDict = {"indexer_id": self.indexerid}
        newValueDict = {
            "indexer": self.indexer,
            "show_name": self.show_name,
            "custom_name": self.custom_name,
            "location": self._location,
            "network": self.network,
            "genre": "|".join(self.genre) if isinstance(self.genre, list) else self.genre,
            "classification": self.classification,
            "runtime": self.runtime,
            "quality": self.quality,
            "airs": self.airs,
            "status": self.status,
            "flatten_folders": int(not self.season_folders),
            "paused": self.paused,
            "air_by_date": self.air_by_date,
            "anime": self.anime,
            "scene": self.scene,
            "sports": self.sports,
            "subtitles": self.subtitles,
            "dvdorder": self.dvdorder,
            "startyear": self.startyear,
            "lang": self.lang,
            "imdb_id": self.imdb_id,
            "last_update_indexer": self.last_update_indexer,
            "rls_ignore_words": self.rls_ignore_words,
            "rls_require_words": self.rls_require_words,
            "rls_prefer_words": self.rls_prefer_words,
            "default_ep_status": self.default_ep_status,
            "sub_use_sr_metadata": self.subtitles_sr_metadata,
        }

        main_db_con = db.DBConnection()
        main_db_con.upsert("tv_shows", newValueDict, controlValueDict)

        helpers.update_anime_support()

        if self.imdb_id and self.imdb_info:
            main_db_con = db.DBConnection()
            main_db_con.upsert("imdb_info", self.imdb_info, controlValueDict)

    def __str__(self):
        info_list = [
            f"indexerid: {self.indexerid}",
            f"indexer: {self.indexer}",
            f"name: {self.name}",
            f"location: {self._location}",
            f"status: {self.status}",
            f"startyear: {self.startyear}",
            f"classification: {self.classification}",
            f"runtime: {self.runtime}",
            f"quality: {self.quality}",
            f"scene: {self.is_scene}",
            f"sports: {self.is_sports}",
            f"anime: {self.is_anime}",
        ]
        if self.network:
            info_list.append(f"network: {self.network}")
        if self.airs:
            info_list.append(f"airs: {self.airs}")
        if self.genre:
            info_list.append(f"genre: {'|'.join(self.genre)}")
        return "\n".join(info_list)

    @staticmethod
    def qualitiesToString(qualities=None):
        return ", ".join([Quality.qualityStrings[quality] for quality in qualities or [] if quality and quality in Quality.qualityStrings]) or "None"

    def wantEpisode(self, season, episode, quality, manualSearch=False, downCurQuality=False):

        allowed_qualities, preferred_qualities = Quality.splitQuality(self.quality)
        logger.debug(
            f"Any,Best = [ {self.qualitiesToString(allowed_qualities)} ] [ {self.qualitiesToString(preferred_qualities)} ]"
            f" Found = [ {self.qualitiesToString([quality])} ]"
        )

        if quality not in allowed_qualities + preferred_qualities or quality is UNKNOWN:
            logger.debug(
                "Don't want this quality, ignoring found result for {name} {ep} with quality {quality}".format(
                    name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]
                )
            )
            return False

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?", [self.indexerid, season, episode])

        if not sql_results or not len(sql_results):
            logger.debug(
                "Unable to find a matching episode in database, ignoring found result for {name} {ep} with quality {quality}".format(
                    name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]
                )
            )
            return False

        epStatus = int(sql_results[0]["status"])
        epStatus_text = statusStrings[epStatus]

        if epStatus in Quality.ARCHIVED + [UNAIRED, SKIPPED, IGNORED] and not manualSearch:
            logger.debug(
                "Existing episode status is '{status}', ignoring found result for {name} {ep} with quality {quality}".format(
                    status=epStatus_text, name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]
                )
            )
            return False

        curStatus_, curQuality = Quality.splitCompositeStatus(epStatus)

        if epStatus in (WANTED, SKIPPED, UNKNOWN, FAILED):
            logger.debug(
                "Existing episode status is '{status}', getting found result for {name} {ep} with quality {quality}".format(
                    status=epStatus_text, name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]
                )
            )
            return True
        elif manualSearch:
            if (downCurQuality and quality >= curQuality) or (not downCurQuality and quality != curQuality):
                logger.debug(
                    "Usually ignoring found result, but forced search allows the quality,"
                    " getting found result for {name} {ep} with quality {quality}".format(
                        name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]
                    )
                )
                return True

        if (
            epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER
            and quality in preferred_qualities
            and (quality > curQuality or curQuality not in preferred_qualities)
        ):
            logger.debug(
                "Episode already exists with quality {existing_quality} but the found result"
                " quality {new_quality} is wanted more, getting found result for {name} {ep}".format(
                    existing_quality=Quality.qualityStrings[curQuality],
                    new_quality=Quality.qualityStrings[quality],
                    name=self.name,
                    ep=episode_num(season, episode),
                )
            )
            return True
        elif curQuality == Quality.UNKNOWN and manualSearch:
            logger.debug(
                "Episode already exists but quality is Unknown, getting found result for {name} {ep} with quality {quality}".format(
                    name=self.name, ep=episode_num(season, episode), quality=Quality.qualityStrings[quality]
                )
            )
            return True
        else:
            logger.debug(
                "Episode already exists with quality {existing_quality} and the found result has same/lower quality,"
                " ignoring found result for {name} {ep} with quality {new_quality}".format(
                    existing_quality=Quality.qualityStrings[curQuality],
                    name=self.name,
                    ep=episode_num(season, episode),
                    new_quality=Quality.qualityStrings[quality],
                )
            )
        return False

    def getOverview(self, epStatus, backlog=False):
        """
        Get the Overview status from the Episode status

        param epStatus: an Episode status
        return: an Overview status
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

            if cur_quality not in allowed_qualities + preferred_qualities and not backlog:
                return Overview.QUAL
            elif preferred_qualities and cur_quality not in preferred_qualities and not backlog:
                return Overview.QUAL
            else:
                return Overview.GOOD
        else:
            logger.error(f"Could not parse episode status into a valid overview status: {epStatus}")

    def __getstate__(self):
        d = dict(self.__dict__)
        del d["lock"]
        return d

    def __setstate__(self, d):
        d["lock"] = threading.Lock()
        self.__dict__.update(d)


class TVEpisode(object):
    name = DirtySetter("")
    season = DirtySetter(None)
    episode = DirtySetter(None)
    absolute_number = DirtySetter(0)
    description = DirtySetter("")
    subtitles = DirtySetter(list())
    subtitles_searchcount = DirtySetter(0)
    subtitles_lastsearch = DirtySetter(str(datetime.datetime.min))
    airdate = DirtySetter(datetime.date.min)
    hasnfo = DirtySetter(False)
    hastbn = DirtySetter(False)
    status = DirtySetter(UNKNOWN)
    indexerid = DirtySetter(0)
    file_size = DirtySetter(0)
    release_name = DirtySetter("")
    is_proper = DirtySetter(False)
    version = DirtySetter(0)
    release_group = DirtySetter("")
    indexer = DirtySetter(1)
    startyear = DirtySetter("")

    def __init__(self, show, season, episode, ep_file=""):
        self.season = season
        self.episode = episode
        self._location = ep_file
        self.startyear = ""

        # setting any of the above sets the dirty flag
        self.dirty = True

        self.show = show
        self.indexer = self.show.indexer

        self.scene_season = 0
        self.scene_episode = 0
        self.scene_absolute_number = 0

        self.lock = threading.Lock()

        self.specifyEpisode(self.season, self.episode)

        self.relatedEps = []

        self.checkForMetaFiles()

        self.wantedQuality = []

    def _set_location(self, new_location):
        logger.debug(f"Setter sets location to {new_location}")

        # self._location = newLocation
        if self._location != new_location:
            self.dirty = True

        self._location = new_location

        if new_location and os.path.isfile(new_location):
            self.file_size = os.path.getsize(new_location)
        else:
            self.file_size = 0

    location = property(lambda self: self._location, _set_location)

    @property
    def idxr(self):
        return self.show.idxr

    @property
    def indexer_name(self):
        return self.show.indexer_name

    def refreshSubtitles(self):
        """Look for subtitles files and refresh the subtitles property"""
        self.subtitles, save_subtitles = subtitles.refresh_subtitles(self)
        if save_subtitles:
            self.saveToDB()

    def download_subtitles(self, force=False, force_lang=None):
        if not os.path.isfile(self.location):
            logger.debug(
                "{id}: Episode file doesn't exist, can't download subtitles for {ep}".format(id=self.show.indexerid, ep=episode_num(self.season, self.episode))
            )
            return

        if not subtitles.needs_subtitles(self.subtitles, force_lang):
            logger.debug(
                "Episode already has all needed subtitles, skipping episode {ep} of show {show}".format(
                    ep=episode_num(self.season, self.episode), show=self.show.name
                )
            )
            return

        logger.debug(
            "Checking subtitle candidates for {show} {ep} ({location})".format(
                show=self.show.name, ep=episode_num(self.season, self.episode), location=os.path.basename(self.location)
            )
        )

        self.subtitles, new_subtitles = subtitles.download_subtitles(self, force_lang)

        self.subtitles_searchcount += 1 if self.subtitles_searchcount else 1
        self.subtitles_lastsearch = datetime.datetime.now().strftime(dateTimeFormat)
        self.saveToDB()

        if new_subtitles:
            subtitle_list = ", ".join([subtitles.name_from_code(code) for code in new_subtitles])
            logger.debug(
                "{id}: Downloaded {subtitles} subtitles for {show} {ep}".format(
                    id=self.show.indexerid, subtitles=subtitle_list, show=self.show.name, ep=episode_num(self.season, self.episode)
                )
            )

            notifiers.notify_subtitle_download(self.pretty_name, subtitle_list)
        else:
            logger.debug(
                "{id}: No subtitles downloaded for {show} {ep}".format(id=self.show.indexerid, show=self.show.name, ep=episode_num(self.season, self.episode))
            )

        return new_subtitles

    def checkForMetaFiles(self):

        oldhasnfo = self.hasnfo
        oldhastbn = self.hastbn

        cur_nfo = False
        cur_tbn = False

        # check for nfo and tbn
        if os.path.isfile(self.location):
            for cur_provider in settings.metadata_provider_dict.values():
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

        sql_results = self.loadFromDB(season, episode)

        if not sql_results:
            # only load from NFO if we didn't load from DB
            if os.path.isfile(self.location):
                try:
                    self.loadFromNFO(self.location)
                except NoNFOException:
                    logger.error(f"{self.show.indexerid}: There was an error loading the NFO for episode {episode_num(season, episode)}")

                # if we tried loading it from NFO and didn't find the NFO, try the Indexers
                if not self.hasnfo:
                    try:
                        result = self.loadFromIndexer(season, episode)
                    except EpisodeDeletedException:
                        result = False

                    # if we failed SQL *and* NFO, Indexers then fail
                    if not result:
                        raise EpisodeNotFoundException("Couldn't find episode {ep}".format(ep=episode_num(season, episode)))

    def loadFromDB(self, season, episode):

        main_db_con = db.DBConnection()
        sql = "SELECT * FROM tv_episodes JOIN tv_shows WHERE showid = indexer_id and showid = ? AND season = ? AND episode = ?"
        sql_results = main_db_con.select(sql, [self.show.indexerid, season, episode])

        if len(sql_results) > 1:
            raise MultipleEpisodesInDatabaseException("Your DB has two records for the same show somehow.")
        elif not sql_results:
            logger.debug("{id}: Episode {ep} not found in the database".format(id=self.show.indexerid, ep=episode_num(season, episode)))
            return False
        else:
            if sql_results[0]["name"]:
                self.name = sql_results[0]["name"]

            self.season = season
            self.episode = episode
            self.absolute_number = try_int(sql_results[0]["absolute_number"], 0)
            self.description = sql_results[0]["description"]
            if not self.description:
                self.description = ""
            if sql_results[0]["subtitles"] and sql_results[0]["subtitles"]:
                self.subtitles = sql_results[0]["subtitles"].split(",")
            self.subtitles_searchcount = int(sql_results[0]["subtitles_searchcount"])
            self.subtitles_lastsearch = sql_results[0]["subtitles_lastsearch"]
            self.airdate = datetime.date.fromordinal(int(sql_results[0]["airdate"]))
            self.status = int(sql_results[0]["status"] or -1)
            self.startyear = str(sql_results[0]["startyear"] or "")

            # don't overwrite my location
            if sql_results[0]["location"] and not self._location:
                self.location = os.path.normpath(sql_results[0]["location"])

            if sql_results[0]["file_size"]:
                self.file_size = int(sql_results[0]["file_size"])
            else:
                self.file_size = 0

            self.indexerid = int(sql_results[0]["indexerid"])
            self.indexer = int(sql_results[0]["indexer"])

            sickchill.oldbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

            self.scene_season = try_int(sql_results[0]["scene_season"], 0)
            self.scene_episode = try_int(sql_results[0]["scene_episode"], 0)
            self.scene_absolute_number = try_int(sql_results[0]["scene_absolute_number"], 0)

            if self.scene_absolute_number == 0:
                self.scene_absolute_number = sickchill.oldbeard.scene_numbering.get_scene_absolute_numbering(
                    self.show.indexerid, self.show.indexer, self.absolute_number
                )

            if self.scene_season == 0 or self.scene_episode == 0:
                self.scene_season, self.scene_episode = sickchill.oldbeard.scene_numbering.get_scene_numbering(
                    self.show.indexerid, self.show.indexer, self.season, self.episode
                )

            if sql_results[0]["release_name"] is not None:
                self.release_name = sql_results[0]["release_name"]

            if sql_results[0]["is_proper"]:
                self.is_proper = int(sql_results[0]["is_proper"])

            if sql_results[0]["version"]:
                self.version = int(sql_results[0]["version"])

            if sql_results[0]["release_group"] is not None:
                self.release_group = sql_results[0]["release_group"]

            self.dirty = False
            return True

    def loadFromIndexer(self, season=None, episode=None):

        myEp = self.idxr.episode(self.show, season or self.season, episode or self.episode)
        if not myEp:
            if self.name:
                logger.debug("{} timed out but we have enough info from other sources, allowing the error".format(self.indexer_name))
                return
            else:
                logger.error("{} timed out, unable to create the episode".format(self.indexer_name))
                return False

        if not myEp.get("episodeName"):
            if self.name:
                logger.info(
                    "This episode {show} - {ep} has no name on {indexer}. Keeping the name: {title}".format(
                        show=self.show.name, ep=episode_num(season, episode), indexer=self.indexer_name, title=self.name
                    )
                )
            else:
                logger.info(
                    "This episode {show} - {ep} has no name on {indexer}. Setting to an empty string".format(
                        show=self.show.name, ep=episode_num(season, episode), indexer=self.indexer_name
                    )
                )
        else:
            self.name = myEp.get("episodeName")

        if not myEp.get("absoluteNumber"):
            logger.debug(
                "{id}: This episode {show} - {ep} has no absolute number on {indexer}".format(
                    id=self.show.indexerid, show=self.show.name, ep=episode_num(season, episode), indexer=self.indexer_name
                )
            )
        else:
            logger.debug(
                "{id}: The absolute number for {ep} is: {absolute} ".format(
                    id=self.show.indexerid, ep=episode_num(season or self.season, episode or self.episode), absolute=myEp["absoluteNumber"]
                )
            )
            self.absolute_number = try_int(myEp["absoluteNumber"], 0)

        self.season = (season, self.season)[season is None]
        self.episode = (episode, self.episode)[season is None]

        sickchill.oldbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

        self.scene_absolute_number = sickchill.oldbeard.scene_numbering.get_scene_absolute_numbering(
            self.show.indexerid, self.show.indexer, self.absolute_number
        )

        self.scene_season, self.scene_episode = sickchill.oldbeard.scene_numbering.get_scene_numbering(
            self.show.indexerid, self.show.indexer, self.season, self.episode
        )

        if myEp.get("overview"):
            self.description = myEp.get("overview")

        first_aired = myEp.get("firstAired")
        if not first_aired or first_aired == "0000-00-00":
            if self.status in (WANTED, UNAIRED, UNKNOWN):
                # Allow changing the airdate of wanted/unaired/unknown in cases of postponed episodes
                first_aired = str(datetime.date.min)
            else:
                first_aired = str(self.airdate)

        rawAirdate = [int(x) for x in first_aired.split("-")]

        try:
            self.airdate = datetime.date(rawAirdate[0], rawAirdate[1], rawAirdate[2])
        except (ValueError, IndexError, TypeError):
            # Changed this to error because it should NEVER happen now
            logger.error(f"Malformed air date of {first_aired} retrieved from {self.indexer_name} for ({self.show.name} - {episode_num(season, episode)})")
            # if I'm incomplete on the indexer but I once was complete then just delete myself from the DB for now
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        if myEp.get("id"):
            self.indexerid = myEp.get("id")

        if not self.indexerid:
            logger.error("Failed to retrieve ID from {indexer}".format(indexer=self.indexer_name))
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        if not os.path.isdir(self.show._location) and not settings.CREATE_MISSING_SHOW_DIRS and not settings.ADD_SHOWS_WO_DIR:
            logger.info(f"The show dir {self.show._location} is missing, not bothering to change the episode statuses since it'd probably be invalid")
            return

        if self.location:
            logger.debug(
                "{id}: Setting status for {ep} based on status {status} and location {location}".format(
                    id=self.show.indexerid, ep=episode_num(season, episode), status=statusStrings[self.status], location=self.location
                )
            )

        if not os.path.isfile(self.location):
            if self.airdate >= datetime.date.today() or self.airdate <= datetime.date.min:
                logger.debug(f"{self.show.indexerid}: Episode airs in the future or has no airdate, marking it {statusStrings[UNAIRED]}")
                self.status = UNAIRED
            elif self.status in [UNAIRED, UNKNOWN]:
                # Only do UNAIRED/UNKNOWN, it could already be snatched/ignored/skipped, or downloaded/archived to disconnected media
                logger.debug(f"Episode has already aired, marking it {statusStrings[self.show.default_ep_status]}")
                self.status = self.show.default_ep_status if self.season > 0 else SKIPPED  # auto-skip specials
            else:
                logger.debug(f"Not touching status [ {statusStrings[self.status]} ] It could be skipped/ignored/snatched/archived")

        elif is_media_file(self.location):
            # leave propers alone, you have to either post-process them or manually change them back
            if self.status not in Quality.SNATCHED_PROPER + Quality.DOWNLOADED + Quality.SNATCHED + Quality.ARCHIVED:
                logger.debug(f"5 Status changes from {self.status} to {Quality.statusFromName(self.location)}")
                self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

        # shouldn't get here probably
        else:
            logger.debug(f"6 Status changes from {self.status} to {UNKNOWN}")
            self.status = UNKNOWN

    def loadFromNFO(self, location):

        if not os.path.isdir(self.show._location):
            logger.info(f"{self.show.indexerid}: The show dir is missing, not bothering to try loading the episode NFO")
            return

        logger.debug(f"{self.show.indexerid}: Loading episode details from the NFO file associated with {location}")

        self.location = location

        if self.location != "":

            if self.status == UNKNOWN and is_media_file(self.location):
                logger.debug(f"7 Status changes from {self.status} to {Quality.statusFromName(self.location, anime=self.show.is_anime)}")
                self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

            nfoFile = replace_extension(self.location, "nfo")
            logger.debug(f"{self.show.indexerid}: Using NFO name {nfoFile}")

            if os.path.isfile(nfoFile):
                try:
                    showXML = ElementTree.ElementTree(file=nfoFile)
                except (SyntaxError, ValueError) as error:
                    logger.error(f"Error loading the NFO, backing up the NFO and skipping for now: {error}")
                    try:
                        os.rename(nfoFile, f"{nfoFile}.old")
                    except OSError as error:
                        logger.error(f"Failed to rename your episode's NFO file - you need to delete it or fix it: {error}")
                    raise NoNFOException("Error in NFO format")

                for epDetails in showXML.iter("episodedetails"):
                    if (
                        epDetails.findtext("season") is None
                        or int(epDetails.findtext("season")) != self.season
                        or epDetails.findtext("episode") is None
                        or int(epDetails.findtext("episode")) != self.episode
                    ):
                        logger.debug(
                            f"{self.show.indexerid}: NFO has an <episodedetails> block for a different episode - wanted {episode_num(self.season, self.episode)} but got {episode_num(epDetails.findtext('season'), epDetails.findtext('episode'))}"
                        )
                        continue

                    if epDetails.findtext("title") is None or epDetails.findtext("aired") is None:
                        raise NoNFOException("Error in NFO format (missing episode title or airdate)")

                    self.name = epDetails.findtext("title")
                    self.episode = int(epDetails.findtext("episode"))
                    self.season = int(epDetails.findtext("season"))

                    sickchill.oldbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

                    self.scene_absolute_number = sickchill.oldbeard.scene_numbering.get_scene_absolute_numbering(
                        self.show.indexerid, self.show.indexer, self.absolute_number
                    )

                    self.scene_season, self.scene_episode = sickchill.oldbeard.scene_numbering.get_scene_numbering(
                        self.show.indexerid, self.show.indexer, self.season, self.episode
                    )

                    self.description = epDetails.findtext("plot")
                    if self.description is None:
                        self.description = ""

                    if epDetails.findtext("aired"):
                        rawAirdate = [int(x) for x in epDetails.findtext("aired").split("-")]
                        self.airdate = datetime.date(rawAirdate[0], rawAirdate[1], rawAirdate[2])

                    self.hasnfo = True
            else:
                self.hasnfo = False

            if os.path.isfile(replace_extension(nfoFile, "tbn")):
                self.hastbn = True
            else:
                self.hastbn = False

    def __str__(self):

        return "\n".join(
            [
                f"{self.show.name} - S{self.season}E{self.episode} - {self.name}",
                f"location: {self.location}",
                f"description: {self.description}",
                f"subtitles: {','.join(self.subtitles)}",
                f"subtitles_searchcount: {self.subtitles_searchcount}",
                f"subtitles_lastsearch: {self.subtitles_lastsearch}",
                f"airdate: {self.airdate.toordinal()} ({self.airdate})",
                f"hasnfo: {self.hasnfo}",
                f"hastbn: {self.hastbn}",
                f"status: {self.status}",
            ]
        )

    def createMetaFiles(self):

        if not os.path.isdir(self.show._location):
            logger.info(f"{self.show.indexerid}: The show dir is missing, not bothering to try to create metadata")
            return

        self.createNFO()
        self.createThumbnail()

        if self.checkForMetaFiles():
            self.saveToDB()

    def createNFO(self):

        result = False

        for cur_provider in settings.metadata_provider_dict.values():
            result = cur_provider.create_episode_metadata(self) or result
            result = cur_provider.update_episode_metadata(self) or result

        return result

    def createThumbnail(self):

        result = False

        for cur_provider in settings.metadata_provider_dict.values():
            result = cur_provider.create_episode_thumb(self) or result

        return result

    def deleteEpisode(self):

        logger.debug(_("Deleting {show} {ep} from the DB").format(show=self.show.name, ep=episode_num(self.season, self.episode)))

        # remove myself from the show dictionary
        if self.show.getEpisode(self.season, self.episode, noCreate=True) == self:
            logger.debug(_("Removing myself from my show's list"))
            del self.show.episodes[self.season][self.episode]

        # delete myself from the DB
        logger.debug(_("Deleting myself from the database"))
        main_db_con = db.DBConnection()
        main_db_con.action("DELETE FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?", [self.show.indexerid, self.season, self.episode])
        raise EpisodeDeletedException()

    def get_sql(self, forceSave=False):
        """
        Creates SQL queue for this episode if any of its data has been changed since the last save.

        forceSave: If True it will create SQL queue even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """
        try:
            if not self.dirty and not forceSave:
                logger.debug(f"{self.show.indexerid}: Not creating SQL queue - record is not dirty")
                return

            main_db_con = db.DBConnection()
            rows = main_db_con.select(
                "SELECT episode_id, subtitles FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                [self.show.indexerid, self.season, self.episode],
            )

            epID = None
            if rows:
                epID = int(rows[0]["episode_id"])

            if epID:
                # use a custom update method to get the data into the DB for existing records.
                # Multi or added subtitle or removed subtitles
                if settings.SUBTITLES_MULTI or not rows[0]["subtitles"] or not self.subtitles:
                    return [
                        "UPDATE tv_episodes SET indexerid = ?, indexer = ?, name = ?, description = ?, subtitles = ?, "
                        "subtitles_searchcount = ?, subtitles_lastsearch = ?, airdate = ?, hasnfo = ?, hastbn = ?, status = ?, "
                        "location = ?, file_size = ?, release_name = ?, is_proper = ?, showid = ?, season = ?, episode = ?, "
                        "absolute_number = ?, version = ?, release_group = ? WHERE episode_id = ?",
                        [
                            self.indexerid,
                            self.indexer,
                            self.name,
                            self.description,
                            ",".join(self.subtitles),
                            self.subtitles_searchcount,
                            self.subtitles_lastsearch,
                            self.airdate.toordinal(),
                            self.hasnfo,
                            self.hastbn,
                            self.status,
                            self.location,
                            self.file_size,
                            self.release_name,
                            self.is_proper,
                            self.show.indexerid,
                            self.season,
                            self.episode,
                            self.absolute_number,
                            self.version,
                            self.release_group,
                            epID,
                        ],
                    ]
                else:
                    # Don't update the subtitle language when the srt file doesn't contain the alpha2 code, keep value from subliminal
                    return [
                        "UPDATE tv_episodes SET indexerid = ?, indexer = ?, name = ?, description = ?, "
                        "subtitles_searchcount = ?, subtitles_lastsearch = ?, airdate = ?, hasnfo = ?, hastbn = ?, status = ?, "
                        "location = ?, file_size = ?, release_name = ?, is_proper = ?, showid = ?, season = ?, episode = ?, "
                        "absolute_number = ?, version = ?, release_group = ? WHERE episode_id = ?",
                        [
                            self.indexerid,
                            self.indexer,
                            self.name,
                            self.description,
                            self.subtitles_searchcount,
                            self.subtitles_lastsearch,
                            self.airdate.toordinal(),
                            self.hasnfo,
                            self.hastbn,
                            self.status,
                            self.location,
                            self.file_size,
                            self.release_name,
                            self.is_proper,
                            self.show.indexerid,
                            self.season,
                            self.episode,
                            self.absolute_number,
                            self.version,
                            self.release_group,
                            epID,
                        ],
                    ]
            else:
                # use a custom insert method to get the data into the DB.
                return [
                    "INSERT OR IGNORE INTO tv_episodes (episode_id, indexerid, indexer, name, description, subtitles, "
                    "subtitles_searchcount, subtitles_lastsearch, airdate, hasnfo, hastbn, status, location, file_size, "
                    "release_name, is_proper, showid, season, episode, absolute_number, version, release_group) VALUES "
                    "((SELECT episode_id FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?)"
                    ",?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
                    [
                        self.show.indexerid,
                        self.season,
                        self.episode,
                        self.indexerid,
                        self.indexer,
                        self.name,
                        self.description,
                        ",".join(self.subtitles),
                        self.subtitles_searchcount,
                        self.subtitles_lastsearch,
                        self.airdate.toordinal(),
                        self.hasnfo,
                        self.hastbn,
                        self.status,
                        self.location,
                        self.file_size,
                        self.release_name,
                        self.is_proper,
                        self.show.indexerid,
                        self.season,
                        self.episode,
                        self.absolute_number,
                        self.version,
                        self.release_group,
                    ],
                ]
        except OperationalError as error:
            logger.error(f"Error while updating database: {error}")

    def saveToDB(self, forceSave=False):
        """
        Saves this episode to the database if any of its data has been changed since the last save.

        forceSave: If True it will save to the database even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """

        if not self.dirty and not forceSave:
            return

        newValueDict = {
            "indexerid": self.indexerid,
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
            "release_group": self.release_group,
        }

        controlValueDict = {"showid": self.show.indexerid, "season": self.season, "episode": self.episode}

        logger.debug(f"{self.show.indexerid}: Saving episode details to database S{self.season}E{self.episode}: {statusStrings[self.status]}")

        # use a custom update/insert method to get the data into the DB
        main_db_con = db.DBConnection()
        main_db_con.upsert("tv_episodes", newValueDict, controlValueDict)

    def fullPath(self):
        if self.location is None or self.location == "":
            return None
        else:
            return os.path.join(self.show.location, self.location)

    def createStrings(self, pattern=None):
        patterns = ["%S.N.S%SE%0E", "%S.N.S%0SE%E", "%S.N.S%SE%E", "%S.N.S%0SE%0E", "%SN S%SE%0E", "%SN S%0SE%E", "%SN S%SE%E", "%SN S%0SE%0E"]

        strings = []
        if not pattern:
            for p in patterns:
                strings += [self._format_pattern(p)]
            return strings
        return self._format_pattern(pattern)

    @property
    def pretty_name(self):
        """
        Returns the name of this episode in a "pretty" human-readable format. Used for logging
        and notifications and such.

        Returns: A string representing the episode's name and season/ep numbers
        """

        if self.show.anime and not self.show.scene:
            return self._format_pattern("%SN - %AB - %EN")
        elif self.show.air_by_date:
            return self._format_pattern("%SN - %AD - %EN")

        return self._format_pattern("%SN - S%0SE%0E - %EN")

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
                    goodName += f" & {relEp.name}"

        return goodName

    def _replace_map(self):
        """
        Generates a replacement map for this episode which maps all possible custom naming patterns to the correct
        value for this episode.

        Returns: A dict with patterns as the keys and their replacement values as the values.
        """

        ep_name = self._ep_name()

        def dot(name):
            # assert isinstance(name, unicode), f'{name} is not unicode'
            # re.sub str . was any char (messy) and sanitizer wouldn't allow brackets to remain without other issues.
            swap_chars = " -_"
            for x in swap_chars:
                name = name.replace(x, ".")
            return name

        def us(name):
            return re.sub("[ -]", "_", name)

        def release_name(name):
            if name:
                name = helpers.remove_non_release_groups(remove_extension(name))
            return name

        def release_group(show, name):
            if name:
                name = helpers.remove_non_release_groups(remove_extension(name))
            else:
                return ""

            try:
                parse_result = NameParser(name, showObj=show, naming_pattern=True).parse(name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.debug(f"Unable to get parse release_group: {error}")
                return ""

            if not parse_result.release_group:
                return ""

            return parse_result.release_group.strip(".- []{}")

        epStatus_, epQual = Quality.splitCompositeStatus(self.status)

        # set the different show name variables and only 4 digit years
        show_name = self.show.name
        show_name_no_year = re.sub(r"\(\d{4}\)$", "", show_name).strip()
        # if the start year is less than 1 character there isn't one so revert to show name (safety check)
        if self.startyear:
            show_start_year = f"{show_name_no_year} ({self.startyear})"
        else:
            show_start_year = show_name

        if settings.NAMING_STRIP_YEAR:
            show_name = show_name_no_year
        else:
            show_name = self.show.name

        # remove brackets from both name sets
        if settings.NAMING_NO_BRACKETS:
            show_name = re.sub(r"[()]", "", show_name).strip()
            show_start_year = re.sub(r"[()]", "", show_start_year).strip()

        # try to get the release group
        rel_grp = {"SICKCHILL": "SICKCHILL"}
        if hasattr(self, "location"):  # from the location name
            rel_grp["location"] = release_group(self.show, self.location)
            if not rel_grp["location"]:
                del rel_grp["location"]
        if hasattr(self, "_release_group"):  # from the release group field in db
            rel_grp["database"] = self._release_group.strip(".- []{}")
            if not rel_grp["database"]:
                del rel_grp["database"]
        if hasattr(self, "release_name"):  # from the release name field in db
            rel_grp["release_name"] = release_group(self.show, self.release_name)
            if not rel_grp["release_name"]:
                del rel_grp["release_name"]

        # use release_group, release_name, location in that order
        if "database" in rel_grp:
            relgrp = "database"
        elif "release_name" in rel_grp:
            relgrp = "release_name"
        elif "location" in rel_grp:
            relgrp = "location"
        else:
            relgrp = "SICKCHILL"

        # try to get the release encoder to comply with scene naming standards
        encoder = Quality.sceneQualityFromName(self.release_name.replace(rel_grp[relgrp], ""), epQual)
        if encoder:
            logger.debug(f"Found codec for '{show_name}: {ep_name}'.")

        return {
            "%SN": show_name,
            "%S.N": dot(show_name),
            "%S_N": us(show_name),
            "%SNY": show_start_year,
            "%S.N.Y": dot(show_start_year),
            "%S_N_Y": us(show_start_year),
            "%EN": ep_name,
            "%E.N": dot(ep_name),
            "%E_N": us(ep_name),
            "%QN": Quality.qualityStrings[epQual],
            "%Q.N": dot(Quality.qualityStrings[epQual]),
            "%Q_N": us(Quality.qualityStrings[epQual]),
            "%SQN": Quality.sceneQualityStrings[epQual] + encoder,
            "%SQ.N": dot(Quality.sceneQualityStrings[epQual] + encoder),
            "%SQ_N": us(Quality.sceneQualityStrings[epQual] + encoder),
            "%S": "" if self.season is None else str(self.season),
            "%0S": "" if self.season is None else f"{int(self.season):02d}",
            "%E": "" if self.episode is None else str(self.episode),
            "%0E": "" if self.episode is None else f"{int(self.episode):02d}",
            "%XS": "" if self.scene_season is None else str(self.scene_season),
            "%0XS": "" if self.scene_season is None else f"{int(self.scene_season):02d}",
            "%XE": "" if self.scene_episode is None else str(self.scene_episode),
            "%0XE": "" if self.scene_episode is None else f"{int(self.scene_episode):02d}",
            "%AB": "" if self.absolute_number is None else f"{int(self.absolute_number):03d}",
            "%XAB": "" if self.scene_absolute_number is None else f"{int(self.scene_absolute_number):03d}",
            "%RN": release_name(self.release_name),
            "%RG": rel_grp[relgrp],
            "%CRG": rel_grp[relgrp].upper(),
            "%AD": str(self.airdate or "").replace("-", " ") if self.airdate else "",
            "%A.D": str(self.airdate).replace("-", ".") if self.airdate else "",
            "%A_D": us(str(self.airdate)) if self.airdate else "",
            "%A-D": str(self.airdate) if self.airdate else "",
            "%Y": str(self.airdate.year) if self.airdate else "",
            "%M": str(self.airdate.month) if self.airdate else "",
            "%D": str(self.airdate.day) if self.airdate else "",
            "%CY": str(datetime.date.today().year) if self.airdate else "",
            "%CM": str(datetime.date.today().month) if self.airdate else "",
            "%CD": str(datetime.date.today().day) if self.airdate else "",
            "%0M": f"{int(self.airdate.month):02d}" if self.airdate else "",
            "%0D": f"{int(self.airdate.day):02d}" if self.airdate else "",
            "%RT": "PROPER" if self.is_proper else "",
        }

    @staticmethod
    def _format_string(pattern, replace_map):
        """
        Replaces all template strings with the correct value
        """

        result_name = pattern

        # do the replacements
        for cur_replacement in sorted(replace_map, reverse=True):
            result_name = result_name.replace(cur_replacement, sanitize_filename(replace_map[cur_replacement]))
            result_name = result_name.replace(cur_replacement.lower(), sanitize_filename(replace_map[cur_replacement].lower()))

        return result_name

    def _format_pattern(self, pattern=None, multi=None, anime_type=None):
        """
        Manipulates an episode naming pattern and then fills the template in
        """

        if pattern is None:
            pattern = settings.NAMING_PATTERN

        if multi is None:
            multi = settings.NAMING_MULTI_EP

        if settings.NAMING_CUSTOM_ANIME:
            if anime_type is None:
                anime_type = settings.NAMING_ANIME
        else:
            anime_type = 3

        replace_map = self._replace_map()

        result_name = pattern

        # if there's no release group in the db, let the user know we replaced it
        if replace_map["%RG"] and replace_map["%RG"] != "SICKCHILL":
            if not hasattr(self, "_release_group") or not self._release_group:
                logger.debug(f"Episode has no release group, replacing it with '{replace_map['%RG']}'")
                self._release_group = replace_map["%RG"]  # if release_group is not in the db, put it there

        # if there's no release name then replace it with a reasonable facsimile
        if not replace_map["%RN"]:
            if self.show.air_by_date or self.show.sports:
                result_name = result_name.replace("%RN", "%S.N.%A.D.%E.N-" + replace_map["%RG"])
                result_name = result_name.replace("%rn", "%s.n.%A.D.%e.n-" + replace_map["%RG"].lower())

            elif anime_type != 3:
                result_name = result_name.replace("%RN", "%S.N.%AB.%E.N-" + replace_map["%RG"])
                result_name = result_name.replace("%rn", "%s.n.%ab.%e.n-" + replace_map["%RG"].lower())

            else:
                result_name = result_name.replace("%RN", "%S.N.S%0SE%0E.%E.N-" + replace_map["%RG"])
                result_name = result_name.replace("%rn", "%s.n.s%0se%0e.%e.n-" + replace_map["%RG"].lower())

            logger.debug(f"Episode has no release name, replacing it with a generic one: {result_name}")

        if not replace_map["%RT"]:
            result_name = re.sub("([ _.-]*)%RT([ _.-]*)", r"\2", result_name)

        # split off ep name part only
        name_groups = re.split(r"[\\/]", result_name)

        # figure out the double-ep numbering style for each group, if applicable
        for cur_name_group in name_groups:
            season_ep_regex = r"""
                                (?P<pre_sep>[ _.-]*)
                                ((?:s(?:eason|eries)?\s*)?%0?S(?![._]?N))
                                (.*?)
                                (%0?E(?![._]?N))
                                (?P<post_sep>[ _.-]*)
                              """
            ep_only_regex = r"(E?%0?E(?![._]?N))"

            # try the normal way
            season_ep_match = re.search(season_ep_regex, cur_name_group, re.I | re.X)
            ep_only_match = re.search(ep_only_regex, cur_name_group, re.I | re.X)

            # if we have a season and episode then collect the necessary data
            if season_ep_match:
                season_format = season_ep_match.group(2)
                ep_sep = season_ep_match.group(3)
                ep_format = season_ep_match.group(4)
                sep = season_ep_match.group("pre_sep")
                if not sep:
                    sep = season_ep_match.group("post_sep")
                if not sep:
                    sep = " "

                # force 2-3-4 format if they chose to extend
                if multi in (NAMING_EXTEND, NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED):
                    ep_sep = "-"

                regex_used = season_ep_regex

            # if there's no season then there's not much choice so we'll just force them to use 03-04-05 style
            elif ep_only_match:
                season_format = ""
                ep_sep = "-"
                ep_format = ep_only_match.group(1)
                sep = ""
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
                    ep_string += "E"

                ep_string += other_ep._format_string(ep_format.upper(), other_ep._replace_map())

            if anime_type != 3:
                if self.absolute_number == 0:
                    curAbsolute_number = self.episode
                else:
                    curAbsolute_number = self.absolute_number

                if self.season != 0:  # dont set absolute numbers if we are on specials !
                    if anime_type == 1:  # this crazy person wants both ! (note: +=)
                        ep_string += f"{sep}{curAbsolute_number:03d}"
                    elif anime_type == 2:  # total anime freak only need the absolute number ! (note: =)
                        ep_string = f"{curAbsolute_number:03d}"

                    for relEp in self.relatedEps:
                        if relEp.absolute_number != 0:
                            ep_string += f"-{relEp.absolute_number:03d}"
                        else:
                            ep_string += f"-{relEp.episode:03d}"

            regex_replacement = None
            if anime_type == 2 and not ep_only_match:
                regex_replacement = rf"\g<pre_sep>{ep_string}\g<post_sep>"
            elif season_ep_match:
                regex_replacement = rf"\g<pre_sep>\g<2>\g<3>{ep_string}\g<post_sep>"
            elif ep_only_match:
                regex_replacement = ep_string

            if regex_replacement:
                # fill out the template for this piece and then insert this piece into the actual pattern
                cur_name_group_result = re.sub("(?i)(?x)" + regex_used, regex_replacement, cur_name_group)
                result_name = result_name.replace(cur_name_group, cur_name_group_result)

        result_name = self._format_string(result_name, replace_map)

        logger.debug(f"formatting pattern: {pattern} -> {result_name}")

        return result_name

    def proper_path(self):
        """
        Figures out the path where this episode SHOULD live according to the renaming rules, relative from the show dir
        """

        anime_type = settings.NAMING_ANIME
        if not self.show.is_anime:
            anime_type = 3

        result = self.formatted_filename(anime_type=anime_type)

        # if they want us to flatten it, and we're allowed to flatten it then we will
        if not (self.show.season_folders or settings.NAMING_FORCE_FOLDERS):
            return result

        # if not we append the folder on and use that
        else:
            result = os.path.join(self.formatted_dir(anime_type=anime_type), result)

        return result

    def formatted_dir(self, pattern=None, multi=None, anime_type=None):
        """
        Just the folder name of the episode
        """

        if pattern is None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and settings.NAMING_CUSTOM_ABD and not self.relatedEps:
                pattern = settings.NAMING_ABD_PATTERN
            elif self.show.sports and settings.NAMING_CUSTOM_SPORTS and not self.relatedEps:
                pattern = settings.NAMING_SPORTS_PATTERN
            elif self.show.anime and settings.NAMING_CUSTOM_ANIME:
                pattern = settings.NAMING_ANIME_PATTERN
            else:
                pattern = settings.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r"[\\/]", pattern)

        if len(name_groups) == 1:
            return ""
        else:
            return self._format_pattern(os.sep.join(name_groups[:-1]), multi, anime_type)

    def formatted_filename(self, pattern=None, multi=None, anime_type=None):
        """
        Just the filename of the episode, formatted based on the naming settings
        """

        if pattern is None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and settings.NAMING_CUSTOM_ABD and not self.relatedEps:
                pattern = settings.NAMING_ABD_PATTERN
            elif self.show.sports and settings.NAMING_CUSTOM_SPORTS and not self.relatedEps:
                pattern = settings.NAMING_SPORTS_PATTERN
            elif self.show.anime and settings.NAMING_CUSTOM_ANIME:
                pattern = settings.NAMING_ANIME_PATTERN
            else:
                pattern = settings.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r"[\\/]", pattern)

        return sanitize_filename(self._format_pattern(name_groups[-1], multi, anime_type))

    def rename(self):
        """
        Renames an episode file and all related files to the location and filename as specified
        in the naming settings.
        """

        if not os.path.isfile(self.location):
            logger.warning(f"Can't perform rename on {self.location} when it doesn't exist, skipping")
            return

        proper_path = self.proper_path()
        absolute_proper_path = os.path.join(self.show.location, proper_path)
        absolute_current_path_no_ext, file_ext = os.path.splitext(self.location)
        absolute_current_path_no_ext_length = len(absolute_current_path_no_ext)

        related_subs = []

        current_path = absolute_current_path_no_ext

        if absolute_current_path_no_ext.startswith(self.show.location):
            current_path = absolute_current_path_no_ext[len(self.show.location) :]

        logger.debug(f"Renaming/moving episode from the base path {self.location} to {absolute_proper_path}")

        # if it's already named correctly then don't do anything
        if proper_path == current_path:
            logger.debug(f"{self.indexerid}: File {self.location} is already named correctly, skipping")
            return

        # get related files
        related_files = postProcessor.PostProcessor(self.location).list_associated_files(self.location, subfolders=True, rename=True)

        # get related subs
        if self.show.subtitles and settings.SUBTITLES_DIR:
            # assume that the video file is in the subtitles dir to find associated subs
            subs_path = os.path.join(settings.SUBTITLES_DIR, os.path.basename(self.location))
            related_subs = postProcessor.PostProcessor(self.location).list_associated_files(subs_path, subtitles_only=True, subfolders=True, rename=True)

        logger.debug(f"Files associated to {self.location}: {related_files}")

        # move the ep file
        result = helpers.rename_ep_file(self.location, absolute_proper_path, absolute_current_path_no_ext_length)

        # move related files
        for cur_related_file in related_files:
            # We need to fix something here because related files can be in subfolders and the original code doesn't handle this (at all)
            cur_related_dir = os.path.dirname(os.path.abspath(cur_related_file))
            subfolder = cur_related_dir.replace(os.path.dirname(os.path.abspath(self.location)), "")
            # We now have a subfolder. We need to add that to the absolute_proper_path.
            # First get the absolute proper-path dir
            proper_related_dir = os.path.dirname(os.path.abspath(absolute_proper_path + file_ext))
            proper_related_path = absolute_proper_path.replace(proper_related_dir, proper_related_dir + subfolder)

            cur_result = helpers.rename_ep_file(cur_related_file, proper_related_path, absolute_current_path_no_ext_length + len(subfolder))
            if not cur_result:
                logger.error(f"{self.indexerid}: Unable to rename file {cur_related_file}")

        for cur_related_sub in related_subs:
            absolute_proper_subs_path = os.path.join(settings.SUBTITLES_DIR, self.formatted_filename())
            cur_result = helpers.rename_ep_file(cur_related_sub, absolute_proper_subs_path, absolute_current_path_no_ext_length)
            if not cur_result:
                logger.error(f"{self.indexerid}: Unable to rename file {cur_related_sub}")

        # save the ep
        with self.lock:
            if result:
                self.location = absolute_proper_path + file_ext
                for relEp in self.relatedEps:
                    relEp.location = absolute_proper_path + file_ext

        # in case something changed with the metadata just do a quick check
        for curEp in [self] + self.relatedEps:
            curEp.checkForMetaFiles()

        # save changes to the database
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
        if not all([settings.AIRDATE_EPISODES, self.airdate, self.location, self.show, self.show.airs, self.show.network]):
            return

        try:
            airdate_ordinal = self.airdate.toordinal()
            if airdate_ordinal < 1:
                return

            airdatetime = network_timezones.parse_date_time(airdate_ordinal, self.show.airs, self.show.network)

            if settings.FILE_TIMESTAMP_TIMEZONE == "local":
                airdatetime = airdatetime.astimezone(network_timezones.sb_timezone)

            filemtime = datetime.datetime.fromtimestamp(os.path.getmtime(self.location)).replace(tzinfo=network_timezones.sb_timezone)

            if filemtime != airdatetime:
                airdatetime = airdatetime.timetuple()
                logger.debug(
                    f"{self.show.indexerid}: About to modify date of '{self.location}' to show air date {time.strftime('%b %d,%Y (%H:%M)', airdatetime)}"
                )
                try:
                    if helpers.touchFile(self.location, time.mktime(airdatetime)):
                        logger.info(
                            f"{self.show.indexerid}: Changed modify date of '{os.path.basename(self.location)}' to "
                            f"show air date {time.strftime('%b %d,%Y (%H:%M)', airdatetime)}"
                        )
                    else:
                        logger.warning(
                            f"{self.show.indexerid}: Unable to modify date of '{os.path.basename(self.location)}' "
                            f"to show air date {time.strftime('%b %d,%Y (%H:%M)', airdatetime)}"
                        )

                except OSError:
                    logger.warning(
                        f"{self.show.indexerid}: Failed to modify date of '{os.path.basename(self.location)}' "
                        f"to show air date {time.strftime('%b %d,%Y (%H:%M)', airdatetime)}"
                    )

        except OSError:
            logger.warning(f"{self.show.indexerid}: Failed to modify date of '{os.path.basename(self.location)}'")

    def cleanup_download_properties(self):
        """
        Clean the properties related with the current download.
        Use only when replacing with a new release or similar tasks.
        """
        self.file_size = 0
        self.is_proper = False
        self.location = ""
        self.release_group = ""
        self.release_name = ""
        self._location = ""
        self._release_group = ""

    def __getstate__(self):
        d = dict(self.__dict__)
        del d["lock"]
        return d

    def __setstate__(self, d):
        d["lock"] = threading.Lock()
        self.__dict__.update(d)
