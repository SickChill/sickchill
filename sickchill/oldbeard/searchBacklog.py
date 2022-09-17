import datetime
import threading

from sickchill import logger, settings

from . import common, db, scheduler, search_queue, ui


class BacklogSearchScheduler(scheduler.Scheduler):
    def forceSearch(self):
        self.action._set_lastBacklog(1)
        self.lastRun = datetime.datetime.fromordinal(1)

    def nextRun(self):
        if self.action._lastBacklog <= 1:
            return datetime.date.today()
        else:
            return datetime.date.fromordinal(self.action._lastBacklog + self.action.cycleTime)


class BacklogSearcher(object):
    def __init__(self):

        self._lastBacklog = self._get_lastBacklog()
        self.cycleTime = settings.BACKLOG_FREQUENCY / 60 / 24
        self.lock = threading.Lock()
        self.amActive = False
        self.amPaused = False
        self.amWaiting = False
        self.currentSearchInfo = {"title": "Initializing"}

        self._resetPI()

    def _resetPI(self):
        self.percentDone = 0
        self.currentSearchInfo = {"title": "Initializing"}

    def getProgressIndicator(self):
        if self.amActive:
            return ui.ProgressIndicator(self.percentDone, self.currentSearchInfo)
        else:
            return None

    def am_running(self):
        logger.debug(f"amWaiting: {self.amWaiting}, amActive: {self.amActive}")
        return (not self.amWaiting) and self.amActive

    def searchBacklog(self, which_shows=None):

        if self.amActive:
            logger.debug("Backlog is still running, not starting it again")
            return

        self.amActive = True
        self.amPaused = False

        if which_shows:
            show_list = which_shows
        else:
            show_list = settings.showList

        self._get_lastBacklog()

        curDate = datetime.date.today().toordinal()
        fromDate = datetime.date.min

        if not (which_shows or curDate - self._lastBacklog >= self.cycleTime):
            logger.info(f"Running limited backlog on missed episodes {settings.BACKLOG_DAYS} day(s) and older only")
            fromDate = datetime.date.today() - datetime.timedelta(days=settings.BACKLOG_DAYS)

        # go through non air-by-date shows and see if they need any episodes
        for curShow in show_list:

            if curShow.paused:
                continue

            segments = self._get_segments(curShow, fromDate)

            for season, segment in segments.items():
                self.currentSearchInfo = {"title": f"{curShow.name} Season {season}"}

                backlog_queue_item = search_queue.BacklogQueueItem(curShow, segment)
                settings.searchQueueScheduler.action.add_item(backlog_queue_item)  # @UndefinedVariable

            if not segments:
                logger.debug(f"Nothing needs to be downloaded for {curShow.name}, skipping")

        # don't consider this an actual backlog search if we only did recent eps
        # or if we only did certain shows
        if fromDate == datetime.date.min and not which_shows:
            self._set_lastBacklog(curDate)

        self.amActive = False
        self._resetPI()

    def _get_lastBacklog(self):

        logger.debug("Retrieving the last check time from the DB")

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT last_backlog FROM info")

        if not sql_results:
            lastBacklog = 1
        elif sql_results[0]["last_backlog"] is None or sql_results[0]["last_backlog"] == "":
            lastBacklog = 1
        else:
            lastBacklog = int(sql_results[0]["last_backlog"])
            if lastBacklog > datetime.date.today().toordinal():
                lastBacklog = 1

        self._lastBacklog = lastBacklog
        return self._lastBacklog

    @staticmethod
    def _get_segments(show, fromDate):
        wanted = {}
        if show.paused:
            logger.debug(f"Skipping backlog for {show.name} because the show is paused")
            return wanted

        allowed_qualities, preferred_qualities = common.Quality.splitQuality(show.quality)

        logger.debug(f"Seeing if we need anything from {show.name}")

        con = db.DBConnection()
        sql_results = con.select("SELECT status, season, episode FROM tv_episodes WHERE airdate > ? AND showid = ?", [fromDate.toordinal(), show.indexerid])

        # check through the list of statuses to see if we want any
        for sql_result in sql_results:
            cur_status, cur_quality = common.Quality.splitCompositeStatus(int(sql_result["status"] or -1))

            if cur_status not in {common.WANTED, common.DOWNLOADED, common.SNATCHED, common.SNATCHED_PROPER}:
                continue

            if cur_status == common.DOWNLOADED and settings.BACKLOG_MISSING_ONLY:
                continue

            if cur_status != common.WANTED:
                if preferred_qualities:
                    if cur_quality in preferred_qualities:
                        continue
                elif cur_quality in allowed_qualities:
                    continue

            ep_obj = show.getEpisode(sql_result["season"], sql_result["episode"])

            if ep_obj.season not in wanted:
                wanted[ep_obj.season] = [ep_obj]
            else:
                wanted[ep_obj.season].append(ep_obj)

        return wanted

    @staticmethod
    def _set_lastBacklog(when):

        logger.debug(f"Setting the last backlog in the DB to {when}")

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT last_backlog FROM info")

        if not sql_results:
            main_db_con.action("INSERT INTO info (last_backlog, last_indexer) VALUES (?,?)", [str(when), 0])
        else:
            main_db_con.action("UPDATE info SET last_backlog=" + str(when))

    def run(self, force=False):
        try:
            self.searchBacklog()
        except Exception:
            self.amActive = False
            raise
