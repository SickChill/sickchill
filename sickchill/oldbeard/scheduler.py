import datetime
import threading
import time
import traceback

from .. import logger


class Scheduler(threading.Thread):
    def __init__(
        self,
        action,
        cycleTime=datetime.timedelta(minutes=10),
        run_delay=datetime.timedelta(minutes=0),
        start_time=None,
        threadName="ScheduledThread",
        silent=True,
    ):
        super().__init__()

        self.run_delay = run_delay
        if start_time is None:
            self.lastRun = datetime.datetime.now() + self.run_delay - cycleTime
        else:
            # Set last run to the last full hour
            temp_now = datetime.datetime.now()
            self.lastRun = datetime.datetime(temp_now.year, temp_now.month, temp_now.day, temp_now.hour, 0, 0, 0) + self.run_delay - cycleTime
        self.action = action
        self.cycleTime = cycleTime
        self.start_time = start_time

        self.name = threadName
        self.silent = silent
        self.stop = threading.Event()
        self.force = False
        self.enable = False

    def timeLeft(self):
        """
        Check how long we have until we run again
        :return: timedelta
        """
        if self.is_alive():
            if self.start_time is None:
                delta = datetime.datetime.now() - self.lastRun
                return (self.cycleTime - delta, self.cycleTime)[delta > self.cycleTime]
            else:
                time_now = datetime.datetime.now()
                start_time_today = datetime.datetime.combine(time_now.date(), self.start_time)
                start_time_tomorrow = start_time_today + datetime.timedelta(days=1)
                if time_now.hour >= self.start_time.hour:
                    return start_time_tomorrow - time_now
                elif time_now.hour < self.start_time.hour:
                    return start_time_today - time_now
        else:
            return datetime.timedelta(seconds=0)

    def forceRun(self):
        if not self.action.amActive:
            self.force = True
            return True
        return False

    def run(self):
        """
        Runs the thread
        """
        try:
            while not self.stop.is_set():
                if self.enable:
                    current_time = datetime.datetime.now()
                    should_run = False
                    # Is self.force enable
                    if self.force:
                        should_run = True
                    # check if interval has passed
                    elif current_time - self.lastRun >= self.cycleTime:
                        # check if wanting to start around certain time taking interval into account
                        if self.start_time is not None:
                            hour_diff = current_time.time().hour - self.start_time.hour
                            if not hour_diff < 0 and hour_diff < self.cycleTime.seconds / 3600:
                                should_run = True
                            else:
                                # set lastRun to only check start_time after another cycleTime
                                self.lastRun = current_time
                        else:
                            should_run = True

                    if should_run:
                        self.lastRun = current_time
                        if not self.silent:
                            logger.debug("Starting new thread: " + self.name)
                        self.action.run(self.force)

                    if self.force:
                        self.force = False

                time.sleep(1)
            # exiting thread
            self.stop.clear()
        except Exception as e:
            logger.exception("Exception generated in thread " + self.name + ": " + str(e))
            logger.debug(repr(traceback.format_exc()))
