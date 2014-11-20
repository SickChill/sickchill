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
from sickbeard import encodingKludge as ek
from sickbeard import logger
from sickbeard import helpers
from sickbeard import search_queue
from sickbeard.common import SKIPPED, WANTED
from lib.trakt import *


class TraktChecker():
    def __init__(self):
        self.todoWanted = []

    def run(self, force=False):
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

        if not len(library):
            logger.log(u"No shows found in your library, aborting library update", logger.DEBUG)
            return

        return filter(lambda x: int(indexerid) in [int(x['tvdb_id']) or 0, int(x['tvrage_id'])] or 0, library)

    def syncLibrary(self):
        logger.log(u"Syncing Trakt.tv show library", logger.DEBUG)

        for myShow in sickbeard.showList:
            self.addShowToTraktLibrary(myShow)

    def removeShowFromTraktLibrary(self, show_obj):
        data = {}
        if self.findShow(show_obj.indexer, show_obj.indexerid):
            # URL parameters
            data['tvdb_id'] = helpers.mapIndexersToShow(show_obj)[1]
            data['title'] = show_obj.name
            data['year'] = show_obj.startyear

        if len(data):
            logger.log(u"Removing " + show_obj.name + " from trakt.tv library", logger.DEBUG)
            TraktCall("show/unlibrary/%API%", sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD,
                      data)

    def addShowToTraktLibrary(self, show_obj):
        """
        Sends a request to trakt indicating that the given show and all its episodes is part of our library.

        show_obj: The TVShow object to add to trakt
        """

        data = {}

        if not self.findShow(show_obj.indexer, show_obj.indexerid):
            # URL parameters
            data['tvdb_id'] = helpers.mapIndexersToShow(show_obj)[1]
            data['title'] = show_obj.name
            data['year'] = show_obj.startyear

        if len(data):
            logger.log(u"Adding " + show_obj.name + " to trakt.tv library", logger.DEBUG)
            TraktCall("show/library/%API%", sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD,
                      data)

    def updateShows(self):
        logger.log(u"Starting trakt show watchlist check", logger.DEBUG)
        watchlist = TraktCall("user/watchlist/shows.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)

        if not watchlist:
            logger.log(u"Could not connect to trakt service, aborting watchlist update", logger.ERROR)
            return

        if not len(watchlist):
            logger.log(u"No shows found in your watchlist, aborting watchlist update", logger.DEBUG)
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
                else:
                    self.todoWanted.append((indexer_id, 1, 1))

    def updateEpisodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        logger.log(u"Starting trakt episode watchlist check", logger.DEBUG)
        watchlist = TraktCall("user/watchlist/episodes.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)

        if not watchlist:
            logger.log(u"Could not connect to trakt service, aborting watchlist update", logger.ERROR)
            return

        if not len(watchlist):
            logger.log(u"No shows found in your watchlist, aborting watchlist update", logger.DEBUG)
            return

        for show in watchlist:
            indexer = int(sickbeard.TRAKT_DEFAULT_INDEXER)
            if indexer == 2:
                indexer_id = int(show["tvrage_id"])
            else:
                indexer_id = int(show["tvdb_id"])

            self.addDefaultShow(indexer, indexer_id, show["title"], SKIPPED)
            newShow = helpers.findCertainShow(sickbeard.showList, indexer_id)

            try:
                if newShow and newShow.indexer == indexer:
                    for episode in show["episodes"]:
                        if newShow is not None:
                            self.setEpisodeToWanted(newShow, episode["season"], episode["number"])
                        else:
                            self.todoWanted.append((indexer_id, episode["season"], episode["number"]))
            except TypeError:
                logger.log(u"Could not parse the output from trakt for " + show["title"], logger.DEBUG)

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

    def setEpisodeToWanted(self, show, s, e):
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

    def manageNewShow(self, show):
        logger.log(u"Checking if trakt watch list wants to search for episodes from new show " + show.name, logger.DEBUG)
        episodes = [i for i in self.todoWanted if i[0] == show.indexerid]
        for episode in episodes:
            self.todoWanted.remove(episode)
            self.setEpisodeToWanted(show, episode[1], episode[2])
