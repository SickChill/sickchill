# Author: Frank Fenton
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

import os
import traceback
import datetime

import sickbeard
from sickbeard import logger
from sickbeard import helpers
from sickbeard import search_queue
from sickbeard import db
from sickbeard.common import ARCHIVED
from sickbeard.common import SKIPPED
from sickbeard.common import UNKNOWN
from sickbeard.common import WANTED
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex
from common import Quality
from libtrakt import *
from libtrakt.exceptions import traktException


def setEpisodeToWanted(show, s, e):
    """
    Sets an episode to wanted, only if it is currently skipped
    """
    epObj = show.getEpisode(int(s), int(e))
    if epObj:

        with epObj.lock:
            if epObj.status != SKIPPED or epObj.airdate == datetime.date.fromordinal(1):
                return

            logger.log(u"Setting episode %s S%02dE%02d to wanted" %(show.name, s, e))
            # figure out what segment the episode is in and remember it so we can backlog it

            epObj.status = WANTED
            epObj.saveToDB()

        cur_backlog_queue_item = search_queue.BacklogQueueItem(show, [epObj])
        sickbeard.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

        logger.log(u"Starting backlog search for %s S%02dE%02d because some episodes were set to wanted" % (show.name, s, e))


class TraktChecker():

    def __init__(self):
        self.trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)
        self.todoBacklog = []
        self.todoWanted = []
        self.ShowWatchlist = {}
        self.EpisodeWatchlist = {}
        self.Collectionlist = {}
        self.amActive = False

    def run(self, force=False):

        self.amActive = True

        # add shows from trakt.tv watchlist
        if sickbeard.TRAKT_SYNC_WATCHLIST:
            self.todoWanted = []  # its about to all get re-added
            if len(sickbeard.ROOT_DIRS.split('|')) < 2:
                logger.log(u"No default root directory", logger.WARNING)
                return

            try:
                self.syncWatchlist()
            except Exception:
                logger.log(traceback.format_exc(), logger.DEBUG)

            try:
                # sync trakt.tv library with sickrage library
                self.syncLibrary()
            except Exception:
                logger.log(traceback.format_exc(), logger.DEBUG)

        self.amActive = False

    def findShow(self, indexer, indexerid):
        traktShow = None

        try:
            library = self.trakt_api.traktRequest("sync/collection/shows") or []

            if not library:
                logger.log(u"Could not connect to trakt service, aborting library check", logger.WARNING)
                return

            if not len(library):
                logger.log(u"No shows found in your library, aborting library update", logger.DEBUG)
                return

            traktShow = filter(lambda x: int(indexerid) in [int(x['show']['ids']['tvdb'] or 0), int(x['show']['ids']['tvrage'] or 0)], library)
        except traktException as e:
            logger.log(u"Could not connect to Trakt service. Aborting library check. Error: %s" % repr(e), logger.WARNING)

        return traktShow

    def removeShowFromTraktLibrary(self, show_obj):
        if self.findShow(show_obj.indexer, show_obj.indexerid):
            trakt_id = sickbeard.indexerApi(show_obj.indexer).config['trakt_id']

            # URL parameters
            data = {
                'shows': [
                    {
                        'title': show_obj.name,
                        'year': show_obj.startyear,
                        'ids': {}
                    }
                ]
            }
            if trakt_id == 'tvdb_id':
                data['shows'][0]['ids']['tvdb'] = show_obj.indexerid
            else:
                data['shows'][0]['ids']['tvrage'] = show_obj.indexerid

            logger.log(u"Removing %s from trakt.tv library" % show_obj.name, logger.DEBUG)

            try:
                self.trakt_api.traktRequest("sync/collection/remove", data, method='POST')
            except traktException as e:
                logger.log(u"Could not connect to Trakt service. Aborting removing show %s from Trakt library. Error: %s" % (show_obj.name, repr(e)), logger.WARNING)

    def addShowToTraktLibrary(self, show_obj):
        """
        Sends a request to trakt indicating that the given show and all its episodes is part of our library.

        show_obj: The TVShow object to add to trakt
        """

        data = {}

        if not self.findShow(show_obj.indexer, show_obj.indexerid):
            trakt_id = sickbeard.indexerApi(show_obj.indexer).config['trakt_id']
            # URL parameters
            data = {
                'shows': [
                    {
                        'title': show_obj.name,
                        'year': show_obj.startyear,
                        'ids': {}
                    }
                ]
            }
            if trakt_id == 'tvdb_id':
                data['shows'][0]['ids']['tvdb'] = show_obj.indexerid
            else:
                data['shows'][0]['ids']['tvrage'] = show_obj.indexerid

        if len(data):
            logger.log(u"Adding %s to trakt.tv library" % show_obj.name, logger.DEBUG)

            try:
                self.trakt_api.traktRequest("sync/collection", data, method='POST')
            except traktException as e:
                logger.log(u"Could not connect to Trakt service. Aborting adding show %s to Trakt library. Error: %s" % (show_obj.name, repr(e)), logger.WARNING)
                return

    def syncLibrary(self):
        if sickbeard.TRAKT_SYNC and sickbeard.USE_TRAKT:
            logger.log(u"Sync SickRage with Trakt Collection", logger.DEBUG)

            if self._getShowCollection():
                self.addEpisodeToTraktCollection()
                if sickbeard.TRAKT_SYNC_REMOVE:
                    self.removeEpisodeFromTraktCollection()

    def removeEpisodeFromTraktCollection(self):
        if sickbeard.TRAKT_SYNC_REMOVE and sickbeard.TRAKT_SYNC and sickbeard.USE_TRAKT:
            logger.log(u"COLLECTION::REMOVE::START - Look for Episodes to Remove From Trakt Collection", logger.DEBUG)

            myDB = db.DBConnection()
            sql_selection='select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode, tv_episodes.status, tv_episodes.location from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid'
            episodes = myDB.select(sql_selection)
            if episodes is not None:
                trakt_data = []
                for cur_episode in episodes:
                    trakt_id = sickbeard.indexerApi(cur_episode["indexer"]).config['trakt_id']
                    if self._checkInList(trakt_id,str(cur_episode["showid"]),str(cur_episode["season"]),str(cur_episode["episode"]), List='Collection'):
                        if cur_episode["location"] == '':
                            logger.log(u"Removing Episode %s S%02dE%02d from collection" %
                            (cur_episode["show_name"], cur_episode["season"], cur_episode["episode"]), logger.DEBUG)
                            trakt_data.append((cur_episode["showid"],cur_episode["indexer"],cur_episode["show_name"],cur_episode["startyear"],cur_episode["season"], cur_episode["episode"]))

            if len(trakt_data):

                try:
                    data = self.trakt_bulk_data_generate(trakt_data)
                    self.trakt_api.traktRequest("sync/collection/remove", data, method='POST')
                    self._getShowCollection()
                except traktException as e:
                    logger.log(u"Could not connect to Trakt service. Aborting removing episode %s S%02dE%02d from Trakt collection. Error: %s" % (cur_episode["show_name"], cur_episode["season"], cur_episode["episode"], repr(e)), logger.WARNING)

            logger.log(u"COLLECTION::REMOVE::FINISH - Look for Episodes to Remove From Trakt Collection", logger.DEBUG)

    def addEpisodeToTraktCollection(self):
        if sickbeard.TRAKT_SYNC and sickbeard.USE_TRAKT:
            logger.log(u"COLLECTION::ADD::START - Look for Episodes to Add to Trakt Collection", logger.DEBUG)

            myDB = db.DBConnection()
            sql_selection='select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid and tv_episodes.status in ('+','.join([str(x) for x in Quality.DOWNLOADED + [ARCHIVED]])+')'
            episodes = myDB.select(sql_selection)
            if episodes is not None:
                trakt_data = []
                for cur_episode in episodes:
                    trakt_id = sickbeard.indexerApi(cur_episode["indexer"]).config['trakt_id']
                    if not self._checkInList(trakt_id,str(cur_episode["showid"]),str(cur_episode["season"]),str(cur_episode["episode"]), List='Collection'):
                        logger.log(u"Adding Episode %s S%02dE%02d to collection" %
                        (cur_episode["show_name"], cur_episode["season"], cur_episode["episode"]), logger.DEBUG)
                        trakt_data.append((cur_episode["showid"],cur_episode["indexer"],cur_episode["show_name"],cur_episode["startyear"],cur_episode["season"], cur_episode["episode"]))

                if len(trakt_data):
                    
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/collection", data, method='POST')
                        self._getShowCollection()
                    except traktException as e:
                        logger.log(u"Could not connect to Trakt service. Aborting adding episode to Trakt collection. Error: %s" % repr(e), logger.WARNING)

            logger.log(u"COLLECTION::ADD::FINISH - Look for Episodes to Add to Trakt Collection", logger.DEBUG)

    def syncWatchlist(self):
        if sickbeard.TRAKT_SYNC_WATCHLIST and sickbeard.USE_TRAKT:
            logger.log(u"Sync SickRage with Trakt Watchlist", logger.DEBUG)

            self.removeShowFromSickRage()

            if self._getShowWatchlist():
                self.addShowToTraktWatchList()
                self.updateShows()

            if self._getEpisodeWatchlist():
                self.removeEpisodeFromTraktWatchList()
                self.addEpisodeToTraktWatchList()
                self.updateEpisodes()

    def removeEpisodeFromTraktWatchList(self):
        if sickbeard.TRAKT_SYNC_WATCHLIST and sickbeard.USE_TRAKT:
            logger.log(u"WATCHLIST::REMOVE::START - Look for Episodes to Remove from Trakt Watchlist", logger.DEBUG)

            myDB = db.DBConnection()
            sql_selection='select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode, tv_episodes.status from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid'
            episodes = myDB.select(sql_selection)
            if episodes is not None:
                trakt_data = []
                for cur_episode in episodes:
                    trakt_id = sickbeard.indexerApi(cur_episode["indexer"]).config['trakt_id']
                    if self._checkInList(trakt_id,str(cur_episode["showid"]),str(cur_episode["season"]),str(cur_episode["episode"])):
                        if cur_episode["status"] not in Quality.SNATCHED + Quality.SNATCHED_PROPER + [UNKNOWN] + [WANTED]:
                            logger.log(u"Removing Episode %s S%02dE%02d from watchlist" %
                            (cur_episode["show_name"], cur_episode["season"], cur_episode["episode"]), logger.DEBUG)
                            trakt_data.append((cur_episode["showid"],cur_episode["indexer"],cur_episode["show_name"],cur_episode["startyear"],cur_episode["season"], cur_episode["episode"]))

            if len(trakt_data):
                
                try:
                    data = self.trakt_bulk_data_generate(trakt_data)
                    self.trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')
                    self._getEpisodeWatchlist()
                except traktException as e:
                    logger.log(u"Could not connect to Trakt service. Aborting removing episode %s S%02dE%02d from Trakt watchlist. Error: %s" % (cur_episode["show_name"], cur_episode["season"], cur_episode["episode"], repr(e)), logger.WARNING)

            logger.log(u"WATCHLIST::REMOVE::FINISH - Look for Episodes to Remove from Trakt Watchlist", logger.DEBUG)

    def addEpisodeToTraktWatchList(self):
        if sickbeard.TRAKT_SYNC_WATCHLIST and sickbeard.USE_TRAKT:
            logger.log(u"WATCHLIST::ADD::START - Look for Episodes to Add to Trakt Watchlist", logger.DEBUG)

            myDB = db.DBConnection()
            sql_selection='select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid and tv_episodes.status in ('+','.join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER + [WANTED]])+')'
            episodes = myDB.select(sql_selection)
            if episodes is not None:
                trakt_data = []
                for cur_episode in episodes:
                    trakt_id = sickbeard.indexerApi(cur_episode["indexer"]).config['trakt_id']
                    if not self._checkInList(trakt_id,str(cur_episode["showid"]),str(cur_episode["season"]),str(cur_episode["episode"])):
                        logger.log(u"Adding Episode %s S%02dE%02d to watchlist" %
                        (cur_episode["show_name"], cur_episode["season"], cur_episode["episode"]), logger.DEBUG)
                        trakt_data.append((cur_episode["showid"],cur_episode["indexer"],cur_episode["show_name"],cur_episode["startyear"],cur_episode["season"],
                        cur_episode["episode"]))

                if len(trakt_data):

                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/watchlist", data, method='POST')
                        self._getEpisodeWatchlist()
                    except traktException as e:
                        logger.log(u"Could not connect to Trakt service. Aborting adding episode %s S%02dE%02d to Trakt watchlist. Error: %s" % (cur_episode["show_name"], cur_episode["season"], cur_episode["episode"], repr(e)), logger.WARNING)

            logger.log(u"WATCHLIST::ADD::FINISH - Look for Episodes to Add to Trakt Watchlist", logger.DEBUG)

    def addShowToTraktWatchList(self):
        if sickbeard.TRAKT_SYNC_WATCHLIST and sickbeard.USE_TRAKT:
            logger.log(u"SHOW_WATCHLIST::ADD::START - Look for Shows to Add to Trakt Watchlist", logger.DEBUG)

            if sickbeard.showList is not None:
                trakt_data = []
                for show in sickbeard.showList:
                    trakt_id = sickbeard.indexerApi(show.indexer).config['trakt_id']
                    if not self._checkInList(trakt_id,str(show.indexerid),'0','0',List='Show'):
                        logger.log(u"Adding Show: Indexer %s %s - %s to Watchlist" % ( trakt_id,str(show.indexerid), show.name), logger.DEBUG)
                        show_el = {'title': show.name, 'year': show.startyear, 'ids': {}}
                        if trakt_id == 'tvdb_id':
                            show_el['ids']['tvdb'] = show.indexerid
                        else:
                            show_el['ids']['tvrage'] = show.indexerid
                        trakt_data.append(show_el)

                if len(trakt_data):
                    
                    try:
                        data = {'shows': trakt_data}
                        self.trakt_api.traktRequest("sync/watchlist", data, method='POST')
                        self._getShowWatchlist()
                    except traktException as e:
                        logger.log(u"Could not connect to Trakt service. Aborting adding show %s to Trakt watchlist. Error: %s" % (show.name, repr(e)), logger.WARNING)

            logger.log(u"SHOW_WATCHLIST::ADD::FINISH - Look for Shows to Add to Trakt Watchlist", logger.DEBUG)

    def removeShowFromSickRage(self):
        if sickbeard.TRAKT_SYNC_WATCHLIST and sickbeard.USE_TRAKT and sickbeard.TRAKT_REMOVE_SHOW_FROM_SICKRAGE:
            logger.log(u"SHOW_SICKRAGE::REMOVE::START - Look for Shows to remove from SickRage", logger.DEBUG)

            if sickbeard.showList:
                for show in sickbeard.showList:
                    if show.status == "Ended":
                        try:
                            progress = self.trakt_api.traktRequest("shows/" + show.imdbid + "/progress/watched") or []
                        except traktException as e:
                            logger.log(u"Could not connect to Trakt service. Aborting removing show %s from SickRage. Error: %s" % (show.name, repr(e)), logger.WARNING)
                            return

                        if 'aired' in progress and 'completed' in progress and progress['aired'] == progress['completed']:
                            sickbeard.showQueueScheduler.action.removeShow(show, full=True)
                            logger.log(u"Show: %s has been removed from SickRage" % show.name, logger.DEBUG)

            logger.log(u"SHOW_SICKRAGE::REMOVE::FINISH - Trakt Show Watchlist", logger.DEBUG)

    def updateShows(self):
        logger.log(u"SHOW_WATCHLIST::CHECK::START - Trakt Show Watchlist", logger.DEBUG)

        if not len(self.ShowWatchlist):
            logger.log(u"No shows found in your watchlist, aborting watchlist update", logger.DEBUG)
            return

        indexer = int(sickbeard.TRAKT_DEFAULT_INDEXER)
        trakt_id = sickbeard.indexerApi(indexer).config['trakt_id']
        for show_el in self.ShowWatchlist[trakt_id]:
            indexer_id = int(str(show_el))
            show = self.ShowWatchlist[trakt_id][show_el]

            #logger.log(u"Checking Show: %s %s %s" % (trakt_id, indexer_id, show['title']),logger.DEBUG)
            if int(sickbeard.TRAKT_METHOD_ADD) != 2:
                self.addDefaultShow(indexer, indexer_id, show['title'], SKIPPED)
            else:
                self.addDefaultShow(indexer, indexer_id, show['title'], WANTED)

            if int(sickbeard.TRAKT_METHOD_ADD) == 1:
                newShow = helpers.findCertainShow(sickbeard.showList, indexer_id)
                if newShow is not None:
                    setEpisodeToWanted(newShow, 1, 1)
                else:
                    self.todoWanted.append((indexer_id, 1, 1))
        logger.log(u"SHOW_WATCHLIST::CHECK::FINISH - Trakt Show Watchlist", logger.DEBUG)

    def updateEpisodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        logger.log(u"SHOW_WATCHLIST::CHECK::START - Trakt Episode Watchlist", logger.DEBUG)

        if not len(self.EpisodeWatchlist):
            logger.log(u"No episode found in your watchlist, aborting episode update", logger.DEBUG)
            return

        managed_show = []

        indexer = int(sickbeard.TRAKT_DEFAULT_INDEXER)
        trakt_id = sickbeard.indexerApi(indexer).config['trakt_id']

        for show_el in self.EpisodeWatchlist[trakt_id]:
            indexer_id = int(show_el)
            show = self.EpisodeWatchlist[trakt_id][show_el]


            newShow = helpers.findCertainShow(sickbeard.showList, indexer_id)

            try:
                if newShow is None:
                    if indexer_id not in managed_show:
                        self.addDefaultShow(indexer, indexer_id, show['title'], SKIPPED)
                        managed_show.append(indexer_id)
                        for season_el in show['seasons']:
                            season = int(season_el)
                            for episode_el in show['seasons'][season_el]['episodes']:
                                self.todoWanted.append((indexer_id, season, int(episode_el)))
                else:
                    if newShow.indexer == indexer:
                        for season_el in show['seasons']:
                            season = int(season_el)
                            for episode_el in show['seasons'][season_el]['episodes']:
                                setEpisodeToWanted(newShow, season, int(episode_el))
            except TypeError:
                logger.log(u"Could not parse the output from trakt for %s " % show["title"], logger.DEBUG)
        logger.log(u"SHOW_WATCHLIST::CHECK::FINISH - Trakt Episode Watchlist", logger.DEBUG)

    def addDefaultShow(self, indexer, indexer_id, name, status):
        """
        Adds a new show with the default settings
        """
        if not helpers.findCertainShow(sickbeard.showList, int(indexer_id)):
            logger.log(u"Adding show " + str(indexer_id))
            root_dirs = sickbeard.ROOT_DIRS.split('|')

            try:
                location = root_dirs[int(root_dirs[0]) + 1]
            except:
                location = None

            if location:
                showPath = ek(os.path.join, location, helpers.sanitizeFileName(name))
                dir_exists = helpers.makeDir(showPath)
                if not dir_exists:
                    logger.log(u"Unable to create the folder %s , can't add the show" % showPath, logger.WARNING)
                    return
                else:
                    helpers.chmodAsParent(showPath)

                sickbeard.showQueueScheduler.action.addShow(int(indexer), int(indexer_id), showPath,
                                                            default_status=status,
                                                            quality=int(sickbeard.QUALITY_DEFAULT),
                                                            flatten_folders=int(sickbeard.FLATTEN_FOLDERS_DEFAULT),
                                                            paused=sickbeard.TRAKT_START_PAUSED,
                                                            default_status_after=status,
                                                            archive=sickbeard.ARCHIVE_DEFAULT)
            else:
                logger.log(u"There was an error creating the show, no root directory setting found", logger.WARNING)
                return

    def manageNewShow(self, show):
        logger.log(u"Checking if trakt watch list wants to search for episodes from new show " + show.name, logger.DEBUG)
        episodes = [i for i in self.todoWanted if i[0] == show.indexerid]
        for episode in episodes:
            self.todoWanted.remove(episode)
            setEpisodeToWanted(show, episode[1], episode[2])

    def _checkInList(self,trakt_id, showid, season, episode, List = None):
        """
         Check in the Watchlist or CollectionList for Show
         Is the Show, Season and Episode in the trakt_id list (tvdb / tvrage)
        """
        #logger.log(u"Checking Show: %s %s %s " % (trakt_id, showid, List),logger.DEBUG)

        if "Collection" == List:
            try:
                if self.Collectionlist[trakt_id][showid]['seasons'][season]['episodes'][episode] == episode:
                    return True
            except:
                return False
        elif "Show" == List:
            try:
                if self.ShowWatchlist[trakt_id][showid]['id'] == showid:
                    return True
            except:
                return False
        else:
            try:
                if self.EpisodeWatchlist[trakt_id][showid]['seasons'][season]['episodes'][episode] == episode:
                    return True
            except:
                return False

    def _getShowWatchlist(self):
        """
        Get Watchlist and parse once into addressable structure
        """

        try:
            self.ShowWatchlist = { 'tvdb_id' : {}, 'tvrage_id': {} }
            TraktShowWatchlist = self.trakt_api.traktRequest("sync/watchlist/shows")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktShowWatchlist:
                tvdb = False
                tvrage = False
                if not watchlist_el['show']['ids']["tvdb"] is None:
                    tvdb = True
                if not watchlist_el['show']['ids']["tvrage"] is None:
                    tvrage = True

                title = watchlist_el['show']['title']
                year = str(watchlist_el['show']['year'])

                if tvdb:
                    showid = str(watchlist_el['show']['ids'][tvdb_id])
                    self.ShowWatchlist[tvdb_id + '_id'][showid] = { 'id': showid , 'title' : title , 'year': year }
                if tvrage:
                    showid = str(watchlist_el['show']['ids'][tvrage_id])
                    self.ShowWatchlist[tvrage_id + '_id'][showid] = { 'id': showid , 'title' : title , 'year': year }

        except traktException as e:
            logger.log(u"Could not connect to trakt service, cannot download Show Watchlist: %s" % repr(e), logger.WARNING)
            return False

        return True

    def _getEpisodeWatchlist(self):
        """
         Get Watchlist and parse once into addressable structure
        """

        try:
            self.EpisodeWatchlist = { 'tvdb_id' : {}, 'tvrage_id': {} }
            TraktEpisodeWatchlist = self.trakt_api.traktRequest("sync/watchlist/episodes")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktEpisodeWatchlist:
                tvdb = False
                tvrage = False
                if not watchlist_el['show']['ids']["tvdb"] is None:
                    tvdb = True
                if not watchlist_el['show']['ids']["tvrage"] is None:
                    tvrage = True

                title = watchlist_el['show']['title']
                year = str(watchlist_el['show']['year'])
                season = str(watchlist_el['episode']['season'])
                episode = str(watchlist_el['episode']['number'])

                if tvdb:
                    showid = str(watchlist_el['show']['ids'][tvdb_id])
                    if not showid in self.EpisodeWatchlist[tvdb_id + '_id'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid] = { 'id': showid , 'title' : title , 'year': year , 'seasons' : {} }

                    if not season in self.EpisodeWatchlist[tvdb_id + '_id'][showid]['seasons'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid]['seasons'][season] = { 's': season , 'episodes' : {} }

                    if not episode in self.EpisodeWatchlist[tvdb_id + '_id'][showid]['seasons'][season]['episodes'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid]['seasons'][season]['episodes'][episode] = episode

                if tvrage:
                    showid = str(watchlist_el['show']['ids'][tvrage_id])
                    if not showid in self.EpisodeWatchlist[tvrage_id + '_id'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid] = { 'id': showid , 'title' : title , 'year': year , 'seasons' : {} }

                    if not season in self.EpisodeWatchlist[tvrage_id + '_id'][showid]['seasons'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid]['seasons'][season] = { 's': season , 'episodes' : {} }

                    if not episode in self.EpisodeWatchlist[tvrage_id + '_id'][showid]['seasons'][season]['episodes'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid]['seasons'][season]['episodes'][episode] = episode

        except traktException as e:
            logger.log(u"Could not connect to trakt service, cannot download Episode Watchlist: %s" % repr(e), logger.WARNING)
            return False

        return True

    def _getShowCollection(self):
        """
        Get Collection and parse once into addressable structure
        """

        try:

            self.Collectionlist = { 'tvdb_id' : {}, 'tvrage_id': {} }
            logger.log(u"Getting Show Collection", logger.DEBUG)
            TraktCollectionList = self.trakt_api.traktRequest("sync/collection/shows")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktCollectionList:
                tvdb = False
                tvrage = False
                if not watchlist_el['show']['ids']["tvdb"] is None:
                    tvdb = True
                if not watchlist_el['show']['ids']["tvrage"] is None:
                    tvrage = True

                title = watchlist_el['show']['title']
                year = str(watchlist_el['show']['year'])

                if 'seasons' in watchlist_el:
                    for season_el in watchlist_el['seasons']:
                        for episode_el in season_el['episodes']:
                            season = str(season_el['number'])
                            episode = str(episode_el['number'])

                            if tvdb:
                                showid = str(watchlist_el['show']['ids'][tvdb_id])
                                if not showid in self.Collectionlist[tvdb_id + '_id'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid] = { 'id': showid , 'title' : title , 'year': year , 'seasons' : {} }

                                if not season in self.Collectionlist[tvdb_id + '_id'][showid]['seasons'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid]['seasons'][season] = { 's': season , 'episodes' : {} }

                                if not episode in self.Collectionlist[tvdb_id + '_id'][showid]['seasons'][season]['episodes'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid]['seasons'][season]['episodes'][episode] = episode

                            if tvrage:
                                showid = str(watchlist_el['show']['ids'][tvrage_id])
                                if not showid in self.Collectionlist[tvrage_id + '_id'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid] = { 'id': showid , 'title' : title , 'year': year , 'seasons' : {} }

                                if not season in self.Collectionlist[tvrage_id + '_id'][showid]['seasons'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid]['seasons'][season] = { 's': season , 'episodes' : {} }

                                if not episode in self.Collectionlist[tvrage_id + '_id'][showid]['seasons'][season]['episodes'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid]['seasons'][season]['episodes'][episode] = episode

        except traktException as e:
            logger.log(u"Could not connect to trakt service, cannot download Show Collection: %s" % repr(e), logger.WARNING)
            return False

        return True

    def trakt_bulk_data_generate(self, data):
        """
        Build the JSON structure to send back to Trakt
        """

        uniqueShows = {}
        uniqueSeasons = {}
        for showid,indexerid,show_name,startyear,season,episode in data:
            if showid not in uniqueShows:
                uniqueShows[showid] = {'title': show_name, 'year': startyear, 'ids': {},'seasons': []}
                trakt_id = sickbeard.indexerApi(indexerid).config['trakt_id']
                if trakt_id == 'tvdb_id':
                    uniqueShows[showid]['ids']["tvdb"] = showid
                else:
                    uniqueShows[showid]['ids']["tvrage"] = showid
                uniqueSeasons[showid] = []

        # Get the unique seasons per Show
        for showid,indexerid,show_name,startyear,season,episode in data:
            if season not in uniqueSeasons[showid]:
                uniqueSeasons[showid].append(season)

        #build the query
        showList = []
        seasonsList = {}
        for searchedShow in uniqueShows:
            seasonsList[searchedShow] = []
            for searchedSeason in uniqueSeasons[searchedShow]:
                episodesList = []
                for showid,indexerid,show_name,startyear,season,episode in data:
                    if season == searchedSeason and showid == searchedShow:
                        episodesList.append({'number': episode})
                show = uniqueShows[searchedShow]
                show['seasons'].append({'number': searchedSeason, 'episodes': episodesList})
            showList.append(show)
        post_data = {'shows': showList}
        return post_data
