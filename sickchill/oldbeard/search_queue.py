import time
import traceback

from sickchill import logger, settings

from . import common, failed_history, generic_queue, history, search, ui

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
        for cur_item in self.queue + [self.currentItem]:
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

        add_item = False
        if isinstance(item, DailySearchQueueItem):
            # daily searches
            add_item = True
        elif isinstance(item, BacklogQueueItem):
            # backlog searches
            add_item = not self.is_in_queue(item.show, item.segment)
        elif isinstance(item, (ManualSearchQueueItem, FailedQueueItem)):
            # manual and failed searches
            add_item = not self.is_ep_in_queue(item.segment)
        else:
            logger.debug("Not adding item, it's already in the queue")

        if add_item:
            super(SearchQueue, self).add_item(item)


class DailySearchQueueItem(generic_queue.QueueItem):
    def __init__(self):
        super(DailySearchQueueItem, self).__init__('Daily Search', DAILY_SEARCH)
        self.success = None

    def run(self):
        super(DailySearchQueueItem, self).run()

        try:
            logger.info("Beginning daily search for new episodes")
            found_results = search.searchForNeededEpisodes()

            if not found_results:
                logger.info("No needed episodes found")
            else:
                for result in found_results:
                    # just use the first result for now
                    logger.info("Downloading " + result.name + " from " + result.provider.name)
                    self.success = search.snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(common.cpu_presets[settings.CPU_PRESET])
        except Exception:
            logger.debug(traceback.format_exc())

        if self.success is None:
            self.success = False

        super(DailySearchQueueItem, self).finish()
        self.finish()


class ManualSearchQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        super(ManualSearchQueueItem, self).__init__('Manual Search', MANUAL_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = 'MANUAL-' + str(show.indexerid)
        self.success = None
        self.show = show
        self.segment = segment
        self.started = None
        self.downCurQuality = downCurQuality

    def run(self):
        super(ManualSearchQueueItem, self).run()

        try:
            logger.info("Beginning manual search for: [" + self.segment.pretty_name() + "]")
            self.started = True

            searchResult = search.searchProviders(self.show, [self.segment], True, self.downCurQuality)

            if searchResult:
                # just use the first result for now
                logger.info("Downloading " + searchResult[0].name + " from " + searchResult[0].provider.name)
                self.success = search.snatchEpisode(searchResult[0])

                # give the CPU a break
                time.sleep(common.cpu_presets[settings.CPU_PRESET])

            else:
                ui.notifications.message('No downloads were found',
                                         "Couldn't find a download for <i>{0}</i>".format(self.segment.pretty_name()))

                logger.info("Unable to find a download for: [" + self.segment.pretty_name() + "]")

        except Exception:
            logger.debug(traceback.format_exc())

        # ## Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)

        if self.success is None:
            self.success = False

        super(ManualSearchQueueItem, self).finish()
        self.finish()


class BacklogQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        super(BacklogQueueItem, self).__init__('Backlog', BACKLOG_SEARCH)
        self.priority = generic_queue.QueuePriorities.LOW
        self.name = 'BACKLOG-' + str(show.indexerid)
        self.success = None
        self.show = show
        self.segment = segment

    def run(self):
        super(BacklogQueueItem, self).run()

        if not self.show.paused:
            try:
                logger.info("Beginning backlog search for: [" + self.show.name + "]")
                searchResult = search.searchProviders(self.show, self.segment, False)

                if searchResult:
                    for result in searchResult:
                        # just use the first result for now
                        logger.info("Downloading " + result.name + " from " + result.provider.name)
                        search.snatchEpisode(result)

                        # give the CPU a break
                        time.sleep(common.cpu_presets[settings.CPU_PRESET])
                else:
                    logger.info("No needed episodes found during backlog search for: [" + self.show.name + "]")
            except Exception:
                logger.debug(traceback.format_exc())

        super(BacklogQueueItem, self).finish()
        self.finish()


class FailedQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        super(FailedQueueItem, self).__init__('Retry', FAILED_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = 'RETRY-' + str(show.indexerid)
        self.show = show
        self.segment = segment
        self.success = None
        self.started = None
        self.downCurQuality = downCurQuality

    def run(self):
        super(FailedQueueItem, self).run()
        self.started = True

        try:
            for epObj in self.segment:

                logger.info("Marking episode as bad: [" + epObj.pretty_name() + "]")

                failed_history.markFailed(epObj)

                (release, provider) = failed_history.findRelease(epObj)
                if release:
                    failed_history.logFailed(release)
                    history.logFailed(epObj, release, provider)

                failed_history.revertEpisode(epObj)
                logger.info("Beginning failed download search for: [" + epObj.pretty_name() + "]")

            # If it is wanted, self.downCurQuality doesnt matter
            # if it isnt wanted, we need to make sure to not overwrite the existing ep that we reverted to!
            searchResult = search.searchProviders(self.show, self.segment, True, False)

            if searchResult:
                for result in searchResult:
                    # just use the first result for now
                    logger.info("Downloading " + result.name + " from " + result.provider.name)
                    search.snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(common.cpu_presets[settings.CPU_PRESET])
            else:
                pass
                # logger.info("No valid episode found to retry for: [" + self.segment.pretty_name() + "]")
        except Exception:
            logger.debug(traceback.format_exc())

        # ## Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)

        if self.success is None:
            self.success = False

        super(FailedQueueItem, self).finish()
        self.finish()


def fifo(my_list, item, max_size=100):
    if len(my_list) >= max_size:
        my_list.pop(0)
    my_list.append(item)
