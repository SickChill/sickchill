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
from sickbeard import network_timezones
from sickbeard.exceptions import ex


class DailySearcher():
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):

        self.amActive = True

        logger.log(u"Searching for new released episodes ...")

        if not network_timezones.network_dict:
            network_timezones.update_network_dict()

        if network_timezones.network_dict:
            curDate = (datetime.date.today() + datetime.timedelta(days=1)).toordinal()
        else:
            curDate = (datetime.date.today() + datetime.timedelta(days=2)).toordinal()

        curTime = datetime.datetime.now(network_timezones.sb_timezone)

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE status = ? AND season > 0 AND airdate <= ?",
                                 [common.UNAIRED, curDate])

        sql_l = []
        show = None

        for sqlEp in sqlResults:
            try:
                if not show or int(sqlEp["showid"]) != show.indexerid:
                    show = helpers.findCertainShow(sickbeard.showList, int(sqlEp["showid"]))

                # for when there is orphaned series in the database but not loaded into our showlist
                if not show:
                    continue

            except exceptions.MultipleShowObjectsException:
                logger.log(u"ERROR: expected to find a single show matching " + str(sqlEp['showid']))
                continue

            try:
                end_time = network_timezones.parse_date_time(sqlEp['airdate'], show.airs,
                                                             show.network) + datetime.timedelta(
                    minutes=helpers.tryInt(show.runtime, 60))
                # filter out any episodes that haven't aried yet
                if end_time > curTime:
                    continue
            except:
                # if an error occured assume the episode hasn't aired yet
                continue

            ep = show.getEpisode(int(sqlEp["season"]), int(sqlEp["episode"]))
            with ep.lock:
                if ep.show.paused:
                    ep.status = common.SKIPPED
                else:
                    ep.status = common.WANTED

                sql_l.append(ep.get_sql())
        else:
            logger.log(u"No new released episodes found ...")

        if len(sql_l) > 0:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)

        # queue episode for daily search
        dailysearch_queue_item = sickbeard.search_queue.DailySearchQueueItem()
        sickbeard.searchQueueScheduler.action.add_item(dailysearch_queue_item)

        self.amActive = False