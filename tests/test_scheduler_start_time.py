"""Scheduler start_time should honor hour and minute."""

from __future__ import annotations

import datetime
import unittest
from unittest import mock

from sickchill.oldbeard.network_timezones import sc_timezone
from sickchill.oldbeard.scheduler import Scheduler


class TestSchedulerStartTime(unittest.TestCase):
    def test_time_left_uses_minute(self):
        # Fixed "now": 10:15 — start_time today 10:30 → about 15 minutes left
        now = datetime.datetime(2026, 9, 2, 10, 15, 0, tzinfo=sc_timezone)
        start = datetime.time(hour=10, minute=30)

        with mock.patch("sickchill.oldbeard.scheduler.sc_now", return_value=now):
            sched = Scheduler(action=mock.Mock(), cycleTime=datetime.timedelta(hours=1), start_time=start)
            with mock.patch.object(sched, "is_alive", return_value=True):
                left = sched.timeLeft()

        self.assertAlmostEqual(left.total_seconds(), 15 * 60, delta=1)

    def test_time_left_after_start_rolls_to_tomorrow(self):
        now = datetime.datetime(2026, 9, 2, 10, 45, 0, tzinfo=sc_timezone)
        start = datetime.time(hour=10, minute=30)

        with mock.patch("sickchill.oldbeard.scheduler.sc_now", return_value=now):
            sched = Scheduler(action=mock.Mock(), cycleTime=datetime.timedelta(hours=1), start_time=start)
            with mock.patch.object(sched, "is_alive", return_value=True):
                left = sched.timeLeft()

        expected = datetime.datetime(2026, 9, 3, 10, 30, 0, tzinfo=sc_timezone) - now
        self.assertAlmostEqual(left.total_seconds(), expected.total_seconds(), delta=1)


if __name__ == "__main__":
    unittest.main()
