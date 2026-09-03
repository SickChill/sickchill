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
        self._schedule_lock = threading.Lock()
        if start_time is None:
            self.lastRun = sc_now() + self.run_delay - cycleTime
        else:
            # Daily-at-start_time jobs: if today's slot has already passed, treat it as
            # done so we do not fire immediately on startup; otherwise due today.
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

    def set_start_time(self, start_time: datetime.time | None, *, mark_ran_today: bool = False) -> None:
        """
        Atomically update ``start_time`` (and optionally the daily-run marker ``lastRun``).

        ``mark_ran_today`` should be set when changing the time after a completed run so
        Scheduler.run does not treat a later minute the same day as a new due slot.
        """
        with self._schedule_lock:
            self.start_time = start_time
            if mark_ran_today and start_time is not None:
                now = sc_now()
                start_today = datetime.datetime.combine(now.date(), start_time, tzinfo=sc_timezone)
                if self.lastRun is None or self.lastRun < start_today:
                    self.lastRun = start_today

    def set_start_hour(self, hour: int) -> None:
        """Keep the existing minute; replace only the hour (config UI)."""
        with self._schedule_lock:
            minute = self.start_time.minute if self.start_time else 0
            self.start_time = datetime.time(hour=hour, minute=minute)

    def bump_start_minute(self, delta_minutes: int, *, mark_ran_today: bool = True) -> datetime.time | None:
        """
        Add ``delta_minutes`` to ``start_time.minute`` (wrap if > 60).

        Used by ShowUpdater after a daily run. Updates ``lastRun`` when
        ``mark_ran_today`` so the scheduler will not fire again the same day.
        """
        with self._schedule_lock:
            if not self.start_time:
                return None
            hour = self.start_time.hour
            new_minute = self.start_time.minute + int(delta_minutes)
            if new_minute > 60:
                new_minute -= 60
            if new_minute == 60:
                new_minute = 0
            self.start_time = datetime.time(hour=hour, minute=new_minute)
            if mark_ran_today:
                now = sc_now()
                start_today = datetime.datetime.combine(now.date(), self.start_time, tzinfo=sc_timezone)
                if self.lastRun is None or self.lastRun < start_today:
                    self.lastRun = start_today
            return self.start_time

    def timeLeft(self):
        """
        Check how long we have until we run again
        :return: timedelta
        """
        if not self.is_alive():
            return datetime.timedelta(seconds=0)

        with self._schedule_lock:
            start_time = self.start_time
            last_run = self.lastRun
            cycle_time = self.cycleTime

        if start_time is None:
            delta = sc_now() - last_run
            return (cycle_time - delta, cycle_time)[delta > cycle_time]

        # Honor full start_time (hour and minute), not hour alone
        time_now = sc_now()
        start_time_today = datetime.datetime.combine(time_now.date(), start_time, tzinfo=sc_timezone)
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
                    else:
                        with self._schedule_lock:
                            start_time = self.start_time
                            last_run = self.lastRun
                            cycle_time = self.cycleTime
                        if start_time is not None:
                            # Once per day at start_time (hour+minute); run when due and not yet run today
                            start_today = datetime.datetime.combine(current_time.date(), start_time, tzinfo=sc_timezone)
                            if current_time >= start_today and last_run < start_today:
                                should_run = True
                        elif current_time - last_run >= cycle_time:
                            should_run = True

                    if should_run:
                        with self._schedule_lock:
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
