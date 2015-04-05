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
import json

import sickbeard
from sickbeard import encodingKludge as ek
from sickbeard.exceptions import ex
from sickbeard import logger
from sickbeard import helpers
from sickbeard import search_queue
from sickbeard import db
from sickbeard import notifiers
from sickbeard.common import SNATCHED, SNATCHED_PROPER, DOWNLOADED, SKIPPED, UNAIRED, IGNORED, ARCHIVED, WANTED, UNKNOWN, FAILED
from common import Quality, qualityPresetStrings, statusStrings
from lib.trakt import *
from trakt.exceptions import traktException


def setEpisodeToWanted(show, s, e):
    """
    Sets an episode to wanted, only is it is currently skipped
    """
    epObj = show.getEpisode(int(s), int(e))
    if epObj:

        with epObj.lock:
            if epObj.status != SKIPPED or epObj.airdate == datetime.date.fromordinal(1):
                return

            logger.log(u"Setting episode s" + str(s) + "e" + str(e) + " of show " + show.name + " to wanted")
            # figure out what segment the episode is in and remember it so we can backlog it

            epObj.status = WANTED
            epObj.saveToDB()

        cur_backlog_queue_item = search_queue.BacklogQueueItem(show, [epObj])
        sickbeard.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

        logger.log(u"Starting backlog for " + show.name + " season " + str(
                s) + " episode " + str(e) + " because some eps were set to wanted")


class TraktChecker():

    def __init__(self):
        self.todoWanted = []
        self.trakt_api = TraktAPI(sickbeard.TRAKT_API_KEY, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD, sickbeard.TRAKT_DISABLE_SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)
        self.todoBacklog = []
        self.ShowWatchlist = []
        self.EpisodeWatchlist = []

    def run(self, force=False):
        if not sickbeard.USE_TRAKT:
            logger.log(u"Trakt integration disabled, quit", logger.DEBUG)
            return

        # add shows from trakt.tv watchlist
        if sickbeard.TRAKT_SYNC_WATCHLIST:
            self.todoWanted = []  # its about to all get re-added
            if len(sickbeard.ROOT_DIRS.split('|')) < 2:
                logger.log(u"No default root directory", logger.ERROR)
                return

            try:
                self.syncWatchlist()
            except Exception:
                logger.log(traceback.format_exc(), logger.DEBUG)

            try:
                # sync trakt.tv library with sickrage library
                if sickbeard.TRAKT_SYNC:
                    self.syncLibrary()
            except Exception:
                logger.log(traceback.format_exc(), logger.DEBUG) 

    def findShow(self, indexer, indexerid):
        traktShow = None

        try:
            library = self.trakt_api.traktRequest("sync/collection/shows") or []

            if not library:
                logger.log(u"Could not connect to trakt service, aborting library check", logger.ERROR)
                return

            if not len(library):
                logger.log(u"No shows found in your library, aborting library update", logger.DEBUG)
                return

            traktShow = filter(lambda x: int(indexerid) in [int(x['show']['ids']['tvdb'] or 0), int(x['show']['ids']['tvrage'] or 0)], library)
        except traktException as e:
            logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)

        return traktShow

    def syncLibrary(self):
        logger.log(u"Syncing Trakt.tv show library", logger.DEBUG)

        for myShow in sickbeard.showList:
            self.addShowToTraktLibrary(myShow)

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

            logger.log(u"Removing " + show_obj.name + " from trakt.tv library", logger.DEBUG)
            try:
                self.trakt_api.traktRequest("sync/collection/remove", data, method='POST')
            except traktException as e:
                logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)
                pass

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
            logger.log(u"Adding " + show_obj.name + " to trakt.tv library", logger.DEBUG)

            try:
                self.trakt_api.traktRequest("sync/collection", data, method='POST')
            except traktException as e:
                logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)
                return

    def syncWatchlist(self):

        logger.log(u"Syncing Trakt.tv show watchlist", logger.DEBUG)

        logger.log(u"Getting ShowWatchlist", logger.DEBUG)
        if self._getShowWatchlist():
            self.addShowToTraktWatchList()
            self.updateShows()

        logger.log(u"Getting EpisodeWatchlist", logger.DEBUG)
        if self._getEpisodeWatchlist():
            self.removeEpisodeFromTraktWatchList()
            self.addEpisodeToTraktWatchList()
            self.updateEpisodes()

    def removeEpisodeFromTraktWatchList(self):

        logger.log(u"Start looking if some episode has to be removed from watchlist", logger.DEBUG)

        if not len(self.EpisodeWatchlist):
            logger.log(u"No episode found in your watchlist, aborting watchlist update", logger.DEBUG)
            return True

        trakt_data = []
        for episode in self.EpisodeWatchlist:
            tvdb_id = int(episode['show']['ids']['tvdb'])
            tvrage_id = int(episode['show']['ids']['tvrage'] or 0)
            newShow = helpers.findCertainShow(sickbeard.showList, [tvdb_id, tvrage_id])
            if newShow is not None:
                ep_obj = newShow.getEpisode(int(episode['episode']['season']), int(episode['episode']['number']))
                if ep_obj is not None:
                    if ep_obj.status != WANTED and ep_obj.status != UNKNOWN and ep_obj.status not in Quality.SNATCHED and ep_obj.status not in Quality.SNATCHED_PROPER:
                        logger.log(u"Removing episode: Indexer " + str(newShow.indexer) + ", indexer_id " + str(newShow.indexerid) + ", Title " + str(newShow.name) + ", Season " + str(episode['episode']['season']) + ", Episode " + str(episode['episode']['number']) + ", Status " + str(ep_obj.status) + " from Watchlist", logger.DEBUG)
                        trakt_data.append((ep_obj.season, ep_obj.episode))
                else:
                    logger.log(u"Episode: Indexer " + str(newShow.indexer) + ", indexer_id " + str(newShow.indexerid) + ", Title " + str(newShow.name) + ", Season " + str(episode['episode']["season"]) + ", Episode" + str(episode['episode']["number"]) + " not in Sickberad ShowList", logger.DEBUG)
                    continue
            else:
                logger.log(u"Show: tvdb_id " + str(episode['show']['ids']['tvdb']) + ", Title " + str(episode['show']['title']) + " not in Sickberad ShowList", logger.DEBUG)
                continue

        if len(trakt_data):
            data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)
            notifiers.trakt_notifier.update_watchlist(newShow, data_episode=data, update="remove")
            self._getEpisodeWatchlist()

        logger.log(u"Stop looking if some episode has to be removed from watchlist", logger.DEBUG)

    def addEpisodeToTraktWatchList(self):

        if sickbeard.TRAKT_SYNC_WATCHLIST and sickbeard.USE_TRAKT:
            logger.log(u"Start looking if some WANTED episode need to be added to watchlist", logger.DEBUG)

            myDB = db.DBConnection()
            sql_selection='select tv_shows.indexer, showid, show_name, season, episode from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid and tv_episodes.status in ('+','.join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER + [WANTED]])+')'
            episodes = myDB.select(sql_selection)
            if episodes is not None:
                trakt_data = []
                for cur_episode in episodes:
                    newShow = helpers.findCertainShow(sickbeard.showList, int(cur_episode["showid"])) 
                    if not self.check_watchlist(newShow, cur_episode["season"], cur_episode["episode"]):
                        logger.log(u"Episode: Indexer " + str(cur_episode["indexer"]) + ", indexer_id " + str(cur_episode["showid"])+ ", Title " +  str(cur_episode["show_name"]) + " " + str(cur_episode["season"]) + "x" + str(cur_episode["episode"]) + " should be added to watchlist", logger.DEBUG)
                        trakt_data.append((cur_episode["season"], cur_episode["episode"]))

                if len(trakt_data):
                    data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)
                    notifiers.trakt_notifier.update_watchlist(newShow, data_episode=data)
                    self._getEpisodeWatchlist()

            logger.log(u"Stop looking if some WANTED episode need to be added to watchlist", logger.DEBUG)

    def addShowToTraktWatchList(self):

        if sickbeard.TRAKT_SYNC_WATCHLIST and sickbeard.USE_TRAKT:
            logger.log(u"Start looking if some show need to be added to watchlist", logger.DEBUG)

            if sickbeard.showList is not None:
                trakt_data = []
                for show in sickbeard.showList:
                    if not self.check_watchlist(show):
                        logger.log(u"Show: Indexer " + str(show.indexer) + ", indexer_id " + str(show.indexerid) + ", Title " +  str(show.name) + " should be added to watchlist", logger.DEBUG)
                        trakt_data.append((show.indexer, show.indexerid, show.name, show.startyear))

                if len(trakt_data):
                    data = notifiers.trakt_notifier.trakt_show_data_generate(trakt_data)
                    notifiers.trakt_notifier.update_watchlist(data_show=data)
                    self._getShowWatchlist()

            logger.log(u"Stop looking if some show need to be added to watchlist", logger.DEBUG)

    def updateShows(self):
        logger.log(u"Starting trakt show watchlist check", logger.DEBUG)

        if not len(self.ShowWatchlist):
            logger.log(u"No shows found in your watchlist, aborting watchlist update", logger.DEBUG)
            return

        for show in self.ShowWatchlist:
            indexer = int(sickbeard.TRAKT_DEFAULT_INDEXER)
            if indexer == 2:
                indexer_id = int(show["show"]["ids"]["tvrage"])
            else:
                indexer_id = int(show["show"]["ids"]["tvdb"])

            if int(sickbeard.TRAKT_METHOD_ADD) != 2:
                self.addDefaultShow(indexer, indexer_id, show["show"]["title"], SKIPPED)
            else:
                self.addDefaultShow(indexer, indexer_id, show["show"]["title"], WANTED)

            if int(sickbeard.TRAKT_METHOD_ADD) == 1:
                newShow = helpers.findCertainShow(sickbeard.showList, indexer_id)
                if newShow is not None:
                    setEpisodeToWanted(newShow, 1, 1)
                else:
                    self.todoWanted.append((indexer_id, 1, 1))

    def updateEpisodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        logger.log(u"Starting trakt episode watchlist check", logger.DEBUG)

        if not len(self.EpisodeWatchlist):
            logger.log(u"No episode found in your watchlist, aborting episode update", logger.DEBUG)
            return

        managed_show = []
        for show in self.EpisodeWatchlist:
            indexer = int(sickbeard.TRAKT_DEFAULT_INDEXER)
            if indexer == 2:
                indexer_id = int(show["show"]["ids"]["tvrage"])
            else:
                indexer_id = int(show["show"]["ids"]["tvdb"])

            newShow = helpers.findCertainShow(sickbeard.showList, indexer_id)
            try:
                if newShow is None:
                    if indexer_id not in managed_show:
                        self.addDefaultShow(indexer, indexer_id, show["show"]["title"], SKIPPED)
                        managed_show.append(indexer_id)
                    self.todoWanted.append((indexer_id, show['episode']['season'], show['episode']['number']))
                else:
                    if newShow.indexer == indexer:
                        setEpisodeToWanted(newShow, show['episode']['season'], show['episode']['number'])
            except TypeError:
                logger.log(u"Could not parse the output from trakt for " + show["show"]["title"], logger.DEBUG)

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
                showPath = ek.ek(os.path.join, location, helpers.sanitizeFileName(name))
                dir_exists = helpers.makeDir(showPath)
                if not dir_exists:
                    logger.log(u"Unable to create the folder " + showPath + ", can't add the show", logger.ERROR)
                    return
                else:
                    helpers.chmodAsParent(showPath)

                sickbeard.showQueueScheduler.action.addShow(int(indexer), int(indexer_id), showPath, status,
                                                            int(sickbeard.QUALITY_DEFAULT),
                                                            int(sickbeard.FLATTEN_FOLDERS_DEFAULT),
                                                            paused=sickbeard.TRAKT_START_PAUSED)
            else:
                logger.log(u"There was an error creating the show, no root directory setting found", logger.ERROR)
                return

    def manageNewShow(self, show):
        logger.log(u"Checking if trakt watch list wants to search for episodes from new show " + show.name, logger.DEBUG)
        episodes = [i for i in self.todoWanted if i[0] == show.indexerid]
        for episode in episodes:
            self.todoWanted.remove(episode)
            setEpisodeToWanted(show, episode[1], episode[2])

    def _getShowWatchlist(self):

        try:
            self.ShowWatchlist = self.trakt_api.traktRequest("sync/watchlist/shows")
        except traktException as e:
            logger.log(u"Could not connect to trakt service, cannot download Show Watchlist: %s" % ex(e), logger.ERROR)
            return False

        return True

    def _getEpisodeWatchlist(self):

        try:
            self.EpisodeWatchlist = self.trakt_api.traktRequest("sync/watchlist/episodes")
        except traktException as e:
            logger.log(u"Could not connect to trakt service, cannot download Episode Watchlist: %s" % ex(e), logger.WARNING)
            return False

        return True

    def check_watchlist (self, show_obj, season=None, episode=None):

        found = False
        if episode is not None:
            watchlist = self.EpisodeWatchlist
        else:
            watchlist = self.ShowWatchlist

        trakt_id = sickbeard.indexerApi(show_obj.indexer).config['trakt_id']
        
        for watchlist_el in watchlist:

            if trakt_id == 'tvdb_id':
                indexer_id = int(watchlist_el['show']['ids']["tvdb"])
            else:
                if not watchlist_el['show']['ids']["tvrage"] is None:
                   indexer_id = int(watchlist_el['show']['ids']["tvrage"])
                else:
                    indexer_id = 0
                    
            if indexer_id == show_obj.indexerid and season is None and episode is None:
                found=True
                break
            elif indexer_id == show_obj.indexerid and season == watchlist_el['episode']["season"] and episode == watchlist_el['episode']["number"]:
                found=True
                break

        return found

class TraktRolling():

    def __init__(self):
        self.trakt_api = TraktAPI(sickbeard.TRAKT_API_KEY, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD, sickbeard.TRAKT_DISABLE_SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)
        self.EpisodeWatched = []

    def run(self, force=False):
        if not (sickbeard.TRAKT_USE_ROLLING_DOWNLOAD and sickbeard.USE_TRAKT):
            return

        logger.log(u"Start getting list from Traktv", logger.DEBUG)

        logger.log(u"Getting EpisodeWatched", logger.DEBUG)
        if not self._getEpisodeWatched():
            return

        self.updateWantedList()

    def _getEpisodeWatched(self):

        try:
            self.EpisodeWatched = self.trakt_api.traktRequest("sync/watched/shows")
        except traktException as e:
            logger.log(u"Could not connect to trakt service, cannot download show from library: %s" % ex(e), logger.ERROR)
            return False

        return True

    def refreshEpisodeWatched(self):

       if not (sickbeard.TRAKT_USE_ROLLING_DOWNLOAD and sickbeard.USE_TRAKT):
           return False

       if not self._getEpisodeWatched():
           return False

       return True

    def updateWantedList(self, indexer_id = None):

        if not (sickbeard.TRAKT_USE_ROLLING_DOWNLOAD and sickbeard.USE_TRAKT):
            return False

        if not self.refreshEpisodeWatched():
            return False

        num_of_download = sickbeard.TRAKT_ROLLING_NUM_EP

        if not len(self.EpisodeWatched) or num_of_download == 0:
            return True

        logger.log(u"Start looking if having " + str(num_of_download) + " episode(s) not watched", logger.DEBUG)

        myDB = db.DBConnection()

        sql_selection="SELECT indexer, indexer_id, imdb_id, show_name, season, episode, paused FROM (SELECT * FROM tv_shows s,tv_episodes e WHERE s.indexer_id = e.showid) T1 WHERE T1.episode_id IN (SELECT T2.episode_id FROM tv_episodes T2 WHERE T2.showid = T1.indexer_id and T2.status in (?) and T2.season!=0 and airdate is not null ORDER BY T2.season,T2.episode LIMIT 1)"

        if indexer_id is not None:
            sql_selection=sql_selection + " and indexer_id = " + str(indexer_id)
        else:
            sql_selection=sql_selection + " and T1.paused = 0"

	    sql_selection=sql_selection + " ORDER BY T1.show_name,season,episode"

        results = myDB.select(sql_selection,[SKIPPED])

        for cur_result in results:

            indexer_id = str(cur_result["indexer_id"])
            show_name = (cur_result["show_name"])
            sn_sb = cur_result["season"]
            ep_sb = cur_result["episode"]

            newShow = helpers.findCertainShow(sickbeard.showList, int(indexer_id))
            imdb_id = cur_result["imdb_id"]

            num_of_ep=0
            season = 1
            episode = 0

            last_per_season = self.trakt_api.traktRequest("shows/" + str(imdb_id) + "/seasons?extended=full")
            if not last_per_season:
                logger.log(u"Could not connect to trakt service, cannot download last season for show", logger.ERROR)
                return False

            logger.log(u"indexer_id: " + str(indexer_id) + ", Show: " + show_name + " - First skipped Episode: Season " + str(sn_sb) + ", Episode " + str(ep_sb), logger.DEBUG)

            if imdb_id not in (show['show']['ids']['imdb'] for show in self.EpisodeWatched):
                logger.log(u"Show not founded in Watched list", logger.DEBUG)
                if (sn_sb*100+ep_sb) > 100+num_of_download:
                    logger.log(u"First " + str(num_of_download) + " episode already downloaded", logger.DEBUG)
                    continue
                else:
                    sn_sb = 1
                    ep_sb = 1
                    num_of_ep = num_of_download
            else:
                logger.log(u"Show founded in Watched list", logger.DEBUG)

                show_watched = [show for show in self.EpisodeWatched if show['show']['ids']['imdb'] == imdb_id]

                season = show_watched[0]['seasons'][-1]['number']
                episode = show_watched[0]['seasons'][-1]['episodes'][-1]['number']
                logger.log(u"Last watched, Season: " + str(season) + " - Episode: " + str(episode), logger.DEBUG)

                num_of_ep = num_of_download - (self._num_ep_for_season(last_per_season, sn_sb, ep_sb) - self._num_ep_for_season(last_per_season, season, episode)) + 1

            logger.log(u"Number of Episode to Download: " + str(num_of_ep), logger.DEBUG)

            s = sn_sb
            e = ep_sb

            for x in range(0,num_of_ep):

                last_s = [last_x_s for last_x_s in last_per_season if last_x_s['number'] == s]
                if last_s is None:
                    break
                if episode == 0 or (s*100+e) <= (int(last_s[0]['number'])*100+int(last_s[0]['episode_count'])): 

                    if (s*100+e) > (season*100+episode):
                        if not cur_result["paused"]:
                            if newShow is not None:
                                setEpisodeToWanted(newShow, s, e)
                            else:
                                self.todoWanted.append(int(indexer_id), s, e)
                    else:
                        self.setEpisodeToDefaultWatched(newShow, s, e)

                    if (s*100+e) == (int(last_s[0]['number'])*100+int(last_s[0]['episode_count'])):
                        s = s + 1
                        e = 1
                    else:
                        e = e + 1

        logger.log(u"Stop looking if having " + str(num_of_download) + " episode not watched", logger.DEBUG)
        return True

    def setEpisodeToDefaultWatched(self, show, s, e):
        """
        Sets an episode to ignored, only if it is currently skipped or failed
        """
        epObj = show.getEpisode(int(s), int(e))
        if epObj:

            with epObj.lock:
                if epObj.status != SKIPPED:
                    return

                logger.log(u"Setting episode s" + str(s) + "e" + str(e) + " of show " + show.name + " to " + statusStrings[sickbeard.EP_DEFAULT_DELETED_STATUS])

                epObj.status = sickbeard.EP_DEFAULT_DELETED_STATUS
                epObj.saveToDB()

    def _num_ep_for_season(self, show, season, episode):

        num_ep = 0

        for curSeason in show:

            sn = int(curSeason["number"])
            ep = int(curSeason["episode_count"])

            if (sn < season):
                num_ep = num_ep + (ep)
            elif (sn == season):
                num_ep = num_ep + episode
            elif (sn == 0):
                continue
            else:
                continue

        return num_ep

