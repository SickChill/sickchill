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

import datetime
import traceback
import threading

import sickbeard
from sickbeard import db, logger, common, exceptions, helpers
from sickbeard import generic_queue, scheduler
from sickbeard import search, failed_history, history
from sickbeard import ui

search_queue_lock = threading.Lock()

BACKLOG_SEARCH = 10
FAILED_SEARCH = 30
MANUAL_SEARCH = 30

class SearchQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "SEARCHQUEUE"

    def is_in_queue(self, show, segment):
        queue =  [x for x in self.queue.queue] + [self.currentItem]
        for cur_item in queue:
            with search_queue_lock:
                if isinstance(cur_item, BacklogQueueItem) and cur_item.show == show and cur_item.segment == segment:
                    return True
        return False

    def is_ep_in_queue(self, ep_obj):
        queue = [x for x in self.queue.queue] + [self.currentItem]
        for cur_item in queue:
            with search_queue_lock:
                if isinstance(cur_item, ManualSearchQueueItem) and cur_item.ep_obj == ep_obj:
                    return True
        return False

    def pause_backlog(self):
        self.min_priority = generic_queue.QueuePriorities.HIGH

    def unpause_backlog(self):
        self.min_priority = 0

    def is_backlog_paused(self):
        # backlog priorities are NORMAL, this should be done properly somewhere
        return self.min_priority >= generic_queue.QueuePriorities.NORMAL

    def is_backlog_in_progress(self):
        queue = [x for x in self.queue.queue] + [self.currentItem]
        for cur_item in queue:
            if isinstance(cur_item, BacklogQueueItem):
                return True
        return False

    def add_item(self, item):

        if isinstance(item, BacklogQueueItem) and not self.is_in_queue(item.show, item.segment):
            generic_queue.GenericQueue.add_item(self, item)
        elif isinstance(item, ManualSearchQueueItem) and not self.is_ep_in_queue(item.ep_obj):
            generic_queue.GenericQueue.add_item(self, item)
        elif isinstance(item, FailedQueueItem) and not self.is_in_queue(item.show, item.episodes):
            generic_queue.GenericQueue.add_item(self, item)
        else:
            logger.log(u"Not adding item, it's already in the queue", logger.DEBUG)

    def snatch_item(self, item):
        for result in item.results:
            # just use the first result for now
            logger.log(u"Downloading " + result.name + " from " + result.provider.name)
            status =  search.snatchEpisode(result)
            item.success = status
            generic_queue.QueueItem.finish(item)

class ManualSearchQueueItem(generic_queue.QueueItem):
    def __init__(self, ep_obj):
        generic_queue.QueueItem.__init__(self, 'Manual Search', MANUAL_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.thread_name = 'MANUAL-' + str(ep_obj.show.indexerid) + '-'
        self.success = None
        self.show = ep_obj.show
        self.ep_obj = ep_obj
        self.results = []

    def execute(self):
        generic_queue.QueueItem.execute(self)

        try:
            logger.log("Beginning manual search for [" + self.ep_obj.prettyName() + "]")
            searchResult = search.searchProviders(self, self.show, self.ep_obj.season, [self.ep_obj],False,True)

            if searchResult:
                SearchQueue().snatch_item(searchResult)
            else:
                ui.notifications.message('No downloads were found',
                                         "Couldn't find a download for <i>%s</i>" % self.ep_obj.prettyName())

                logger.log(u"Unable to find a download for " + self.ep_obj.prettyName())

        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        self.finish()

class BacklogQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        generic_queue.QueueItem.__init__(self, 'Backlog', BACKLOG_SEARCH)
        self.priority = generic_queue.QueuePriorities.LOW
        self.thread_name = 'BACKLOG-' + str(show.indexerid) + '-'
        self.success = None
        self.show = show
        self.segment = segment
        self.wantedEpisodes = []
        self.results = []

        logger.log(u"Seeing if we need any episodes from " + self.show.name + " season " + str(self.segment))

        myDB = db.DBConnection()

        # see if there is anything in this season worth searching for
        if not self.show.air_by_date:
            statusResults = myDB.select("SELECT status, episode FROM tv_episodes WHERE showid = ? AND season = ?",
                                        [self.show.indexerid, self.segment])
        else:
            season_year, season_month = map(int, self.segment.split('-'))
            min_date = datetime.date(season_year, season_month, 1)

            # it's easier to just hard code this than to worry about rolling the year over or making a month length map
            if season_month == 12:
                max_date = datetime.date(season_year, 12, 31)
            else:
                max_date = datetime.date(season_year, season_month + 1, 1) - datetime.timedelta(days=1)

            statusResults = myDB.select(
                "SELECT status, episode FROM tv_episodes WHERE showid = ? AND airdate >= ? AND airdate <= ?",
                [self.show.indexerid, min_date.toordinal(), max_date.toordinal()])

        anyQualities, bestQualities = common.Quality.splitQuality(self.show.quality)  #@UnusedVariable
        self.wantedEpisodes = self._need_any_episodes(statusResults, bestQualities)

    def execute(self):
        generic_queue.QueueItem.execute(self)

        # check if we want to search for season packs instead of just season/episode
        seasonSearch = False
        seasonEps = self.show.getAllEpisodes(self.segment)
        if len(seasonEps) == len(self.wantedEpisodes):
            seasonSearch = True

        try:
            logger.log("Beginning backlog search for episodes from [" + self.show.name + "]  - Season[" + str(self.segment) + "]")
            searchResult = search.searchProviders(self, self.show, self.segment, self.wantedEpisodes, seasonSearch, False)

            if searchResult:
                SearchQueue().snatch_item(searchResult)
            else:
                logger.log(u"No needed episodes found during backlog search")

        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        self.finish()

    def _need_any_episodes(self, statusResults, bestQualities):
        wantedEpisodes = []

        # check through the list of statuses to see if we want any
        for curStatusResult in statusResults:
            curCompositeStatus = int(curStatusResult["status"])
            curStatus, curQuality = common.Quality.splitCompositeStatus(curCompositeStatus)
            episode = int(curStatusResult["episode"])

            if bestQualities:
                highestBestQuality = max(bestQualities)
            else:
                highestBestQuality = 0

            # if we need a better one then say yes
            if (curStatus in (common.DOWNLOADED, common.SNATCHED, common.SNATCHED_PROPER,
                              common.SNATCHED_BEST) and curQuality < highestBestQuality) or curStatus == common.WANTED:
                epObj = self.show.getEpisode(self.segment, episode)
                wantedEpisodes.append(epObj)

        return wantedEpisodes

class FailedQueueItem(generic_queue.QueueItem):
    def __init__(self, show, episodes):
        generic_queue.QueueItem.__init__(self, 'Retry', FAILED_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.thread_name = 'RETRY-' + str(show.indexerid) + '-'
        self.show = show
        self.episodes = episodes
        self.success = None
        self.results = []

    def execute(self):
        generic_queue.QueueItem.execute(self)

        failed_episodes = []
        for i, epObj in enumerate(self.episodes):
            (release, provider) = failed_history.findRelease(epObj)
            if release:
                logger.log(u"Marking release as bad: " + release)
                failed_history.markFailed(epObj)
                failed_history.logFailed(release)
                history.logFailed(epObj, release, provider)
                failed_history.revertEpisode(epObj)
                failed_episodes.append(epObj)

        if len(failed_episodes):
            try:
                logger.log(
                    "Beginning failed download search for episodes from Season [" + str(self.episodes[0].season) + "]")

                searchResult = search.searchProviders(self, self.show, failed_episodes[0].season, failed_episodes, False, True)

                if searchResult:
                    SearchQueue().snatch_item(searchResult)
                else:
                    logger.log(u"No episodes found to retry for failed downloads return from providers!")
            except Exception, e:
                logger.log(traceback.format_exc(), logger.DEBUG)

        self.finish()