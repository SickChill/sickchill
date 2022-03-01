import time
import traceback
from typing import TYPE_CHECKING

from sickchill import logger, settings
from sickchill.show.History import History

if TYPE_CHECKING:
    from sickchill.oldbeard.databases.movie import Movie

from . import common, generic_queue, search, ui

BACKLOG_SEARCH = 10
DAILY_SEARCH = 20
FAILED_SEARCH = 30
MANUAL_SEARCH = 40

MANUAL_SEARCH_HISTORY = []
MANUAL_SEARCH_HISTORY_SIZE = 100


class SearchQueue(generic_queue.GenericQueue):
    def __init__(self):
        super().__init__()
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

    def is_movie_in_queue(self, movie: "Movie"):
        for cur_item in self.queue:
            if isinstance(cur_item, MovieQueueItem) and cur_item.movie.pk == movie.pk:
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
            if isinstance(cur_item, (BacklogQueueItem, MovieQueueItem)):
                return True
        return False

    def is_dailysearch_in_progress(self):
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, DailySearchQueueItem):
                return True
        return False

    def queue_length(self):
        length = {"backlog": 0, "daily": 0, "manual": 0, "failed": 0}
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, DailySearchQueueItem):
                length["daily"] += 1
            elif isinstance(cur_item, (BacklogQueueItem, MovieQueueItem)):
                length["backlog"] += 1
            elif isinstance(cur_item, ManualSearchQueueItem):
                length["manual"] += 1
            elif isinstance(cur_item, FailedQueueItem):
                length["failed"] += 1
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
        elif isinstance(item, MovieQueueItem):
            add_item = not self.is_movie_in_queue(item.movie)
        else:
            logger.debug("Not adding item, it's already in the queue")

        if add_item:
            super().add_item(item)


class DailySearchQueueItem(generic_queue.QueueItem):
    def __init__(self):
        super().__init__("Daily Search", DAILY_SEARCH)
        self.success = None

    def run(self):
        super().run()

        try:
            logger.info("Beginning daily search for new episodes")
            found_results = search.searchForNeededEpisodes()

            if not found_results:
                logger.info("No needed episodes found")
            else:
                for result in found_results:
                    # just use the first result for now
                    logger.info(f"Downloading {result.name} from {result.provider.name}")
                    self.success = search.snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(common.cpu_presets[settings.CPU_PRESET])
        except Exception:
            logger.debug(traceback.format_exc())

        if self.success is None:
            self.success = False

        super().finish()
        self.finish()


class ManualSearchQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        super().__init__("Manual Search", MANUAL_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = f"MANUAL-{show.indexerid}"
        self.success = None
        self.show = show
        self.segment = segment
        self.started = None
        self.downCurQuality = downCurQuality

    def run(self):
        super().run()

        try:
            logger.info(f"Beginning manual search for: [{self.segment.pretty_name}]")
            self.started = True

            search_result = search.searchProviders(self.show, [self.segment], True, self.downCurQuality)

            if search_result:
                # just use the first result for now
                logger.info(f"Downloading {search_result[0].name} from {search_result[0].provider.name}")
                self.success = search.snatchEpisode(search_result[0])

                # give the CPU a break
                time.sleep(common.cpu_presets[settings.CPU_PRESET])

            else:
                ui.notifications.message("No downloads were found", "Couldn't find a download for <i>{0}</i>".format(self.segment.pretty_name))

                logger.info(f"Unable to find a download for: [{self.segment.pretty_name}]")

        except Exception:
            logger.debug(traceback.format_exc())

        # ## Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)

        if self.success is None:
            self.success = False

        super().finish()
        self.finish()


class BacklogQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        super().__init__("Backlog", BACKLOG_SEARCH)
        self.priority = generic_queue.QueuePriorities.LOW
        self.name = f"BACKLOG-{show.indexerid}"
        self.success = None
        self.show = show
        self.segment = segment

    def run(self):
        super().run()

        if not self.show.paused:
            try:
                logger.info(f"Beginning backlog search for: [{self.show.name}]")
                searchResult = search.searchProviders(self.show, self.segment, False)

                if searchResult:
                    for result in searchResult:
                        # just use the first result for now
                        logger.info(f"Downloading {result.name} from {result.provider.name}")
                        search.snatchEpisode(result)

                        # give the CPU a break
                        time.sleep(common.cpu_presets[settings.CPU_PRESET])
                else:
                    logger.info(f"No needed episodes found during backlog search for: [{self.show.name}]")
            except Exception:
                logger.debug(traceback.format_exc())

        super().finish()
        self.finish()


class MovieQueueItem(generic_queue.QueueItem):
    def __init__(self, movie: "Movie"):
        super().__init__("Movie", BACKLOG_SEARCH)
        self.priority = generic_queue.QueuePriorities.LOW
        self.name = f"BACKLOG-{movie.tmdb_id}"
        self.success = None
        self.movie = movie

    def run(self):
        super().run()

        if not self.movie.paused:
            try:
                logger.info(f"Beginning backlog search for: [{self.movie.name}]")
                settings.movie_list.search_providers(self.movie)
                for result in self.movie.results:
                    # just use the first result for now
                    logger.info(f"Downloading {result.name} from {result.provider}")
                    settings.movie_list.snatch_movie(result)

                    # give the CPU a break
                    time.sleep(common.cpu_presets[settings.CPU_PRESET])
                else:
                    logger.info(_("No needed movie results found during backlog search for: [{name}]".format(name=self.movie.name)))
            except Exception:
                logger.debug(traceback.format_exc())

        super().finish()
        self.finish()


class FailedQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        super().__init__("Retry", FAILED_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.name = f"RETRY-{show.indexerid}"
        self.show = show
        self.segment = segment
        self.success = None
        self.started = None
        self.downCurQuality = downCurQuality

    def run(self):
        super().run()
        self.started = True

        try:
            for epObj in self.segment:
                History().markFailed(epObj)
                logger.info(f"Beginning failed download search for: [{epObj.pretty_name}]")

            # If it is wanted, self.downCurQuality doesnt matter
            # if it isnt wanted, we need to make sure to not overwrite the existing ep that we reverted to!
            search_result = search.searchProviders(self.show, self.segment, True)

            if search_result:
                for result in search_result:
                    # just use the first result for now
                    logger.info(f"Downloading {result.name} from {result.provider.name}")
                    search.snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(common.cpu_presets[settings.CPU_PRESET])
            else:
                pass
                # logger.info(f"No valid episode found to retry for: [{self.segment.pretty_name}]")
        except Exception:
            logger.debug(traceback.format_exc())

        # ## Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)

        if self.success is None:
            self.success = False

        super().finish()
        self.finish()


def fifo(my_list, item, max_size=100):
    if len(my_list) >= max_size:
        my_list.pop(0)
    my_list.append(item)
