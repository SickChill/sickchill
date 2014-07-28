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

import sickbeard
from sickbeard import encodingKludge as ek
from sickbeard import logger
from sickbeard import helpers
from sickbeard import search_queue
from sickbeard.common import SKIPPED, WANTED
from lib.trakt import *


class TraktChecker():
    def __init__(self):
        self.todoWanted = []
        self.todoBacklog = []

    def run(self, force=False):
        if not sickbeard.USE_TRAKT:
            return

        try:
            # add shows from trakt.tv watchlist
            if sickbeard.TRAKT_USE_WATCHLIST:
                self.todoWanted = []  # its about to all get re-added
                if len(sickbeard.ROOT_DIRS.split('|')) < 2:
                    logger.log(u"No default root directory", logger.ERROR)
                    return
                self.updateShows()
                self.updateEpisodes()

            # sync trakt.tv library with sickrage library
            if sickbeard.TRAKT_SYNC:
                self.syncLibrary()
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

    def findShow(self, indexer, indexerid):
        library = TraktCall("user/library/shows/all.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)

        if not library:
            logger.log(u"Could not connect to trakt service, aborting library check", logger.ERROR)
            return

        return filter(lambda x: int(indexerid) in [int(x.tvdb_id), int(x.tvrage_id)], library)

    def syncLibrary(self):
        logger.log(u"Syncing library to trakt.tv show library", logger.DEBUG)
        if sickbeard.showList:
            for myShow in sickbeard.showList:
                self.addShowToTraktLibrary(myShow)

    def removeShowFromTraktLibrary(self, show_obj):
        if self.findShow(show_obj.indexer, show_obj.indexerid):
            # URL parameters
            data = {}
            if show_obj.indexer == 1:
                data['tvdb_id'] = show_obj.indexerid
                data['title'] = show_obj.name
                data['year'] = show_obj.startyear

            elif show_obj.indexer == 2:
                data['tvrage_id'] = show_obj.indexerid
                data['title'] = show_obj.name
                data['year'] = show_obj.startyear

            if data is not None:
                logger.log(u"Removing " + show_obj.name + " from trakt.tv library", logger.DEBUG)
                TraktCall("show/unlibrary/%API%", sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD,
                          data)

    def addShowToTraktLibrary(self, show_obj):
        """
        Sends a request to trakt indicating that the given show and all its episodes is part of our library.

        show_obj: The TVShow object to add to trakt
        """

        if not self.findShow(show_obj.indexer, show_obj.indexerid):
            # URL parameters
            data = {}
            if show_obj.indexer == 1:
                data['tvdb_id'] = show_obj.indexerid
                data['title'] = show_obj.name
                data['year'] = show_obj.startyear

            elif show_obj.indexer == 2:
                data['tvrage_id'] = show_obj.indexerid
                data['title'] = show_obj.name
                data['year'] = show_obj.startyear

            if data:
                logger.log(u"Adding " + show_obj.name + " to trakt.tv library", logger.DEBUG)
                TraktCall("show/library/%API%", sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD,
                          data)

    def updateShows(self):
        logger.log(u"Starting trakt show watchlist check", logger.DEBUG)
        watchlist = TraktCall("user/watchlist/shows.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)

        if not watchlist:
            logger.log(u"Could not connect to trakt service, aborting watchlist update", logger.ERROR)
            return

        for show in watchlist:
            indexer = int(sickbeard.TRAKT_DEFAULT_INDEXER)
            if indexer == 2:
                indexer_id = int(show["tvrage_id"])
            else:
                indexer_id = int(show["tvdb_id"])

            if int(sickbeard.TRAKT_METHOD_ADD) != 2:
                self.addDefaultShow(indexer, indexer_id, show["title"], SKIPPED)
            else:
                self.addDefaultShow(indexer, indexer_id, show["title"], WANTED)

            if int(sickbeard.TRAKT_METHOD_ADD) == 1:
                newShow = helpers.findCertainShow(sickbeard.showList, indexer_id)
                if newShow is not None:
                    self.setEpisodeToWanted(newShow, 1, 1)
                    self.startBacklog(newShow)
                else:
                    self.todoWanted.append((indexer_id, 1, 1))
            self.todoWanted.append((indexer_id, -1, -1))  # used to pause new shows if the settings say to

    def updateEpisodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        logger.log(u"Starting trakt episode watchlist check", logger.DEBUG)
        watchlist = TraktCall("user/watchlist/episodes.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)

        if not watchlist:
            logger.log(u"Could not connect to trakt service, aborting watchlist update", logger.ERROR)
            return

        for show in watchlist:
            indexer = int(sickbeard.TRAKT_DEFAULT_INDEXER)
            if indexer == 2:
                indexer_id = int(show["tvrage_id"])
            else:
                indexer_id = int(show["tvdb_id"])

            self.addDefaultShow(indexer, indexer_id, show["title"], SKIPPED)
            newShow = helpers.findCertainShow(sickbeard.showList, indexer_id)

            if newShow and int(newShow['indexer']) == indexer:
                for episode in show["episodes"]:
                    if newShow is not None:
                        self.setEpisodeToWanted(newShow, episode["season"], episode["number"])
                    else:
                        self.todoWanted.append((indexer_id, episode["season"], episode["number"]))
                self.startBacklog(newShow)

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
                                                            int(sickbeard.FLATTEN_FOLDERS_DEFAULT))
            else:
                logger.log(u"There was an error creating the show, no root directory setting found", logger.ERROR)
                return

    def setEpisodeToWanted(self, show, s, e):
        """
        Sets an episode to wanted, only is it is currently skipped
        """
        epObj = show.getEpisode(int(s), int(e))
        if epObj:

            ep_segment = {}

            with epObj.lock:
                if epObj.status != SKIPPED:
                    return

                logger.log(u"Setting episode s" + str(s) + "e" + str(e) + " of show " + show.name + " to wanted")
                # figure out what segment the episode is in and remember it so we can backlog it

                if epObj.season in ep_segment:
                    ep_segment[epObj.season].append(epObj)
                else:
                    ep_segment[epObj.season] = [epObj]

                epObj.status = WANTED
                epObj.saveToDB()

                backlog = (show, ep_segment)
                if self.todoBacklog.count(backlog) == 0:
                    self.todoBacklog.append(backlog)


    def manageNewShow(self, show):
        episodes = [i for i in self.todoWanted if i[0] == show.indexerid]
        for episode in episodes:
            self.todoWanted.remove(episode)
            if episode[1] == -1 and sickbeard.TRAKT_START_PAUSED:
                show.paused = 1
                continue
            self.setEpisodeToWanted(show, episode[1], episode[2])
        self.startBacklog(show)

    def startBacklog(self, show):
        segments = [i for i in self.todoBacklog if i[0] == show]
        for segment in segments:
            cur_backlog_queue_item = search_queue.BacklogQueueItem(show, segment[1])
            sickbeard.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

            for season in segment[1]:
                logger.log(u"Starting backlog for " + show.name + " season " + str(
                    season) + " because some eps were set to wanted")
                self.todoBacklog.remove(segment)