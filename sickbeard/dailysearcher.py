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

from __future__ import with_statement

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


class DailySearcher():
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):

        self.amActive = True

        providers = [x for x in sickbeard.providers.sortedProviderList() if x.isActive() and not x.backlog_only]
        for curProviderCount, curProvider in enumerate(providers):

            logger.log(u"Updating [" + curProvider.name + "] RSS cache ...")

            try:
                curProvider.cache.updateCache()
            except exceptions.AuthException, e:
                logger.log(u"Authentication error: " + ex(e), logger.ERROR)
                continue
            except Exception, e:
                logger.log(u"Error while updating cache for " + curProvider.name + ", skipping: " + ex(e), logger.ERROR)
                logger.log(traceback.format_exc(), logger.DEBUG)
                continue

        logger.log(u"Searching for coming episodes and 1 weeks worth of previously WANTED episodes ...")

        fromDate = datetime.date.today() - datetime.timedelta(weeks=1)
        curDate = datetime.date.today()

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE status in (?,?) AND airdate >= ? AND airdate <= ?",
                                 [common.UNAIRED, common.WANTED, fromDate.toordinal(), curDate.toordinal()])

        sql_l = []
        for sqlEp in sqlResults:
            try:
                show = helpers.findCertainShow(sickbeard.showList, int(sqlEp["showid"]))
            except exceptions.MultipleShowObjectsException:
                logger.log(u"ERROR: expected to find a single show matching " + sqlEp["showid"])
                continue

            ep = show.getEpisode(int(sqlEp["season"]), int(sqlEp["episode"]))
            with ep.lock:
                if ep.show.paused:
                    ep.status = common.SKIPPED

                if ep.status == common.UNAIRED:
                    logger.log(u"New episode " + ep.prettyName() + " airs today, setting status to WANTED")
                    ep.status = common.WANTED

                sql_l.append(ep.get_sql())

                if ep.status == common.WANTED:
                    dailysearch_queue_item = sickbeard.search_queue.DailySearchQueueItem(show, [ep])
                    sickbeard.searchQueueScheduler.action.add_item(dailysearch_queue_item)
        else:
            logger.log(u"Could not find any wanted episodes for the last 7 days to search for")

        if len(sql_l) > 0:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)

        self.amActive = False