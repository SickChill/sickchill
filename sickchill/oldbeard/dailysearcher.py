import datetime
import threading

import sickchill.oldbeard.search_queue
from sickchill import logger, settings
from sickchill.helper.exceptions import MultipleShowObjectsException
from sickchill.show.Show import Show

from . import common, db, network_timezones


class DailySearcher(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the daily searcher, queuing selected episodes for search

        param force: Force search
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
                logger.info(_("ERROR: expected to find a single show matching {show_id}").format(show_id=sqlEp["showid"]))
                continue

            if show.airs and show.network:
                # This is how you assure it is always converted to local time
                air_time = network_timezones.parse_date_time(sqlEp["airdate"], show.airs, show.network).astimezone(network_timezones.sb_timezone)

                # filter out any episodes that haven't started airing yet,
                # but set them to the default status while they are airing so that they are snatched faster
                if air_time > curTime:
                    continue

            ep = show.getEpisode(sqlEp["season"], sqlEp["episode"])
            with ep.lock:
                prefix = _("New episode {episode_string} airs today,").format(episode_string=ep.pretty_name)
                if ep.season == 0:
                    logger.info(_("{prefix} setting status to SKIPPED because is a special season").format(prefix=prefix))
                    ep.status = common.SKIPPED
                else:
                    if ep.status != common.UNAIRED:
                        logger.debug(
                            _(
                                "{prefix} but it has already been snatched or downloaded, but has not been saved to the database yet. Skipping so we don't download it again!"
                            ).format(prefix=prefix)
                        )
                    else:
                        logger.info(
                            _("{prefix} setting to default episode status for this show: {status_string}").format(
                                prefix=prefix, status_string=common.statusStrings[ep.show.default_ep_status]
                            )
                        )
                        ep.status = ep.show.default_ep_status

                sql_l.append(ep.get_sql())

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)
        else:
            logger.info(_("No new released episodes found ..."))

        # queue episode for daily search
        dailysearch_queue_item = sickchill.oldbeard.search_queue.DailySearchQueueItem()
        settings.searchQueueScheduler.action.add_item(dailysearch_queue_item)

        self.amActive = False
