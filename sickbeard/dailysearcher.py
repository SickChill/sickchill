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
                    myDB = db.DBConnection()
                    sql_selection="SELECT show_name, indexer_id, season, episode, paused FROM (SELECT * FROM tv_shows s,tv_episodes e WHERE s.indexer_id = e.showid) T1 WHERE T1.paused = 0 and T1.episode_id IN (SELECT T2.episode_id FROM tv_episodes T2 WHERE T2.showid = T1.indexer_id and T2.status in (?) ORDER BY T2.season,T2.episode LIMIT 1) and airdate is not null and indexer_id = ? ORDER BY T1.show_name,season,episode"
                    results = myDB.select(sql_selection, [common.SKIPPED, sqlEp["showid"]])
                    if not sickbeard.TRAKT_USE_ROLLING_DOWNLOAD:
                        if ep.season == 0: 
                            logger.log(u"New episode " + ep.prettyName() + " airs today, setting status to SKIPPED, due to trakt integration")
                            ep.status = common.SKIPPED
                        else:  
                            logger.log(u"New episode " + ep.prettyName() + " airs today, setting status to WANTED")
                            ep.status = common.WANTED                         
                    else:
                        sn_sk = results[0]["season"]
                        ep_sk = results[0]["episode"]
                        if (int(sn_sk)*100+int(ep_sk)) < (int(sqlEp["season"])*100+int(sqlEp["episode"])):
                            logger.log(u"New episode " + ep.prettyName() + " airs today, setting status to SKIPPED, due to trakt integration")
                            ep.status = common.SKIPPED
                        else:
                            if ep.season == 0: 
                                logger.log(u"New episode " + ep.prettyName() + " airs today, setting status to SKIPPED, due to trakt integration")
                                ep.status = common.SKIPPED
                            else:
                                logger.log(u"New episode " + ep.prettyName() + " airs today, setting status to WANTED")
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
