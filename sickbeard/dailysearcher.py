# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement
import time
import datetime
import threading
import traceback

import sickbeard
from sickbeard import logger
from sickbeard import db
from sickbeard import common
from sickbeard import helpers
from sickbeard import exceptions
from sickbeard.exceptions import ex
from sickbeard.search import pickBestResult, snatchEpisode
from sickbeard import generic_queue


class DailySearcher():
    def __init__(self):
        self.lock = threading.Lock()

        self.amActive = False

    def run(self):
        self.amActive = True
        self._changeUnairedEpisodes()

        logger.log(u"Searching for todays new releases ...")
        foundResults = self.searchForNeededEpisodes()

        if not len(foundResults):
            logger.log(u"No needed episodes found on the RSS feeds")
        else:
            for curResult in foundResults:
                snatchEpisode(curResult)

        self.amActive = False

    def _changeUnairedEpisodes(self):

        logger.log(u"Setting todays new releases to status WANTED")

        curDate = datetime.date.today().toordinal()

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE status = ? AND airdate < ?",
                                 [common.UNAIRED, curDate])

        for sqlEp in sqlResults:

            try:
                show = helpers.findCertainShow(sickbeard.showList, int(sqlEp["showid"]))
            except exceptions.MultipleShowObjectsException:
                logger.log(u"ERROR: expected to find a single show matching " + sqlEp["showid"])
                return None

            if show == None:
                logger.log(u"Unable to find the show with ID " + str(
                    sqlEp["showid"]) + " in your show list! DB value was " + str(sqlEp), logger.ERROR)
                return None

            ep = show.getEpisode(sqlEp["season"], sqlEp["episode"])
            with ep.lock:
                if ep.show.paused:
                    ep.status = common.SKIPPED
                else:
                    ep.status = common.WANTED
                ep.saveToDB()

    def searchForNeededEpisodes(self):

        logger.log(u"Searching ESS Cache for any needed new episodes")

        foundResults = {}

        didSearch = False

        # ask all providers for any episodes it finds
        for curProvider in [x for x in sickbeard.providers.sortedProviderList() if x.isActive()]:

            try:
                curFoundResults = curProvider.searchRSS()
            except exceptions.AuthException, e:
                logger.log(u"Authentication error: " + ex(e), logger.ERROR)
                continue
            except Exception, e:
                logger.log(u"Error while searching " + curProvider.name + ", skipping: " + ex(e), logger.ERROR)
                logger.log(traceback.format_exc(), logger.DEBUG)
                continue

            didSearch = True

            # pick a single result for each episode, respecting existing results
            for curEp in curFoundResults:

                if curEp.show.paused:
                    logger.log(
                        u"Show " + curEp.show.name + " is paused, ignoring all RSS items for " + curEp.prettyName(),
                        logger.DEBUG)
                    continue

                # find the best result for the current episode
                bestResult = None
                for curResult in curFoundResults[curEp]:
                    if not bestResult or bestResult.quality < curResult.quality:
                        bestResult = curResult

                bestResult = pickBestResult(curFoundResults[curEp], curEp.show)

                # if all results were rejected move on to the next episode
                if not bestResult:
                    logger.log(u"All found results for " + curEp.prettyName() + " were rejected.", logger.DEBUG)
                    continue

                # if it's already in the list (from another provider) and the newly found quality is no better then skip it
                if curEp in foundResults and bestResult.quality <= foundResults[curEp].quality:
                    continue

                foundResults[curEp] = bestResult

        if not didSearch:
            logger.log(
                u"No NZB/Torrent providers found or enabled in the sickbeard config. Please check your settings.",
                logger.ERROR)

        return foundResults.values()