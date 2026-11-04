import datetime
import threading

from sickchill import logger
from sickchill.oldbeard.network_timezones import sc_now


class QueuePriorities(object):
    LOW: int = 10
    NORMAL: int = 20
    HIGH: int = 30
    USER: int = 40  # UI click: after currentItem, before scheduled HIGH
    CONNECTIVITY: int = 50  # above USER; internet probe while a network item is stuck


class GenericQueue(object):
    def __init__(self):
        self.amActive = False

        self.currentItem = None

        self.queue = []

        self.queue_name = "QUEUE"

        self.min_priority = 0

        self.lock = threading.Lock()

        self.watch_stuck_items = False
        self._connectivity_paused = False
        self._min_priority_before_connectivity = 0
        self._connectivity_warned = False
        self._connectivity_attempt = 0
        self._off_queue_probe_thread = None
        self._off_queue_probe_stop = None

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

    def stop_current_item(self, timeout: float = 10):
        """
        Signal the running queue worker to stop and wait briefly.

        Used on shutdown/restart so we do not only join the scheduler thread while a
        SHOWQUEUE-REFRESH (or similar) worker stays stuck forever. A hung worker may
        still not exit (Python cannot kill threads); we log and continue after timeout.
        """
        stop = self._off_queue_probe_stop
        if stop is not None:
            stop.set()

        with self.lock:
            item = self.currentItem

        if not item:
            return

        name = getattr(item, "name", "queue-item")
        if getattr(item, "stop", None) is not None:
            item.stop.set()
            logger.info(f"Signaled {name} to stop")

        if item.is_alive() and timeout > 0:
            logger.info(f"Waiting up to {timeout:g}s for {name} to exit")
            item.join(timeout)
            if not item.is_alive():
                logger.info(f"{name} exited")

        if item.is_alive():
            # Keep currentItem set so Scheduler.run will not start another worker
            # while this one is still running after the join timeout.
            if timeout > 0:
                logger.warning(f"{name} did not exit within {timeout:g}s; leaving as currentItem")
            return

        with self.lock:
            if self.currentItem is item:
                try:
                    item.finish()
                except Exception:
                    pass
                self.currentItem = None

    def stuck_threshold(self, item):
        from sickchill import settings

        return int(getattr(settings, "CONNECTIVITY_STUCK_DEFAULT", 900) or 900)

    def connectivity_status(self):
        if self._connectivity_paused:
            return "paused"
        if self._has_connectivity_check():
            return "checking"
        return "ok"

    def _is_connectivity_item(self, item):
        if item is None:
            return False
        from sickchill.oldbeard.connectivity import ConnectivityCheckQueueItem

        return isinstance(item, ConnectivityCheckQueueItem)

    def _queued_connectivity_check(self):
        return any(self._is_connectivity_item(item) for item in self.queue)

    def _off_queue_probe_running(self):
        thread = self._off_queue_probe_thread
        return thread is not None and thread.is_alive()

    def _current_item_blocks_probe(self):
        item = self.currentItem
        return item is not None and item.is_alive() and not self._is_connectivity_item(item)

    def _wait_connectivity_retry(self, delay: float) -> bool:
        """Wait delay seconds. Return False if the off-queue probe was asked to stop."""
        stop = self._off_queue_probe_stop
        if stop is None:
            return True
        if delay <= 0:
            return not stop.is_set()
        return not stop.wait(delay)

    def _has_connectivity_check(self):
        return self._is_connectivity_item(self.currentItem) or self._queued_connectivity_check() or self._off_queue_probe_running()

    def pause_for_connectivity(self):
        if not self._connectivity_paused:
            self._min_priority_before_connectivity = self.min_priority
            self._connectivity_paused = True
        if self.min_priority < QueuePriorities.CONNECTIVITY:
            self.min_priority = QueuePriorities.CONNECTIVITY

    def resume_after_connectivity(self, *, propagate=True):
        if self._connectivity_paused:
            self.min_priority = self._min_priority_before_connectivity
            self._connectivity_paused = False
        self._connectivity_warned = False
        self._connectivity_attempt = 0
        if propagate:
            from sickchill.oldbeard.connectivity import iter_network_queues

            for other in iter_network_queues():
                if other is not self:
                    other.resume_after_connectivity(propagate=False)

    def handle_connectivity_failure(self, check_item):
        from sickchill.oldbeard.connectivity import STAGED_ATTEMPTS, delay_after_failure

        raw_attempt = check_item if isinstance(check_item, int) else getattr(check_item, "attempt", 1)
        attempt = max(1, int(raw_attempt or 1))
        self._connectivity_attempt = attempt
        self.pause_for_connectivity()
        delay = delay_after_failure(attempt)
        logger.debug("Connectivity check failed (attempt %s); retrying in %ss", attempt, delay)
        if attempt >= STAGED_ATTEMPTS and not self._connectivity_warned:
            logger.warning(
                "Connectivity check failed after %d staged retries; internet appears unavailable. Queue remains paused.",
                STAGED_ATTEMPTS,
            )
            self._connectivity_warned = True
        if self._current_item_blocks_probe():
            return
        self._enqueue_connectivity_retry(attempt + 1, delay)

    def _enqueue_connectivity_check(self):
        from sickchill.oldbeard.connectivity import ConnectivityCheckQueueItem

        check = ConnectivityCheckQueueItem(self)
        self.add_item(check, front=True)
        check.priority = QueuePriorities.CONNECTIVITY

    def _enqueue_connectivity_retry(self, attempt: int, delay: float = 0):
        from sickchill.oldbeard.connectivity import ConnectivityCheckQueueItem

        nxt = ConnectivityCheckQueueItem(self, attempt=attempt)
        if delay:
            nxt.not_before = sc_now() + datetime.timedelta(seconds=delay)
        nxt.priority = QueuePriorities.CONNECTIVITY
        self.add_item(nxt)

    def _start_off_queue_connectivity_probe(self, attempt: int = 1):
        if self._off_queue_probe_running():
            return
        self.pause_for_connectivity()
        self._off_queue_probe_stop = threading.Event()
        thread = threading.Thread(
            target=self._run_off_queue_connectivity_probe,
            args=(attempt,),
            name=f"{self.queue_name}-CONNECTIVITY-CHECK",
            daemon=True,
        )
        self._off_queue_probe_thread = thread
        thread.start()

    def _run_off_queue_connectivity_probe(self, attempt: int = 1):
        from sickchill.oldbeard.connectivity import delay_after_failure, run_connectivity_probe

        try:
            current_attempt = max(1, int(attempt or 1))
            while True:
                try:
                    run_connectivity_probe(self, current_attempt)
                except Exception as error:
                    logger.debug("Off-queue connectivity probe raised %s: %s", type(error).__name__, error)
                    self.handle_connectivity_failure(current_attempt)
                if not self._connectivity_paused:
                    return
                if not self._current_item_blocks_probe():
                    if not self._queued_connectivity_check() and not self._is_connectivity_item(self.currentItem):
                        self._enqueue_connectivity_retry(current_attempt + 1, delay_after_failure(current_attempt))
                    return
                delay = delay_after_failure(current_attempt)
                if not self._wait_connectivity_retry(delay):
                    return
                current_attempt += 1
                if not self._current_item_blocks_probe():
                    self._enqueue_connectivity_retry(current_attempt)
                    return
        finally:
            if threading.current_thread() is self._off_queue_probe_thread:
                self._off_queue_probe_thread = None

    def request_connectivity_check(self, reason="network error"):
        """
        Enqueue a connectivity probe after a DNS/connect failure.

        Does not stop currentItem: this is often called from that thread, and join() would deadlock.
        """
        from sickchill import settings

        if not getattr(settings, "CONNECTIVITY_CHECK", True):
            return
        if self._has_connectivity_check():
            return
        logger.info("Injecting high-priority connectivity check due to network error: %s", reason)
        self.pause_for_connectivity()
        from sickchill.oldbeard.connectivity import iter_network_queues

        for other in iter_network_queues():
            if other is not self:
                other.pause_for_connectivity()
        self._enqueue_connectivity_check()

    def inject_connectivity_check(self, stuck_item):
        if self._has_connectivity_check():
            return
        name = getattr(stuck_item, "name", "queue-item")
        logger.info("Injecting high-priority connectivity check due to stuck queue item: %s", name)
        # Signal stop without blocking the scheduler; hung search items do not read self.stop.
        self.stop_current_item(timeout=0)
        if self.currentItem is not None and self.currentItem.is_alive() and not self._is_connectivity_item(self.currentItem):
            self._start_off_queue_connectivity_probe()
            return
        self._enqueue_connectivity_check()

    def _maybe_inject_connectivity_check(self):
        from sickchill import settings

        if not self.watch_stuck_items or not getattr(settings, "CONNECTIVITY_CHECK", True):
            return
        item = self.currentItem
        if not item or not item.is_alive() or self._is_connectivity_item(item):
            return
        if self._has_connectivity_check():
            return
        started_at = getattr(item, "started_at", None)
        if started_at is None:
            return
        elapsed = (sc_now() - started_at).total_seconds()
        if elapsed < self.stuck_threshold(item):
            return
        self.inject_connectivity_check(item)

    def run(self, force=False):
        """
        Process items in this queue

        :param force: Force queue processing (currently not implemented)
        """
        self.amActive = True
        try:
            if self.watch_stuck_items:
                self._maybe_inject_connectivity_check()

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
                        now = sc_now()
                        chosen_index = None
                        for i, item in enumerate(self.queue):
                            if item.not_before is not None and item.not_before > now:
                                continue
                            if item.priority < self.min_priority:
                                continue
                            chosen_index = i
                            break
                        if chosen_index is None:
                            return

                        # launch the queue item in a thread
                        self.currentItem = self.queue.pop(chosen_index)
                        self.currentItem.name = self.queue_name + "-" + self.currentItem.name
                        self.currentItem.started_at = sc_now()
                        self.currentItem.start()
        finally:
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
        self.started_at = None
        self.not_before = None

    def run(self):
        """Implementing classes should call this"""

        self.inProgress = True

    def finish(self):
        """Implementing Classes should call this"""

        self.inProgress = False

        threading.current_thread().name = self.name
