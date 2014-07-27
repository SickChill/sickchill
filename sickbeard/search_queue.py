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

import time
import traceback
import threading

import sickbeard
from sickbeard import db, logger, common, exceptions, helpers
from sickbeard import generic_queue, scheduler
from sickbeard import search, failed_history, history
from sickbeard import ui
from sickbeard.exceptions import ex
from sickbeard.search import pickBestResult

search_queue_lock = threading.Lock()

BACKLOG_SEARCH = 10
DAILY_SEARCH = 20
FAILED_SEARCH = 30
MANUAL_SEARCH = 40


class SearchQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "SEARCHQUEUE"

    def is_in_queue(self, show, segment):
        for cur_item in self.queue:
            if isinstance(cur_item, BacklogQueueItem) and cur_item.show == show and cur_item.segment == segment:
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
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, BacklogQueueItem):
                return True
        return False

    def is_dailysearch_in_progress(self):
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, DailySearchQueueItem):
                return True
        return False

    def add_item(self, item):

        if isinstance(item, (DailySearchQueueItem, BacklogQueueItem, ManualSearchQueueItem, FailedQueueItem)) \
                and not self.is_in_queue(item.show, item.segment):
            sickbeard.name_cache.buildNameCache(item.show)
            generic_queue.GenericQueue.add_item(self, item)
        else:
            logger.log(u"Not adding item, it's already in the queue", logger.DEBUG)


class DailySearchQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        generic_queue.QueueItem.__init__(self, 'Daily Search', DAILY_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = 'DAILYSEARCH-' + str(show.indexerid)
        self.show = show
        self.segment = segment

    def run(self):

        generic_queue.QueueItem.run(self)

        try:

            logger.log("Beginning daily search for [" + self.show.name + "]")
            foundResults = search.searchForNeededEpisodes(self.show, self.segment)

            if not len(foundResults):
                logger.log(u"No needed episodes found during daily search for [" + self.show.name + "]")
            else:
                for result in foundResults:
                    # just use the first result for now
                    logger.log(u"Downloading " + result.name + " from " + result.provider.name)
                    search.snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])

            generic_queue.QueueItem.finish(self)
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        self.finish()

class ManualSearchQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        generic_queue.QueueItem.__init__(self, 'Manual Search', MANUAL_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = 'MANUAL-' + str(show.indexerid)
        self.success = None
        self.show = show
        self.segment = segment

    def run(self):
        generic_queue.QueueItem.run(self)

        try:
            logger.log("Beginning manual search for [" + self.segment.prettyName() + "]")
            searchResult = search.searchProviders(self.show, self.segment.season, [self.segment], True)

            if searchResult:
                # just use the first result for now
                logger.log(u"Downloading " + searchResult[0].name + " from " + searchResult[0].provider.name)
                self.success = search.snatchEpisode(searchResult[0])

                # give the CPU a break
                time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])

            else:
                ui.notifications.message('No downloads were found',
                                         "Couldn't find a download for <i>%s</i>" % self.segment.prettyName())

                logger.log(u"Unable to find a download for " + self.segment.prettyName())

        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        if self.success is None:
            self.success = False

        self.finish()


class BacklogQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        generic_queue.QueueItem.__init__(self, 'Backlog', BACKLOG_SEARCH)
        self.priority = generic_queue.QueuePriorities.LOW
        self.name = 'BACKLOG-' + str(show.indexerid)
        self.success = None
        self.show = show
        self.segment = segment

    def run(self):
        generic_queue.QueueItem.run(self)

        try:
            for season in self.segment:
                sickbeard.searchBacklog.BacklogSearcher.currentSearchInfo = {
                'title': self.show.name + " Season " + str(season)}

                wantedEps = self.segment[season]

                logger.log("Beginning backlog search for [" + self.show.name + "]")
                searchResult = search.searchProviders(self.show, season, wantedEps, False)

                if searchResult:
                    for result in searchResult:
                        # just use the first result for now
                        logger.log(u"Downloading " + result.name + " from " + result.provider.name)
                        search.snatchEpisode(result)

                        # give the CPU a break
                        time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])
                else:
                    logger.log(u"No needed episodes found during backlog search for [" + self.show.name + "]")
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        self.finish()


class FailedQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        generic_queue.QueueItem.__init__(self, 'Retry', FAILED_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = 'RETRY-' + str(show.indexerid)
        self.show = show
        self.segment = segment
        self.success = None

    def run(self):
        generic_queue.QueueItem.run(self)

        try:
            for season, episodes in self.segment.items():
                for epObj in episodes:
                    logger.log(u"Marking episode as bad: [" + epObj.prettyName() + "]")
                    failed_history.markFailed(epObj)

                    (release, provider) = failed_history.findRelease(epObj)
                    if release:
                        failed_history.logFailed(release)
                        history.logFailed(epObj, release, provider)

                    failed_history.revertEpisode(epObj)
                    logger.log("Beginning failed download search for [" + epObj.prettyName() + "]")

                    searchResult = search.searchProviders(self.show, season, [epObj], True)

                    if searchResult:
                        for result in searchResult:
                            # just use the first result for now
                            logger.log(u"Downloading " + result.name + " from " + result.provider.name)
                            search.snatchEpisode(result)

                            # give the CPU a break
                            time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])
                    else:
                        logger.log(u"No valid episode found to retry for [" + epObj.prettyName() + "]")
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        if self.success is None:
            self.success = False

        self.finish()