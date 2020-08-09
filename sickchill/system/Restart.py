from sickchill import settings
from sickchill.oldbeard.event_queue import Events


class Restart(object):
    def __init__(self):
        pass

    @staticmethod
    def restart(pid):
        if str(pid) != str(settings.PID):
            return False

        settings.events.put(Events.SystemEvent.RESTART)

        return True
