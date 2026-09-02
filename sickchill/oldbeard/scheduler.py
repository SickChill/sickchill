import datetime
import threading
import time
import traceback

from sickchill import logger
from sickchill.oldbeard.network_timezones import sc_now, sc_timezone


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
            self.lastRun = sc_now() + self.run_delay - cycleTime
        else:
            temp_now = sc_now()
            start_today = datetime.datetime.combine(temp_now.date(), start_time, tzinfo=sc_timezone)
            if temp_now >= start_today:
                self.lastRun = start_today
            else:
                self.lastRun = start_today - datetime.timedelta(days=1)
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
        if not self.is_alive():
            return datetime.timedelta(seconds=0)

        if self.start_time is None:
            delta = sc_now() - self.lastRun
            return (self.cycleTime - delta, self.cycleTime)[delta > self.cycleTime]

        # Honor full start_time (hour and minute), not hour alone
        time_now = sc_now()
        start_time_today = datetime.datetime.combine(time_now.date(), self.start_time, tzinfo=sc_timezone)
        start_time_tomorrow = start_time_today + datetime.timedelta(days=1)
        if time_now >= start_time_today:
            return start_time_tomorrow - time_now
        return start_time_today - time_now

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
                    current_time = sc_now()
                    should_run = False
                    # Is self.force enable
                    if self.force:
                        should_run = True
                    elif self.start_time is not None:
                        # Once per day at start_time (hour+minute); run when due and not yet run today
                        start_today = datetime.datetime.combine(current_time.date(), self.start_time, tzinfo=sc_timezone)
                        if current_time >= start_today and self.lastRun < start_today:
                            should_run = True
                    elif current_time - self.lastRun >= self.cycleTime:
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
        except Exception as error:
            logger.exception(f"Exception generated in thread {self.name}: {error}")
            logger.debug(repr(traceback.format_exc()))
