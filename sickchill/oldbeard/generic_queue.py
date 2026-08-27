import datetime
import threading

from sickchill import logger
from sickchill.oldbeard.network_timezones import sc_now


class QueuePriorities(object):
    LOW: int = 10
    NORMAL: int = 20
    HIGH: int = 30
    USER: int = 40  # UI click: after currentItem, before scheduled HIGH


class GenericQueue(object):
    def __init__(self):
        self.amActive = False

        self.currentItem = None

        self.queue = []

        self.queue_name = "QUEUE"

        self.min_priority = 0

        self.lock = threading.Lock()

    def __len__(self):
        _len = len(self.queue)
        if self.currentItem:
            _len += 1
        return _len

    def pause(self):
        """Pauses this queue"""
        logger.info("Pausing queue")
        self.min_priority = 999999999999

    def unpause(self):
        """Unpauses this queue"""
        logger.info("Unpausing queue")
        self.min_priority = 0

    def _apply_front(self, item):
        """Raise priority to USER and date the item so it sorts next after currentItem."""
        item.priority = max(item.priority, QueuePriorities.USER)
        # Last promote/click first among USER items
        waiting = [x.added for x in self.queue if x is not item and x.priority >= QueuePriorities.USER and x.added is not None]
        if waiting:
            item.added = min(waiting) - datetime.timedelta(microseconds=1)
        elif item.added is None:
            item.added = sc_now()

    def add_item(self, item, front=False):
        """
        Adds an item to this queue

        :param item: Queue object to add
        :param front: If True, bump to USER priority so it runs next after currentItem
            (last USER click runs first among USER items). Cannot preempt currentItem
            or outrank Remove (HIGH**2).
        :return: item
        """
        with self.lock:
            item.added = sc_now()
            if front:
                self._apply_front(item)
            self.queue.append(item)

            return item

    def promote_item(self, item):
        """
        Promote an already-queued item to run next after currentItem (USER priority).

        :return: item if it was in the queue and promoted, else None
        """
        with self.lock:
            if item not in self.queue:
                return None
            self._apply_front(item)
            return item

    def run(self, force=False):
        """
        Process items in this queue

        :param force: Force queue processing (currently not implemented)
        """
        self.amActive = True

        with self.lock:
            # only start a new task if one isn't already going
            if self.currentItem is None or not self.currentItem.is_alive():
                # if the thread is dead then the current item should be finished
                if self.currentItem:
                    self.currentItem.finish()
                    self.currentItem = None

                # if there's something in the queue then run it in a thread and take it out of the queue
                if self.queue:
                    from functools import cmp_to_key

                    # sort by priority
                    def sorter(x, y):
                        """
                        Sorts by priority descending then time ascending
                        """
                        if x.priority == y.priority:
                            if y.added == x.added:
                                return 0
                            elif y.added < x.added:
                                return 1
                            elif y.added > x.added:
                                return -1
                        else:
                            return y.priority - x.priority

                    self.queue.sort(key=cmp_to_key(sorter))
                    if self.queue[0].priority < self.min_priority:
                        return

                    # launch the queue item in a thread
                    self.currentItem = self.queue.pop(0)
                    self.currentItem.name = self.queue_name + "-" + self.currentItem.name
                    self.currentItem.start()

        self.amActive = False


class QueueItem(threading.Thread):
    def __init__(self, name, action_id=0):
        super().__init__()

        self.name = name.replace(" ", "-").upper()
        self.inProgress = False
        self.priority = QueuePriorities.NORMAL
        self.action_id = action_id
        self.stop = threading.Event()
        self.added = None

    def run(self):
        """Implementing classes should call this"""

        self.inProgress = True

    def finish(self):
        """Implementing Classes should call this"""

        self.inProgress = False

        threading.current_thread().name = self.name
