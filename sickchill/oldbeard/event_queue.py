import threading
import traceback
from queue import Empty, Queue

from .. import logger


class Event(object):
    def __init__(self, event_type):
        self.event_type = event_type

    @property
    def type(self):
        return self.event_type


class Events(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.queue = Queue()
        self.daemon = True
        self.callback = callback
        self.name = "EVENT-QUEUE"
        self.stop = threading.Event()

    def put(self, event_type):
        self.queue.put(event_type)

    def run(self):
        """
        Actually runs the thread to process events
        """
        try:
            while not self.stop.is_set():
                try:
                    # get event type
                    event_type = self.queue.get(timeout=1)

                    # perform callback if we got a event type
                    self.callback(event_type)

                    # event completed
                    self.queue.task_done()
                except Empty:
                    pass

            # exiting thread
            self.stop.clear()
        except Exception as error:
            logger.exception(f"Exception generated in thread {self.name}: {error}")
            logger.debug(traceback.format_exc())

    # System Events
    class SystemEvent(Event):
        RESTART = "RESTART"
        SHUTDOWN = "SHUTDOWN"
