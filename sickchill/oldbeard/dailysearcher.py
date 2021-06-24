import datetime
import threading

import sickchill.oldbeard.search_queue
from sickchill import logger, settings
from sickchill.helper.exceptions import MultipleShowObjectsException
from sickchill.show.Show import Show

from . import common, db, network_timezones


class DailySearcher(object):  # pylint:disable=too-few-public-methods
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):  # pylint:disable=too-many-branches
        """
        Runs the daily searcher, queuing selected episodes for search

        :param force: Force search
        """
        if self.amActive:
            return

        self.amActive = True
        logger.info(_("Searching for new released episodes ..."))

        if not network_timezones.network_dict:
            network_timezones.update_network_dict()

        if network_timezones.network_dict:
            curDate = (datetime.date.today() + datetime.timedelta(days=1)).toordinal()
        else:
            curDate = (datetime.date.today() + datetime.timedelta(days=2)).toordinal()

        curTime = datetime.datetime.now(network_timezones.sb_timezone)

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select(
            "SELECT showid, airdate, season, episode FROM tv_episodes WHERE status = ? AND (airdate <= ? and airdate > 1)", [common.UNAIRED, curDate]
        )

        sql_l = []
        show = None

        for sqlEp in sql_results:
            try:
                if not show or int(sqlEp["showid"]) != show.indexerid:
                    show = Show.find(settings.showList, int(sqlEp["showid"]))

                # for when there is orphaned series in the database but not loaded into our showlist
                if not show or show.paused:
                    continue

            except MultipleShowObjectsException:
                logger.info("ERROR: expected to find a single show matching " + str(sqlEp["showid"]))
                continue

            if show.airs and show.network:
                # This is how you assure it is always converted to local time
                air_time = network_timezones.parse_date_time(sqlEp["airdate"], show.airs, show.network).astimezone(network_timezones.sb_timezone)

                # filter out any episodes that haven't started airing yet,
                # but set them to the default status while they are airing
                # so they are snatched faster
                if air_time > curTime:
                    continue

            ep = show.getEpisode(sqlEp["season"], sqlEp["episode"])
            with ep.lock:
                if ep.season == 0:
                    logger.info("New episode " + ep.pretty_name + " airs today, setting status to SKIPPED because is a special season")
                    ep.status = common.SKIPPED
                else:
                    logger.info(
                        "New episode {0} airs today, setting to default episode status for this show: {1}".format(
                            ep.pretty_name, common.statusStrings[ep.show.default_ep_status]
                        )
                    )
                    ep.status = ep.show.default_ep_status

                sql_l.append(ep.get_sql())

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)
        else:
            logger.info("No new released episodes found ...")

        # queue episode for daily search
        dailysearch_queue_item = sickchill.oldbeard.search_queue.DailySearchQueueItem()
        settings.searchQueueScheduler.action.add_item(dailysearch_queue_item)

        self.amActive = False
