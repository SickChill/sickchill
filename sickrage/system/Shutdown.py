import sickbeard

from sickbeard.event_queue import Events


class Shutdown:
    def __init__(self):
        pass

    @staticmethod
    def stop(pid):
        if str(pid) != str(sickbeard.PID):
            return False

        sickbeard.events.put(Events.SystemEvent.SHUTDOWN)

        return True
