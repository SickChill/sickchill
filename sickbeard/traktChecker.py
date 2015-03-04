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
from sickbeard.common import SKIPPED, WANTED, IGNORED, FAILED, statusStrings

from lib.trakt import *
from trakt.exceptions import traktException, traktAuthException, traktServerBusy


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

    def run(self, force=False):
        if not sickbeard.USE_TRAKT:
            logger.log(u"Trakt integration disabled, quit", logger.DEBUG)
            return

        try:
            # add shows from trakt.tv watchlist
            if sickbeard.TRAKT_SYNC_WATCHLIST:
                self.todoWanted = []  # its about to all get re-added
                if len(sickbeard.ROOT_DIRS.split('|')) < 2:
                    logger.log(u"No default root directory", logger.ERROR)
                    return
                self.updateShows()
                self.updateEpisodes()

            # sync trakt.tv library with sickrage library
            if sickbeard.TRAKT_SYNC:
                self.syncLibrary()
        except Exception as e:
            logger.log('Trakt: Error Syncing library. Reason: {0}'.format(str(e)), logger.DEBUG)

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
        except (traktException, traktAuthException, traktServerBusy) as e:
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
            except (traktException, traktAuthException, traktServerBusy) as e:
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
            except (traktException, traktAuthException, traktServerBusy) as e:
                logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)
                return

    def updateShows(self):
        logger.log(u"Starting trakt show watchlist check", logger.DEBUG)

        try:
            watchlist = self.trakt_api.traktRequest("sync/watchlist/shows")
        except (traktException, traktAuthException, traktServerBusy) as e:
            logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)
            return

        if not len(watchlist):
            logger.log(u"No shows found in your watchlist, aborting watchlist update", logger.DEBUG)
            return

        for show in watchlist:
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

        try:
            watchlist = self.trakt_api.traktRequest("sync/watchlist/episodes")
        except (traktException, traktAuthException, traktServerBusy) as e:
            logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)
            return

        if not len(watchlist):
            logger.log(u"No shows found in your watchlist, aborting watchlist update", logger.DEBUG)
            return

        for show in watchlist:
            indexer = int(sickbeard.TRAKT_DEFAULT_INDEXER)
            if indexer == 2:
                indexer_id = int(show["show"]["ids"]["tvrage"])
            else:
                indexer_id = int(show["show"]["ids"]["tvdb"])

            self.addDefaultShow(indexer, indexer_id, show["show"]["title"], SKIPPED)
            newShow = helpers.findCertainShow(sickbeard.showList, indexer_id)

            try:
                if newShow and newShow.indexer == indexer:
                    for episode in show["episode"]:
                        if newShow is not None:
                            setEpisodeToWanted(newShow, episode["season"], episode["number"])
                        else:
                            self.todoWanted.append((indexer_id, episode["season"], episode["number"]))
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

class TraktRolling():

    def __init__(self):
        self.trakt_api = TraktAPI(sickbeard.TRAKT_API_KEY, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD, sickbeard.TRAKT_DISABLE_SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)
        self.EpisodeWatched = []

    def run(self, force=False):
        if not sickbeard.TRAKT_USE_ROLLING_DOWNLOAD:
            logger.log(u"Trakt rolling donwload disabled, quit", logger.DEBUG)
            return

        logger.log(u"Start getting list from Tracktv", logger.DEBUG)

        logger.log(u"Getting EpisodeWatched", logger.DEBUG)
        if not self._getEpisodeWatched():
            return

        self.updateWantedList()

    def _getEpisodeWatched(self):

        try:
            self.EpisodeWatched = self.trakt_api.traktRequest("sync/watched/shows")
        except (traktException, traktAuthException, traktServerBusy) as e:
            logger.log(u"Could not connect to trakt service, cannot download show from library: %s" % ex(e), logger.ERROR)
            return False

        return True

    def refreshEpisodeWatched(self):

       if not self._getEpisodeWatched():
           return False

       return True

    def updateWantedList(self, indexer_id = None):

        #num_of_download = sickbeard.TRAKT_NUM_EP
        num_of_download = 4

        if not len(self.EpisodeWatched) or num_of_download == 0:
            return True

        logger.log(u"Start looking if having " + str(num_of_download) + " episode not watched", logger.DEBUG)

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
                if epObj.status not in (SKIPPED):
                    return

                logger.log(u"Setting episode s"+str(s)+"e"+str(e)+" of show " + show.name + " to " + statusStrings[sickbeard.TRAKT_ROLLING_DEFAULT_WATCHED_STATUS])

                epObj.status = sickbeard.TRAKT_ROLLING_DEFAULT_WATCHED_STATUS
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
