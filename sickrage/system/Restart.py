import sickbeard

from sickbeard.event_queue import Events


class Restart:
    def __init__(self):
        pass

    @staticmethod
    def restart(pid):
        if str(pid) != str(sickbeard.PID):
            return False

        sickbeard.events.put(Events.SystemEvent.RESTART)

        return True
