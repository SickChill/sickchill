import threading
import traceback
from Queue import Queue, Empty
from sickbeard import logger
from sickrage.helper.exceptions import ex


class Event:
    def __init__(self, type):
        self._type = type

    @property
    def type(self):
        return self._type


class Events(threading.Thread):
    def __init__(self, callback):
        super(Events, self).__init__()
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
            while (not self.stop.is_set()):
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
        except Exception, e:
            logger.log(u"Exception generated in thread " + self.name + ": " + ex(e), logger.ERROR)
            logger.log(repr(traceback.format_exc()), logger.DEBUG)

    # System Events
    class SystemEvent(Event):
        RESTART = "RESTART"
        SHUTDOWN = "SHUTDOWN"
