from threading import Thread
from Queue import Queue, Empty

class Event:
    def __init__(self, type):
        self._type = type

    @property
    def type(self):
        return self._type

class Events(Thread):
    def __init__(self, callback):
        super(Events, self).__init__()
        self.queue = Queue()
        self.daemon = True
        self.alive = True
        self.callback = callback
        self.name = "EVENT-QUEUE"

    def put(self, type):
        self.queue.put(type)

    def run(self):
        while(self.alive):
            try:
                # get event type
                type = self.queue.get(True, 1)

                # perform callback if we got a event type
                self.callback(type)

                # event completed
                self.queue.task_done()
            except Empty:
                type = None

    # System Events
    class SystemEvent(Event):
        RESTART = "RESTART"
        SHUTDOWN = "SHUTDOWN"