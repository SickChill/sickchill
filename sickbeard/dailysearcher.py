# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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


import datetime
import threading

import sickbeard
from sickbeard import logger
from sickbeard import db
from sickbeard import common
from sickbeard import helpers
from sickbeard import network_timezones
from sickrage.helper.exceptions import MultipleShowObjectsException


class DailySearcher():
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the daily searcher, queuing selected episodes for search

        :param force: Force search
        """
        if self.amActive:
            return

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
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE status = ? AND season > 0 AND (airdate <= ? and airdate > 1)",
                                 [common.UNAIRED, curDate])

        sql_l = []
        show = None

        for sqlEp in sqlResults:
            try:
                if not show or int(sqlEp["showid"]) != show.indexerid:
                    show = helpers.findCertainShow(sickbeard.showList, int(sqlEp["showid"]))

                # for when there is orphaned series in the database but not loaded into our showlist
                if not show or show.paused:
                    continue

            except MultipleShowObjectsException:
                logger.log(u"ERROR: expected to find a single show matching " + str(sqlEp['showid']))
                continue

            if show.airs and show.network:
                # This is how you assure it is always converted to local time
                air_time = network_timezones.parse_date_time(sqlEp['airdate'], show.airs, show.network).astimezone(network_timezones.sb_timezone)

                # filter out any episodes that haven't started airing yet,
                # but set them to the default status while they are airing
                # so they are snatched faster
                if air_time > curTime:
                    continue

            ep = show.getEpisode(int(sqlEp["season"]), int(sqlEp["episode"]))
            with ep.lock:
                if ep.season == 0:
                    logger.log(u"New episode " + ep.prettyName() + " airs today, setting status to SKIPPED because is a special season")
                    ep.status = common.SKIPPED
                else:
                    logger.log(u"New episode %s airs today, setting to default episode status for this show: %s" % (ep.prettyName(), common.statusStrings[ep.show.default_ep_status]))
                    ep.status = ep.show.default_ep_status

                sql_l.append(ep.get_sql())

        if len(sql_l) > 0:
            myDB = db.DBConnection()
            myDB.mass_action(sql_l)
        else:
            logger.log(u"No new released episodes found ...")

        # queue episode for daily search
        dailysearch_queue_item = sickbeard.search_queue.DailySearchQueueItem()
        sickbeard.searchQueueScheduler.action.add_item(dailysearch_queue_item)

        self.amActive = False
