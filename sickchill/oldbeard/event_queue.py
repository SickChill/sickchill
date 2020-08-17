import threading
import traceback
# noinspection PyUnresolvedReferences
from queue import Empty, Queue

from .. import logger


class Event(object):
    def __init__(self, type):
        self._type = type

    @property
    def type(self):
        return self._type


class Events(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.queue = Queue()
        self.daemon = True
        self.callback = callback
        self.name = "EVENT-QUEUE"
        self.stop = threading.Event()

    def put(self, type):
        self.queue.put(type)

    def run(self):
        """
        Actually runs the thread to process events
        """
        try:
            while not self.stop.is_set():
                try:
                    # get event type
                    type = self.queue.get(True, 1)

                    # perform callback if we got a event type
                    self.callback(type)

                    # event completed
                    self.queue.task_done()
                except Empty:
                    type = None

            # exiting thread
            self.stop.clear()
        except Exception as e:
            logger.exception("Exception generated in thread " + self.name + ": " + str(e))
            logger.debug(repr(traceback.format_exc()))

    # System Events
    class SystemEvent(Event):
        RESTART = "RESTART"
        SHUTDOWN = "SHUTDOWN"
