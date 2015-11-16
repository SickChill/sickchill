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


import time
import traceback
import threading

import sickbeard
from sickbeard import common
from sickbeard import logger
from sickbeard import generic_queue
from sickbeard import search, failed_history, history
from sickbeard import ui

search_queue_lock = threading.Lock()

BACKLOG_SEARCH = 10
DAILY_SEARCH = 20
FAILED_SEARCH = 30
MANUAL_SEARCH = 40

MANUAL_SEARCH_HISTORY = []
MANUAL_SEARCH_HISTORY_SIZE = 100

class SearchQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "SEARCHQUEUE"

    def is_in_queue(self, show, segment):
        for cur_item in self.queue:
            if isinstance(cur_item, BacklogQueueItem) and cur_item.show == show and cur_item.segment == segment:
                return True
        return False

    def is_ep_in_queue(self, segment):
        for cur_item in self.queue:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.segment == segment:
                return True
        return False

    def is_show_in_queue(self, show):
        for cur_item in self.queue:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.show.indexerid == show:
                return True
        return False

    def get_all_ep_from_queue(self, show):
        ep_obj_list = []
        for cur_item in self.queue:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and str(cur_item.show.indexerid) == show:
                ep_obj_list.append(cur_item)
        return ep_obj_list

    def pause_backlog(self):
        self.min_priority = generic_queue.QueuePriorities.HIGH

    def unpause_backlog(self):
        self.min_priority = 0

    def is_backlog_paused(self):
        # backlog priorities are NORMAL, this should be done properly somewhere
        return self.min_priority >= generic_queue.QueuePriorities.NORMAL

    def is_manualsearch_in_progress(self):
        # Only referenced in webserve.py, only current running manualsearch or failedsearch is needed!!
        if isinstance(self.currentItem, (ManualSearchQueueItem, FailedQueueItem)):
            return True
        return False

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

    def queue_length(self):
        length = {'backlog': 0, 'daily': 0, 'manual': 0, 'failed': 0}
        for cur_item in self.queue:
            if isinstance(cur_item, DailySearchQueueItem):
                length['daily'] += 1
            elif isinstance(cur_item, BacklogQueueItem):
                length['backlog'] += 1
            elif isinstance(cur_item, ManualSearchQueueItem):
                length['manual'] += 1
            elif isinstance(cur_item, FailedQueueItem):
                length['failed'] += 1
        return length


    def add_item(self, item):
        if isinstance(item, DailySearchQueueItem):
            # daily searches
            generic_queue.GenericQueue.add_item(self, item)
        elif isinstance(item, BacklogQueueItem) and not self.is_in_queue(item.show, item.segment):
            # backlog searches
            generic_queue.GenericQueue.add_item(self, item)
        elif isinstance(item, (ManualSearchQueueItem, FailedQueueItem)) and not self.is_ep_in_queue(item.segment):
            # manual and failed searches
            generic_queue.GenericQueue.add_item(self, item)
        else:
            logger.log(u"Not adding item, it's already in the queue", logger.DEBUG)

class DailySearchQueueItem(generic_queue.QueueItem):
    def __init__(self):
        self.success = None
        generic_queue.QueueItem.__init__(self, u'Daily Search', DAILY_SEARCH)

    def run(self):
        generic_queue.QueueItem.run(self)

        try:
            logger.log(u"Beginning daily search for new episodes")
            foundResults = search.searchForNeededEpisodes()

            if not len(foundResults):
                logger.log(u"No needed episodes found")
            else:
                for result in foundResults:
                    # just use the first result for now
                    logger.log(u"Downloading " + result.name + " from " + result.provider.name)
                    self.success = search.snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])

            generic_queue.QueueItem.finish(self)
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        if self.success is None:
            self.success = False

        self.finish()


class ManualSearchQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        generic_queue.QueueItem.__init__(self, u'Manual Search', MANUAL_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = 'MANUAL-' + str(show.indexerid)
        self.success = None
        self.show = show
        self.segment = segment
        self.started = None
        self.downCurQuality = downCurQuality

    def run(self):
        generic_queue.QueueItem.run(self)

        try:
            logger.log(u"Beginning manual search for: [" + self.segment.prettyName() + "]")
            self.started = True

            searchResult = search.searchProviders(self.show, [self.segment], True, self.downCurQuality)

            if searchResult:
                # just use the first result for now
                logger.log(u"Downloading " + searchResult[0].name + " from " + searchResult[0].provider.name)
                self.success = search.snatchEpisode(searchResult[0])

                # give the CPU a break
                time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])

            else:
                ui.notifications.message('No downloads were found',
                                         "Couldn't find a download for <i>%s</i>" % self.segment.prettyName())

                logger.log(u"Unable to find a download for: [" + self.segment.prettyName() + "]")

        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        ### Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)

        if self.success is None:
            self.success = False

        self.finish()


class BacklogQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        generic_queue.QueueItem.__init__(self, u'Backlog', BACKLOG_SEARCH)
        self.priority = generic_queue.QueuePriorities.LOW
        self.name = 'BACKLOG-' + str(show.indexerid)
        self.success = None
        self.show = show
        self.segment = segment

    def run(self):
        generic_queue.QueueItem.run(self)

        if not self.show.paused:
            try:
                logger.log(u"Beginning backlog search for: [" + self.show.name + "]")
                searchResult = search.searchProviders(self.show, self.segment, False)

                if searchResult:
                    for result in searchResult:
                        # just use the first result for now
                        logger.log(u"Downloading " + result.name + " from " + result.provider.name)
                        search.snatchEpisode(result)

                        # give the CPU a break
                        time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])
                else:
                    logger.log(u"No needed episodes found during backlog search for: [" + self.show.name + "]")
            except Exception:
                logger.log(traceback.format_exc(), logger.DEBUG)

        self.finish()


class FailedQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        generic_queue.QueueItem.__init__(self, u'Retry', FAILED_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = 'RETRY-' + str(show.indexerid)
        self.show = show
        self.segment = segment
        self.success = None
        self.started = None
        self.downCurQuality = downCurQuality

    def run(self):
        generic_queue.QueueItem.run(self)
        self.started = True

        try:
            for epObj in self.segment:

                logger.log(u"Marking episode as bad: [" + epObj.prettyName() + "]")

                failed_history.markFailed(epObj)

                (release, provider) = failed_history.findRelease(epObj)
                if release:
                    failed_history.logFailed(release)
                    history.logFailed(epObj, release, provider)

                failed_history.revertEpisode(epObj)
                logger.log(u"Beginning failed download search for: [" + epObj.prettyName() + "]")

            # If it is wanted, self.downCurQuality doesnt matter
            # if it isnt wanted, we need to make sure to not overwrite the existing ep that we reverted to!
            searchResult = search.searchProviders(self.show, self.segment, True, False)

            if searchResult:
                for result in searchResult:
                    # just use the first result for now
                    logger.log(u"Downloading " + result.name + " from " + result.provider.name)
                    search.snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])
            else:
                pass
                # logger.log(u"No valid episode found to retry for: [" + self.segment.prettyName() + "]")
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        ### Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)

        if self.success is None:
            self.success = False

        self.finish()

def fifo(myList, item, maxSize = 100):
    if len(myList) >= maxSize:
        myList.pop(0)
    myList.append(item)
