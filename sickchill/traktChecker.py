# coding=utf-8
# Author: Frank Fenton
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import datetime
import os
import traceback

from libtrakt import TraktAPI
from libtrakt.exceptions import traktException

import sickchill
from sickchill import db, helpers, logger, search_queue
from sickchill.common import Quality, SKIPPED, UNKNOWN, WANTED
from sickchill.helper.common import episode_num, sanitize_filename
from sickchill.helper.encoding import ek
from sickchill.helper.exceptions import ex
from sickchill.show.Show import Show


def setEpisodeToWanted(show, s, e):
    """
    Sets an episode to wanted, only if it is currently skipped
    """
    epObj = show.getEpisode(s, e)
    if epObj:

        with epObj.lock:
            if epObj.status != SKIPPED or epObj.airdate == datetime.date.fromordinal(1):
                return

            logger.log("Setting episode {show} {ep} to wanted".format
                       (show=show.name, ep=episode_num(s, e)))
            # figure out what segment the episode is in and remember it so we can backlog it

            epObj.status = WANTED
            epObj.saveToDB()

        cur_backlog_queue_item = search_queue.BacklogQueueItem(show, [epObj])
        sickchill.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

        logger.log("Starting backlog search for {show} {ep} because some episodes were set to wanted".format
                   (show=show.name, ep=episode_num(s, e)))


class TraktChecker(object):
    def __init__(self):
        self.trakt_api = TraktAPI(sickchill.SSL_VERIFY, sickchill.TRAKT_TIMEOUT)
        self.todoBacklog = []
        self.todoWanted = []
        self.ShowWatchlist = {}
        self.EpisodeWatchlist = {}
        self.Collectionlist = {}
        self.amActive = False

    def run(self, force=False):
        self.amActive = True

        # add shows from trakt.tv watchlist
        if sickchill.TRAKT_SYNC_WATCHLIST:
            self.todoWanted = []  # its about to all get re-added
            if len(sickchill.ROOT_DIRS.split('|')) < 2:
                logger.log("No default root directory", logger.WARNING)
                return

            try:
                self.syncWatchlist()
            except Exception:
                logger.log(traceback.format_exc(), logger.DEBUG)

            try:
                # sync trakt.tv library with sickchill library
                self.syncLibrary()
            except Exception:
                logger.log(traceback.format_exc(), logger.DEBUG)

        self.amActive = False

    def findShow(self, indexer, indexerid):
        traktShow = None

        try:
            library = self.trakt_api.traktRequest("sync/collection/shows") or []
            if not library:
                logger.log("No shows found in your library, aborting library update", logger.DEBUG)
                return

            traktShow = [x for x in library if int(indexerid) in [int(x['show']['ids']['tvdb'] or 0), int(x['show']['ids']['tvrage'] or 0)]]
        except traktException as e:
            logger.log("Could not connect to Trakt service. Aborting library check. Error: {0}".format(repr(e)), logger.WARNING)

        return traktShow

    def removeShowFromTraktLibrary(self, show_obj):
        if self.findShow(show_obj.indexer, show_obj.indexerid):
            trakt_id = sickchill.indexerApi(show_obj.indexer).config['trakt_id']

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

            logger.log("Removing {0} from trakt.tv library".format(show_obj.name), logger.DEBUG)

            try:
                self.trakt_api.traktRequest("sync/collection/remove", data, method='POST')
            except traktException as e:
                logger.log("Could not connect to Trakt service. Aborting removing show {0} from Trakt library. Error: {1}".format(show_obj.name, repr(e)), logger.WARNING)

    def addShowToTraktLibrary(self, show_obj):
        """
        Sends a request to trakt indicating that the given show and all its episodes is part of our library.

        show_obj: The TVShow object to add to trakt
        """
        data = {}

        if not self.findShow(show_obj.indexer, show_obj.indexerid):
            trakt_id = sickchill.indexerApi(show_obj.indexer).config['trakt_id']
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

        if data:
            logger.log("Adding {0} to trakt.tv library".format(show_obj.name), logger.DEBUG)

            try:
                self.trakt_api.traktRequest("sync/collection", data, method='POST')
            except traktException as e:
                logger.log("Could not connect to Trakt service. Aborting adding show {0} to Trakt library. Error: {1}".format(show_obj.name, repr(e)), logger.WARNING)
                return

    def syncLibrary(self):
        if sickchill.TRAKT_SYNC and sickchill.USE_TRAKT:
            logger.log("Sync SickChill with Trakt Collection", logger.DEBUG)

            if self._getShowCollection():
                self.addEpisodeToTraktCollection()
                if sickchill.TRAKT_SYNC_REMOVE:
                    self.removeEpisodeFromTraktCollection()

    def removeEpisodeFromTraktCollection(self):
        if sickchill.TRAKT_SYNC_REMOVE and sickchill.TRAKT_SYNC and sickchill.USE_TRAKT:
            logger.log("COLLECTION::REMOVE::START - Look for Episodes to Remove From Trakt Collection", logger.DEBUG)

            main_db_con = db.DBConnection()
            sql_selection = 'select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode, tv_episodes.status, tv_episodes.location from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid'
            episodes = main_db_con.select(sql_selection)

            if episodes is not None:
                trakt_data = []

                for cur_episode in episodes:
                    trakt_id = sickchill.indexerApi(cur_episode[b"indexer"]).config[b'trakt_id']

                    if self._checkInList(trakt_id, str(cur_episode[b"showid"]), str(cur_episode[b"season"]), str(cur_episode[b"episode"]), List='Collection'):
                        if cur_episode[b"location"] == '':
                            logger.log("Removing Episode {show} {ep} from collection".format(
                                show=cur_episode[b"show_name"], ep=episode_num(cur_episode[b"season"], cur_episode[b"episode"])), logger.DEBUG
                            )
                            trakt_data.append((cur_episode[b"showid"], cur_episode[b"indexer"], cur_episode[b"show_name"], cur_episode[b"startyear"],
                                               cur_episode[b"season"], cur_episode[b"episode"]))

                if trakt_data:
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/collection/remove", data, method='POST')
                        self._getShowCollection()
                    except traktException as e:
                        logger.log("Could not connect to Trakt service. Error: {0}".format(ex(e)), logger.WARNING)

            logger.log("COLLECTION::REMOVE::FINISH - Look for Episodes to Remove From Trakt Collection", logger.DEBUG)

    def addEpisodeToTraktCollection(self):
        if sickchill.TRAKT_SYNC and sickchill.USE_TRAKT:
            logger.log("COLLECTION::ADD::START - Look for Episodes to Add to Trakt Collection", logger.DEBUG)

            main_db_con = db.DBConnection()
            sql_selection = 'select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid and tv_episodes.status in (' + ','.join([str(x) for x in Quality.DOWNLOADED + Quality.ARCHIVED]) + ')'
            episodes = main_db_con.select(sql_selection)

            if episodes is not None:
                trakt_data = []

                for cur_episode in episodes:
                    trakt_id = sickchill.indexerApi(cur_episode[b"indexer"]).config['trakt_id']

                    if not self._checkInList(trakt_id, str(cur_episode[b"showid"]), str(cur_episode[b"season"]), str(cur_episode[b"episode"]), List='Collection'):
                        logger.log("Adding Episode {show} {ep} to collection".format
                                   (show=cur_episode[b"show_name"],
                                    ep=episode_num(cur_episode[b"season"], cur_episode[b"episode"])),
                                   logger.DEBUG)
                        trakt_data.append((cur_episode[b"showid"], cur_episode[b"indexer"], cur_episode[b"show_name"], cur_episode[b"startyear"], cur_episode[b"season"], cur_episode[b"episode"]))

                if trakt_data:
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/collection", data, method='POST')
                        self._getShowCollection()
                    except traktException as e:
                        logger.log("Could not connect to Trakt service. Error: {0}".format(ex(e)), logger.WARNING)

            logger.log("COLLECTION::ADD::FINISH - Look for Episodes to Add to Trakt Collection", logger.DEBUG)

    def syncWatchlist(self):
        if sickchill.TRAKT_SYNC_WATCHLIST and sickchill.USE_TRAKT:
            logger.log("Sync SickChill with Trakt Watchlist", logger.DEBUG)

            self.removeShowFromSickChill()

            if self._getShowWatchlist():
                self.addShowToTraktWatchList()
                self.updateShows()

            if self._getEpisodeWatchlist():
                self.removeEpisodeFromTraktWatchList()
                self.addEpisodeToTraktWatchList()
                self.updateEpisodes()

    def removeEpisodeFromTraktWatchList(self):
        if sickchill.TRAKT_SYNC_WATCHLIST and sickchill.USE_TRAKT:
            logger.log("WATCHLIST::REMOVE::START - Look for Episodes to Remove from Trakt Watchlist", logger.DEBUG)

            main_db_con = db.DBConnection()
            sql_selection = 'select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode, tv_episodes.status from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid'
            episodes = main_db_con.select(sql_selection)

            if episodes is not None:
                trakt_data = []

                for cur_episode in episodes:
                    trakt_id = sickchill.indexerApi(cur_episode[b"indexer"]).config['trakt_id']

                    if self._checkInList(trakt_id, str(cur_episode[b"showid"]), str(cur_episode[b"season"]), str(cur_episode[b"episode"])):
                        if cur_episode[b"status"] not in Quality.SNATCHED + Quality.SNATCHED_PROPER + [UNKNOWN] + [WANTED]:
                            logger.log("Removing Episode {show} {ep} from watchlist".format
                                       (show=cur_episode[b"show_name"],
                                        ep=episode_num(cur_episode[b"season"], cur_episode[b"episode"])),
                                       logger.DEBUG)
                            trakt_data.append((cur_episode[b"showid"], cur_episode[b"indexer"], cur_episode[b"show_name"], cur_episode[b"startyear"], cur_episode[b"season"], cur_episode[b"episode"]))

                if trakt_data:
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')
                        self._getEpisodeWatchlist()
                    except traktException as e:
                        logger.log("Could not connect to Trakt service. Error: {0}".format(ex(e)), logger.WARNING)

                logger.log("WATCHLIST::REMOVE::FINISH - Look for Episodes to Remove from Trakt Watchlist", logger.DEBUG)

    def addEpisodeToTraktWatchList(self):
        if sickchill.TRAKT_SYNC_WATCHLIST and sickchill.USE_TRAKT:
            logger.log("WATCHLIST::ADD::START - Look for Episodes to Add to Trakt Watchlist", logger.DEBUG)

            main_db_con = db.DBConnection()
            sql_selection = 'select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid and tv_episodes.status in (' + ','.join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER + [WANTED]]) + ')'
            episodes = main_db_con.select(sql_selection)

            if episodes is not None:
                trakt_data = []

                for cur_episode in episodes:
                    trakt_id = sickchill.indexerApi(cur_episode[b"indexer"]).config['trakt_id']

                    if not self._checkInList(trakt_id, str(cur_episode[b"showid"]), str(cur_episode[b"season"]), str(cur_episode[b"episode"])):
                        logger.log("Adding Episode {show} {ep} to watchlist".format
                                   (show=cur_episode[b"show_name"],
                                    ep=episode_num(cur_episode[b"season"], cur_episode[b"episode"])),
                                   logger.DEBUG)
                        trakt_data.append((cur_episode[b"showid"], cur_episode[b"indexer"], cur_episode[b"show_name"], cur_episode[b"startyear"], cur_episode[b"season"],
                                           cur_episode[b"episode"]))

                if trakt_data:
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/watchlist", data, method='POST')
                        self._getEpisodeWatchlist()
                    except traktException as e:
                        logger.log("Could not connect to Trakt service. Error {0}".format(ex(e)), logger.WARNING)

            logger.log("WATCHLIST::ADD::FINISH - Look for Episodes to Add to Trakt Watchlist", logger.DEBUG)

    def addShowToTraktWatchList(self):
        if sickchill.TRAKT_SYNC_WATCHLIST and sickchill.USE_TRAKT:
            logger.log("SHOW_WATCHLIST::ADD::START - Look for Shows to Add to Trakt Watchlist", logger.DEBUG)

            if sickchill.showList is not None:
                trakt_data = []

                for show in sickchill.showList:
                    trakt_id = sickchill.indexerApi(show.indexer).config['trakt_id']

                    if not self._checkInList(trakt_id, str(show.indexerid), '0', '0', List='Show'):
                        logger.log("Adding Show: Indexer {0} {1} - {2} to Watchlist".format(trakt_id, str(show.indexerid), show.name), logger.DEBUG)
                        show_el = {'title': show.name, 'year': show.startyear, 'ids': {}}
                        if trakt_id == 'tvdb_id':
                            show_el['ids']['tvdb'] = show.indexerid
                        else:
                            show_el['ids']['tvrage'] = show.indexerid
                        trakt_data.append(show_el)

                if trakt_data:
                    try:
                        data = {'shows': trakt_data}
                        self.trakt_api.traktRequest("sync/watchlist", data, method='POST')
                        self._getShowWatchlist()
                    except traktException as e:
                        logger.log("Could not connect to Trakt service. Error: {0}".format(ex(e)), logger.WARNING)

            logger.log("SHOW_WATCHLIST::ADD::FINISH - Look for Shows to Add to Trakt Watchlist", logger.DEBUG)

    def removeShowFromSickChill(self):
        if sickchill.TRAKT_SYNC_WATCHLIST and sickchill.USE_TRAKT and sickchill.TRAKT_REMOVE_SHOW_FROM_SICKCHILL:
            logger.log("SHOW_SICKCHILL::REMOVE::START - Look for Shows to remove from SickChill", logger.DEBUG)

            if sickchill.showList:
                for show in sickchill.showList:
                    if show.status in ("Ended", "Canceled"):
                        if not show.imdbid:
                            logger.log('Could not check trakt progress for {0} because the imdb id is missing from tvdb data, skipping'.format
                                       (show.name), logger.WARNING)
                            continue

                        try:
                            progress = self.trakt_api.traktRequest("shows/" + show.imdbid + "/progress/watched") or []
                        except traktException as e:
                            logger.log("Could not connect to Trakt service. Aborting removing show {0} from SickChill. Error: {1}".format(show.name, repr(e)), logger.WARNING)
                            continue

                        if not progress:
                            continue

                        if progress.get('aired', True) == progress.get('completed', False):
                            sickchill.showQueueScheduler.action.remove_show(show, full=True)
                            logger.log("Show: {0} has been removed from SickChill".format(show.name), logger.DEBUG)

            logger.log("SHOW_SICKCHILL::REMOVE::FINISH - Trakt Show Watchlist", logger.DEBUG)

    def updateShows(self):
        logger.log("SHOW_WATCHLIST::CHECK::START - Trakt Show Watchlist", logger.DEBUG)

        self._getShowWatchlist()
        if not self.ShowWatchlist:
            logger.log("No shows found in your watchlist, aborting watchlist update", logger.DEBUG)
            return

        indexer = int(sickchill.TRAKT_DEFAULT_INDEXER)
        trakt_id = sickchill.indexerApi(indexer).config['trakt_id']

        for show_el in self.ShowWatchlist[trakt_id]:
            indexer_id = int(str(show_el))
            show = self.ShowWatchlist[trakt_id][show_el]

            # logger.log(u"Checking Show: %s %s %s" % (trakt_id, indexer_id, show['title']),logger.DEBUG)
            if int(sickchill.TRAKT_METHOD_ADD) != 2:
                self.addDefaultShow(indexer, indexer_id, show['title'], SKIPPED)
            else:
                self.addDefaultShow(indexer, indexer_id, show['title'], WANTED)

            if int(sickchill.TRAKT_METHOD_ADD) == 1:
                newShow = Show.find(sickchill.showList, indexer_id)

                if newShow is not None:
                    setEpisodeToWanted(newShow, 1, 1)
                else:
                    self.todoWanted.append((indexer_id, 1, 1))
        logger.log("SHOW_WATCHLIST::CHECK::FINISH - Trakt Show Watchlist", logger.DEBUG)

    def updateEpisodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        logger.log("SHOW_WATCHLIST::CHECK::START - Trakt Episode Watchlist", logger.DEBUG)

        self._getEpisodeWatchlist()
        if not self.EpisodeWatchlist:
            logger.log("No episode found in your watchlist, aborting episode update", logger.DEBUG)
            return

        managed_show = []

        indexer = int(sickchill.TRAKT_DEFAULT_INDEXER)
        trakt_id = sickchill.indexerApi(indexer).config['trakt_id']

        for show_el in self.EpisodeWatchlist[trakt_id]:
            indexer_id = int(show_el)
            show = self.EpisodeWatchlist[trakt_id][show_el]

            newShow = Show.find(sickchill.showList, indexer_id)

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
                logger.log("Could not parse the output from trakt for {0} ".format(show["title"]), logger.DEBUG)
        logger.log("SHOW_WATCHLIST::CHECK::FINISH - Trakt Episode Watchlist", logger.DEBUG)

    @staticmethod
    def addDefaultShow(indexer, indexer_id, name, status):
        """
        Adds a new show with the default settings
        """
        if not Show.find(sickchill.showList, int(indexer_id)):
            logger.log("Adding show " + str(indexer_id))
            root_dirs = sickchill.ROOT_DIRS.split('|')

            try:
                location = root_dirs[int(root_dirs[0]) + 1]
            except Exception:
                location = None

            if location:
                showPath = ek(os.path.join, location, sanitize_filename(name))
                dir_exists = helpers.makeDir(showPath)

                if not dir_exists:
                    logger.log("Unable to create the folder {0} , can't add the show".format(showPath), logger.WARNING)
                    return
                else:
                    helpers.chmodAsParent(showPath)

                sickchill.showQueueScheduler.action.add_show(int(indexer), int(indexer_id), showPath,
                                                             default_status=status,
                                                             quality=int(sickchill.QUALITY_DEFAULT),
                                                             season_folders=int(sickchill.SEASON_FOLDERS_DEFAULT),
                                                             paused=sickchill.TRAKT_START_PAUSED,
                                                             default_status_after=status)
            else:
                logger.log("There was an error creating the show, no root directory setting found", logger.WARNING)
                return

    def manageNewShow(self, show):
        logger.log("Checking if trakt watch list wants to search for episodes from new show " + show.name, logger.DEBUG)
        episodes = [i for i in self.todoWanted if i[0] == show.indexerid]

        for episode in episodes:
            self.todoWanted.remove(episode)
            setEpisodeToWanted(show, episode[1], episode[2])

    def _checkInList(self, trakt_id, showid, season, episode, List=None):
        """
         Check in the Watchlist or CollectionList for Show
         Is the Show, Season and Episode in the trakt_id list (tvdb / tvrage)
        """
        # logger.log(u"Checking Show: %s %s %s " % (trakt_id, showid, List),logger.DEBUG)

        if "Collection" == List:
            try:
                if self.Collectionlist[trakt_id][showid]['seasons'][season]['episodes'][episode] == episode:
                    return True
            except Exception:
                return False
        elif "Show" == List:
            try:
                if self.ShowWatchlist[trakt_id][showid]['id'] == showid:
                    return True
            except Exception:
                return False
        else:
            try:
                if self.EpisodeWatchlist[trakt_id][showid]['seasons'][season]['episodes'][episode] == episode:
                    return True
            except Exception:
                return False

    def _getShowWatchlist(self):
        """
        Get Watchlist and parse once into addressable structure
        """
        try:
            self.ShowWatchlist = {'tvdb_id': {}, 'tvrage_id': {}}
            TraktShowWatchlist = self.trakt_api.traktRequest("sync/watchlist/shows")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktShowWatchlist:
                tvdb = False
                tvrage = False

                if watchlist_el['show']['ids']["tvdb"] is not None:
                    tvdb = True

                if watchlist_el['show']['ids']["tvrage"] is not None:
                    tvrage = True

                title = watchlist_el['show']['title']
                year = str(watchlist_el['show']['year'])

                if tvdb:
                    showid = str(watchlist_el['show']['ids'][tvdb_id])
                    self.ShowWatchlist[tvdb_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year}

                if tvrage:
                    showid = str(watchlist_el['show']['ids'][tvrage_id])
                    self.ShowWatchlist[tvrage_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year}
        except traktException as e:
            logger.log("Could not connect to trakt service, cannot download Show Watchlist: {0}".format(repr(e)), logger.WARNING)
            return False
        return True

    def _getEpisodeWatchlist(self):
        """
         Get Watchlist and parse once into addressable structure
        """
        try:
            self.EpisodeWatchlist = {'tvdb_id': {}, 'tvrage_id': {}}
            TraktEpisodeWatchlist = self.trakt_api.traktRequest("sync/watchlist/episodes")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktEpisodeWatchlist:
                tvdb = False
                tvrage = False

                if watchlist_el['show']['ids']["tvdb"] is not None:
                    tvdb = True

                if watchlist_el['show']['ids']["tvrage"] is not None:
                    tvrage = True

                title = watchlist_el['show']['title']
                year = str(watchlist_el['show']['year'])
                season = str(watchlist_el['episode']['season'])
                episode = str(watchlist_el['episode']['number'])

                if tvdb:
                    showid = str(watchlist_el['show']['ids'][tvdb_id])

                    if showid not in self.EpisodeWatchlist[tvdb_id + '_id'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year, 'seasons': {}}

                    if season not in self.EpisodeWatchlist[tvdb_id + '_id'][showid]['seasons'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid]['seasons'][season] = {'s': season, 'episodes': {}}

                    if episode not in self.EpisodeWatchlist[tvdb_id + '_id'][showid]['seasons'][season]['episodes'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid]['seasons'][season]['episodes'][episode] = episode

                if tvrage:
                    showid = str(watchlist_el['show']['ids'][tvrage_id])

                    if showid not in self.EpisodeWatchlist[tvrage_id + '_id'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year, 'seasons': {}}

                    if season not in self.EpisodeWatchlist[tvrage_id + '_id'][showid]['seasons'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid]['seasons'][season] = {'s': season, 'episodes': {}}

                    if episode not in self.EpisodeWatchlist[tvrage_id + '_id'][showid]['seasons'][season]['episodes'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid]['seasons'][season]['episodes'][episode] = episode
        except traktException as e:
            logger.log("Could not connect to trakt service, cannot download Episode Watchlist: {0}".format(repr(e)), logger.WARNING)
            return False
        return True

    def _getShowCollection(self):
        """
        Get Collection and parse once into addressable structure
        """
        try:
            self.Collectionlist = {'tvdb_id': {}, 'tvrage_id': {}}
            logger.log("Getting Show Collection", logger.DEBUG)
            TraktCollectionList = self.trakt_api.traktRequest("sync/collection/shows")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktCollectionList:
                tvdb = False
                tvrage = False

                if watchlist_el['show']['ids']["tvdb"] is not None:
                    tvdb = True

                if watchlist_el['show']['ids']["tvrage"] is not None:
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

                                if showid not in self.Collectionlist[tvdb_id + '_id'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year, 'seasons': {}}

                                if season not in self.Collectionlist[tvdb_id + '_id'][showid]['seasons'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid]['seasons'][season] = {'s': season, 'episodes': {}}

                                if episode not in self.Collectionlist[tvdb_id + '_id'][showid]['seasons'][season]['episodes'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid]['seasons'][season]['episodes'][episode] = episode

                            if tvrage:
                                showid = str(watchlist_el['show']['ids'][tvrage_id])

                                if showid not in self.Collectionlist[tvrage_id + '_id'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year, 'seasons': {}}

                                if season not in self.Collectionlist[tvrage_id + '_id'][showid]['seasons'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid]['seasons'][season] = {'s': season, 'episodes': {}}

                                if episode not in self.Collectionlist[tvrage_id + '_id'][showid]['seasons'][season]['episodes'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid]['seasons'][season]['episodes'][episode] = episode
        except traktException as e:
            logger.log("Could not connect to trakt service, cannot download Show Collection: {0}".format(repr(e)), logger.WARNING)
            return False
        return True

    @staticmethod
    def trakt_bulk_data_generate(data):
        """
        Build the JSON structure to send back to Trakt
        """
        uniqueShows = {}
        uniqueSeasons = {}

        for showid, indexerid, show_name, startyear, season, episode in data:
            if showid not in uniqueShows:
                uniqueShows[showid] = {'title': show_name, 'year': startyear, 'ids': {}, 'seasons': []}
                trakt_id = sickchill.indexerApi(indexerid).config['trakt_id']

                if trakt_id == 'tvdb_id':
                    uniqueShows[showid]['ids']["tvdb"] = showid
                else:
                    uniqueShows[showid]['ids']["tvrage"] = showid
                uniqueSeasons[showid] = []

        # Get the unique seasons per Show
        for showid, indexerid, show_name, startyear, season, episode in data:
            if season not in uniqueSeasons[showid]:
                uniqueSeasons[showid].append(season)

        # build the query
        showList = []
        seasonsList = {}

        for searchedShow in uniqueShows:
            seasonsList[searchedShow] = []

            for searchedSeason in uniqueSeasons[searchedShow]:
                episodesList = []

                for showid, indexerid, show_name, startyear, season, episode in data:
                    if season == searchedSeason and showid == searchedShow:
                        episodesList.append({'number': episode})
                show = uniqueShows[searchedShow]
                show['seasons'].append({'number': searchedSeason, 'episodes': episodesList})
            showList.append(show)
        post_data = {'shows': showList}
        return post_data
