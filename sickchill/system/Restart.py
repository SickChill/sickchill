from sickchill import settings
from sickchill.helper.event_queue import Events


class Restart(object):
    def __init__(self):
        pass

    @staticmethod
    def restart(pid):
        if str(pid) != str(settings.PID):
            return False

        settings.events.put(Events.SystemEvent.RESTART)
        settings.restarting = True

        return True
