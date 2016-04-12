# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import datetime
import threading

import sickbeard
from sickbeard import logger
from sickbeard import db
from sickbeard import common
from sickbeard import network_timezones
from sickrage.show.Show import Show
from sickrage.helper.exceptions import MultipleShowObjectsException


class DailySearcher(object):  # pylint:disable=too-few-public-methods
    def __init__(self):
        self.lock = threading.Lock()
        self.am_active = False

    def run(self, force=False):  # pylint:disable=too-many-branches
        """
        Runs the daily searcher, queuing selected episodes for search

        :param force: Force search
        """
        if self.am_active:
            return

        self.am_active = True
        force_ = force
        logger.log(u"Searching for new released episodes ...")

        if not network_timezones.network_dict:
            network_timezones.update_network_dict()

        if network_timezones.network_dict:
            cur_date = (datetime.date.today() + datetime.timedelta(days=1)).toordinal()
        else:
            cur_date = (datetime.date.today() + datetime.timedelta(days=2)).toordinal()

        cur_time = datetime.datetime.now(network_timezones.sb_timezone)

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT showid, airdate, season, episode FROM tv_episodes WHERE status = ? AND (airdate <= ? and airdate > 1)",
                                         [common.UNAIRED, cur_date])

        sql_l = []
        show = None

        for sql_ep in sql_results:
            try:
                if not show or int(sql_ep["showid"]) != show.indexerid:
                    show = Show.find(sickbeard.show_list, int(sql_ep["showid"]))
                    show = Show.find(sickbeard.show_list, int(sql_ep["showid"]))

                # for when there is orphaned series in the database but not loaded into our showlist
                if not show or show.paused:
                    continue

            except MultipleShowObjectsException:
                logger.log(u"ERROR: expected to find a single show matching " + str(sql_ep['showid']))
                continue

            if show.airs and show.network:
                # This is how you assure it is always converted to local time
                air_time = network_timezones.parse_date_time(sql_ep['airdate'], show.airs, show.network).astimezone(network_timezones.sb_timezone)

                # filter out any episodes that haven't started airing yet,
                # but set them to the default status while they are airing
                # so they are snatched faster
                if air_time > cur_time:
                    continue

            ep = show.get_episode(sql_ep["season"], sql_ep["episode"])
            with ep.lock:
                if ep.season == 0:
                    logger.log(u"New episode " + ep.prettyName() + " airs today, setting status to SKIPPED because is a special season")
                    ep.status = common.SKIPPED
                else:
                    logger.log(u"New episode {0} airs today, setting to default episode status for this show: {1}".format(ep.prettyName(), common.statusStrings[ep.show.default_ep_status]))
                    ep.status = ep.show.default_ep_status

                sql_l.append(ep.get_sql())

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)
        else:
            logger.log(u"No new released episodes found ...")

        # queue episode for daily search
        dailysearch_queue_item = sickbeard.search_queue.DailySearchQueueItem()
        sickbeard.search_queue_scheduler.action.add_item(dailysearch_queue_item)

        self.am_active = False
