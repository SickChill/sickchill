from sickchill import settings
from sickchill.oldbeard.event_queue import Events


class Shutdown(object):
    def __init__(self):
        pass

    @staticmethod
    def stop(pid):
        if str(pid) != str(settings.PID):
            return False

        settings.events.put(Events.SystemEvent.SHUTDOWN)

        return True
