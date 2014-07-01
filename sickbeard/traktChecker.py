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
import time
import os

import sickbeard
from sickbeard import encodingKludge as ek
from sickbeard import logger
from sickbeard import helpers
from sickbeard import search_queue
from sickbeard import db
from sickbeard.common import SNATCHED, SNATCHED_PROPER, DOWNLOADED, SKIPPED, UNAIRED, IGNORED, ARCHIVED, WANTED, UNKNOWN
from lib.trakt import *


class TraktChecker():
    def __init__(self):
        self.todoWanted = []
        self.todoBacklog = []

    def __del__(self):
        pass

    def run(self, force=False):
        # add shows from trakt.tv watchlist
        if sickbeard.TRAKT_USE_WATCHLIST:
            self.todoWanted = []  #its about to all get re-added
            if len(sickbeard.ROOT_DIRS.split('|')) < 2:
                logger.log(u"No default root directory", logger.ERROR)
                return
            self.updateShows()
            self.updateEpisodes()

        # sync trakt.tv library with sickrage library
        if sickbeard.TRAKT_SYNC:
            self.syncLibrary()

    def findShow(self, indexerid):
        library = TraktCall("user/library/shows/all.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API,
                            sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)

        results = filter(lambda x: int(x['tvdb_id']) == int(indexerid), library)
        if len(results) == 0:
            return None
        else:
            return results[0]

    def syncLibrary(self):
        logger.log(u"Syncing library to trakt.tv show library", logger.DEBUG)
        for myShow in sickbeard.showList:
            self.addShowToTraktLibrary(myShow)

    def removeShowFromTraktLibrary(self, show_obj):
        if not self.findShow(show_obj.indexerid):
            return

        # URL parameters
        data = {
            'tvdb_id': show_obj.indexerid,
            'title': show_obj.name,
            'year': show_obj.startyear,
        }

        if data is not None:
            logger.log(u"Removing " + show_obj.name + " from trakt.tv library", logger.DEBUG)
            TraktCall("show/unlibrary/%API%", sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD, data)

    def addShowToTraktLibrary(self, show_obj):
        """
        Sends a request to trakt indicating that the given show and all its episodes is part of our library.

        show_obj: The TVShow object to add to trakt
        """

        if self.findShow(show_obj.indexerid):
           return

        # URL parameters
        data = {
            'tvdb_id': show_obj.indexerid,
            'title': show_obj.name,
            'year': show_obj.startyear,
        }

        if data is not None:
            logger.log(u"Adding " + show_obj.name + " to trakt.tv library", logger.DEBUG)
            TraktCall("show/library/%API%", sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD, data)

    def updateShows(self):
        logger.log(u"Starting trakt show watchlist check", logger.DEBUG)
        watchlist = TraktCall("user/watchlist/shows.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API,
                              sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)
        if watchlist is None:
            logger.log(u"Could not connect to trakt service, aborting watchlist update", logger.ERROR)
            return
        for show in watchlist:
            if int(sickbeard.TRAKT_METHOD_ADD) != 2:
                self.addDefaultShow(show["tvdb_id"], show["title"], SKIPPED)
            else:
                self.addDefaultShow(show["tvdb_id"], show["title"], WANTED)

            if int(sickbeard.TRAKT_METHOD_ADD) == 1:
                newShow = helpers.findCertainShow(sickbeard.showList, int(show["tvdb_id"]))
                if newShow is not None:
                    self.setEpisodeToWanted(newShow, 1, 1)
                    self.startBacklog(newShow)
                else:
                    self.todoWanted.append((int(show["tvdb_id"]), 1, 1))
            self.todoWanted.append((int(show["tvdb_id"]), -1, -1))  #used to pause new shows if the settings say to

    def updateEpisodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        logger.log(u"Starting trakt episode watchlist check", logger.DEBUG)
        watchlist = TraktCall("user/watchlist/episodes.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API,
                              sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)
        if watchlist is None:
            logger.log(u"Could not connect to trakt service, aborting watchlist update", logger.ERROR)
            return
        for show in watchlist:
            self.addDefaultShow(int(show["tvdb_id"]), show["title"], SKIPPED)
            newShow = helpers.findCertainShow(sickbeard.showList, int(show["tvdb_id"]))
            for episode in show["episodes"]:
                if newShow is not None:
                    self.setEpisodeToWanted(newShow, episode["season"], episode["number"])
                else:
                    self.todoWanted.append((int(show["tvdb_id"]), episode["season"], episode["number"]))
            self.startBacklog(newShow)

    def addDefaultShow(self, indexerid, name, status):
        """
        Adds a new show with the default settings
        """
        if helpers.findCertainShow(sickbeard.showList, int(indexerid)):
            return

        logger.log(u"Adding show " + str(indexerid))
        root_dirs = sickbeard.ROOT_DIRS.split('|')
        location = root_dirs[int(root_dirs[0]) + 1]

        showPath = ek.ek(os.path.join, location, helpers.sanitizeFileName(name))
        dir_exists = helpers.makeDir(showPath)
        if not dir_exists:
            logger.log(u"Unable to create the folder " + showPath + ", can't add the show", logger.ERROR)
            return
        else:
            helpers.chmodAsParent(showPath)

        sickbeard.showQueueScheduler.action.addShow(1, int(indexerid), showPath, status,
                                                    int(sickbeard.QUALITY_DEFAULT),
                                                    int(sickbeard.FLATTEN_FOLDERS_DEFAULT))

    def setEpisodeToWanted(self, show, s, e):
        """
        Sets an episode to wanted, only is it is currently skipped
        """
        epObj = show.getEpisode(int(s), int(e))
        if epObj == None:
            return
        with epObj.lock:
            if epObj.status != SKIPPED:
                return
            logger.log(u"Setting episode s" + str(s) + "e" + str(e) + " of show " + show.name + " to wanted")
            # figure out what segment the episode is in and remember it so we can backlog it
            if epObj.show.air_by_date or epObj.show.sports:
                ep_segment = str(epObj.airdate)[:7]
            else:
                ep_segment = epObj.season

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
            logger.log(u"Starting backlog for " + show.name + " season " + str(
                segment[1]) + " because some eps were set to wanted")
            self.todoBacklog.remove(segment)


