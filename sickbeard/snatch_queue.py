import Queue
import threading

import sickbeard
from sickbeard import logger, search, generic_queue, ui
from sickbeard.common import Quality

snatch_queue_lock = threading.Lock()

class SnatchQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "SNATCHQUEUE"

        # snatch queues
        self.ManualQueue = Queue.Queue()
        self.BacklogQueue = Queue.Queue()
        self.FailedQueue = Queue.Queue()

    def is_in_queue(self, queue, show, episodes, quality):
        for i, cur_item in enumerate(queue.queue):
            if cur_item.results.show == show and cur_item.results.episodes.sort() == episodes.sort():
                if cur_item.results.quality < quality:
                    queue.queue.pop(i)
                    return False
                return True
        return False

    def add_item(self, item):
        resultsKeep = []
        for result in item.results:
            show = result.extraInfo[0]
            episodes = result.episodes
            quality = result.quality

            # check if we already have a item ready to snatch with same or better quality score
            if not self.is_in_queue(self.queue, show, episodes, quality):
                generic_queue.GenericQueue.add_item(self, item)
                resultsKeep.append(result)
                logger.log(
                    u"Adding item [" + result.name + "] to snatch queue",
                    logger.DEBUG)
            else:
                logger.log(
                    u"Not adding item [" + result.name + "] it's already in the queue with same or higher quality",
                    logger.DEBUG)

        # update item with new results we want to snatch and disgard the rest
        item.results = resultsKeep

    def snatch_item(self, item):
        for result in item.results:
            # just use the first result for now
            logger.log(u"Downloading " + result.name + " from " + result.provider.name)
            status =  search.snatchEpisode(result)
            item.success = status
            generic_queue.QueueItem.finish(item)
            return status

    def process_results(self, item):
        # dynamically select our snatch queue
        if isinstance(item, sickbeard.search_queue.ManualSearchQueueItem):
            self.queue = self.ManualQueue
        elif isinstance(item, sickbeard.search_queue.BacklogQueueItem):
            self.queue = self.BacklogQueue
        elif isinstance(item, sickbeard.search_queue.FailedQueueItem):
            self.queue = self.FailedQueue

        for result in item.results:
                logger.log(u"Checking if we should snatch " + result.name, logger.DEBUG)
                show_obj = result.episodes[0].show
                any_qualities, best_qualities = Quality.splitQuality(show_obj.quality)

                # if there is a redownload that's higher than this then we definitely need to keep looking
                if best_qualities and result.quality == max(best_qualities):
                    return self.snatch_item(item)

                # if there's no redownload that's higher (above) and this is the highest initial download then we're good
                elif any_qualities and result.quality in any_qualities:
                    return self.snatch_item(item)

        # Add item to queue if we couldn't find a match to snatch
        self.add_item(item)
