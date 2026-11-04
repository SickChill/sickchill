"""Search-queue connectivity check: stuck detection, backoff, pause/resume."""

from __future__ import annotations

import datetime
import threading
import unittest
from unittest.mock import MagicMock, patch

from sickchill.oldbeard import connectivity, generic_queue
from sickchill.oldbeard.connectivity import ConnectivityCheckQueueItem
from sickchill.oldbeard.generic_queue import GenericQueue, QueueItem, QueuePriorities
from sickchill.oldbeard.network_timezones import sc_now
from sickchill.oldbeard.search_queue import DailySearchQueueItem, SearchQueue
from sickchill.show.indexers.tvdb_v4_client import TVDBv4Error
from sickchill.show.indexers.wrappers import ExceptionDecorator


class TestProbeConnectivity(unittest.TestCase):
    def test_parse_hosts_default_when_empty(self):
        self.assertEqual(connectivity.parse_connectivity_hosts(""), list(connectivity.DEFAULT_HOSTS))

    def test_default_hosts_include_https_fallback(self):
        self.assertIn(("1.1.1.1", 53), connectivity.DEFAULT_HOSTS)
        self.assertIn(("8.8.8.8", 53), connectivity.DEFAULT_HOSTS)
        self.assertIn(("1.1.1.1", 443), connectivity.DEFAULT_HOSTS)

    def test_parse_hosts_custom(self):
        self.assertEqual(connectivity.parse_connectivity_hosts("9.9.9.9:53,1.0.0.1:443"), [("9.9.9.9", 53), ("1.0.0.1", 443)])

    def test_probe_succeeds_on_first_host(self):
        with (
            patch("sickchill.oldbeard.connectivity.settings.PROXY_SETTING", ""),
            patch("sickchill.oldbeard.connectivity.socket.create_connection") as connect,
        ):
            connect.return_value.__enter__.return_value = MagicMock()
            self.assertTrue(connectivity.probe_connectivity([("1.1.1.1", 53)], timeout=1))
            connect.assert_called_once()

    def test_probe_fails_when_all_hosts_raise(self):
        with (
            patch("sickchill.oldbeard.connectivity.settings.PROXY_SETTING", ""),
            patch("sickchill.oldbeard.connectivity.socket.create_connection", side_effect=OSError("offline")),
        ):
            self.assertFalse(connectivity.probe_connectivity([("1.1.1.1", 53), ("8.8.8.8", 53)], timeout=1))

    def test_probe_skips_overflow_and_tries_next_host(self):
        cm = MagicMock()
        cm.__enter__.return_value = MagicMock()
        with (
            patch("sickchill.oldbeard.connectivity.settings.PROXY_SETTING", ""),
            patch("sickchill.oldbeard.connectivity.socket.create_connection", side_effect=[OverflowError("port"), cm]) as connect,
        ):
            self.assertTrue(connectivity.probe_connectivity([("1.1.1.1", 70000), ("1.1.1.1", 443)], timeout=1))
            self.assertEqual(connect.call_count, 2)

    def test_probe_treats_value_error_as_miss(self):
        with (
            patch("sickchill.oldbeard.connectivity.settings.PROXY_SETTING", ""),
            patch("sickchill.oldbeard.connectivity.socket.create_connection", side_effect=UnicodeError("bad host")),
        ):
            self.assertFalse(connectivity.probe_connectivity([("a..b", 53)], timeout=1))

    def test_probe_uses_proxy_when_configured(self):
        cm = MagicMock()
        cm.__enter__.return_value = MagicMock()
        with (
            patch("sickchill.oldbeard.connectivity.settings.PROXY_SETTING", "http://127.0.0.1:8888"),
            patch("sickchill.oldbeard.connectivity.socket.create_connection", return_value=cm) as connect,
        ):
            self.assertTrue(connectivity.probe_connectivity([("1.1.1.1", 53)], timeout=1))
            connect.assert_called_once_with(("127.0.0.1", 8888), timeout=1)

    def test_probe_treats_unparseable_proxy_as_success(self):
        with (
            patch("sickchill.oldbeard.connectivity.settings.PROXY_SETTING", "://"),
            patch("sickchill.oldbeard.connectivity.socket.create_connection") as connect,
        ):
            self.assertTrue(connectivity.probe_connectivity([("1.1.1.1", 53)], timeout=1))
            connect.assert_not_called()

    def test_delay_after_failure_progression(self):
        self.assertEqual(connectivity.delay_after_failure(1), 15)
        self.assertEqual(connectivity.delay_after_failure(2), 30)
        self.assertEqual(connectivity.delay_after_failure(3), 90)
        self.assertEqual(connectivity.delay_after_failure(4), 300)
        self.assertEqual(connectivity.delay_after_failure(5), 1800)
        self.assertEqual(connectivity.delay_after_failure(20), 1800)


class TestGenericQueueConnectivity(unittest.TestCase):
    def test_processing_queue_does_not_watch_stuck_items(self):
        from sickchill.oldbeard.post_processing_queue import ProcessingQueue

        self.assertFalse(ProcessingQueue().watch_stuck_items)
        self.assertTrue(SearchQueue().watch_stuck_items)

    def test_not_before_skips_item(self):
        q = GenericQueue()
        item = QueueItem("later")
        q.add_item(item)
        item.not_before = sc_now() + datetime.timedelta(hours=1)
        q.run()
        self.assertIsNone(q.currentItem)
        self.assertIn(item, q.queue)
        self.assertFalse(q.amActive)

    def test_min_priority_does_not_leave_am_active(self):
        q = GenericQueue()
        q.min_priority = QueuePriorities.CONNECTIVITY
        q.add_item(QueueItem("low"))
        q.run()
        self.assertFalse(q.amActive)
        self.assertEqual(len(q.queue), 1)

    def test_pause_restore_keeps_prior_backlog_pause(self):
        q = GenericQueue()
        q.min_priority = QueuePriorities.HIGH
        q.pause_for_connectivity()
        self.assertEqual(q.min_priority, QueuePriorities.CONNECTIVITY)
        self.assertEqual(q.connectivity_status(), "paused")
        q.resume_after_connectivity()
        self.assertEqual(q.min_priority, QueuePriorities.HIGH)
        self.assertEqual(q.connectivity_status(), "ok")


class TestSearchQueueStuckInjection(unittest.TestCase):
    def test_injects_one_check_when_current_has_stopped(self):
        q = SearchQueue()
        stuck = DailySearchQueueItem()
        stuck.started_at = sc_now() - datetime.timedelta(hours=2)
        stuck.success = False
        stuck.is_alive = MagicMock(return_value=True)
        q.currentItem = stuck

        def stop(timeout=5):
            q.currentItem = None

        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch.object(q, "stop_current_item", side_effect=stop),
        ):
            q._maybe_inject_connectivity_check()
            q._maybe_inject_connectivity_check()

        checks = [item for item in q.queue if isinstance(item, ConnectivityCheckQueueItem)]
        dailies = [item for item in q.queue if isinstance(item, DailySearchQueueItem)]
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].priority, QueuePriorities.CONNECTIVITY)
        self.assertEqual(len(dailies), 0)
        self.assertEqual(q.connectivity_status(), "checking")

    def test_below_threshold_does_not_inject(self):
        q = SearchQueue()
        stuck = DailySearchQueueItem()
        stuck.started_at = sc_now()
        stuck.is_alive = MagicMock(return_value=True)
        q.currentItem = stuck
        with patch("sickchill.settings.CONNECTIVITY_CHECK", True), patch("sickchill.settings.CONNECTIVITY_STUCK_DAILY", 1800):
            q._maybe_inject_connectivity_check()
        self.assertFalse(any(isinstance(item, ConnectivityCheckQueueItem) for item in q.queue))

    def test_failure_pauses_and_warns_once(self):
        q = SearchQueue()
        failed = ConnectivityCheckQueueItem(q, attempt=connectivity.STAGED_ATTEMPTS)
        with patch.object(generic_queue.logger, "warning") as warning:
            q.handle_connectivity_failure(failed)
            q.handle_connectivity_failure(ConnectivityCheckQueueItem(q, attempt=connectivity.STAGED_ATTEMPTS + 1))
        self.assertEqual(q.min_priority, QueuePriorities.CONNECTIVITY)
        self.assertTrue(q._connectivity_paused)
        self.assertEqual(warning.call_count, 1)
        retries = [item for item in q.queue if isinstance(item, ConnectivityCheckQueueItem)]
        self.assertEqual(len(retries), 1)
        self.assertIsNotNone(retries[0].not_before)

    def test_check_success_resumes_queue(self):
        q = SearchQueue()
        q.pause_for_connectivity()
        item = ConnectivityCheckQueueItem(q, attempt=3)
        with patch("sickchill.oldbeard.connectivity.probe_connectivity", return_value=True):
            item.run()
        self.assertFalse(q._connectivity_paused)
        self.assertEqual(q.min_priority, 0)

    def test_check_item_run_treats_probe_exception_as_failure(self):
        q = SearchQueue()
        item = ConnectivityCheckQueueItem(q, attempt=1)
        with patch("sickchill.oldbeard.connectivity.probe_connectivity", side_effect=RuntimeError("boom")):
            item.run()
        self.assertTrue(q._connectivity_paused)
        self.assertEqual(q.min_priority, QueuePriorities.CONNECTIVITY)
        retries = [queued for queued in q.queue if isinstance(queued, ConnectivityCheckQueueItem)]
        self.assertEqual(len(retries), 1)
        self.assertEqual(retries[0].attempt, 2)

    def test_inject_runs_probe_off_queue_when_current_still_alive(self):
        q = SearchQueue()
        stuck = DailySearchQueueItem()
        stuck.started_at = sc_now() - datetime.timedelta(hours=2)
        stuck.is_alive = MagicMock(return_value=True)
        stuck.join = MagicMock()
        q.currentItem = stuck
        started = threading.Event()
        release = threading.Event()

        def slow_probe(*args, **kwargs):
            started.set()
            self.assertTrue(release.wait(timeout=2))
            return True

        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.oldbeard.connectivity.probe_connectivity", side_effect=slow_probe) as probe,
        ):
            q._maybe_inject_connectivity_check()
            q._maybe_inject_connectivity_check()
            self.assertTrue(started.wait(timeout=2))
            stuck.join.assert_not_called()
            self.assertIs(q.currentItem, stuck)
            self.assertFalse(any(isinstance(item, ConnectivityCheckQueueItem) for item in q.queue))
            self.assertTrue(q._off_queue_probe_running())
            self.assertTrue(q._has_connectivity_check())
            release.set()
            thread = q._off_queue_probe_thread
            self.assertIsNotNone(thread)
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            probe.assert_called_once()
            self.assertFalse(q._connectivity_paused)
            self.assertEqual(q.min_priority, 0)

            q._maybe_inject_connectivity_check()
            self.assertFalse(q._off_queue_probe_running())
            probe.assert_called_once()

        other = DailySearchQueueItem()
        other.started_at = sc_now() - datetime.timedelta(hours=2)
        other.is_alive = MagicMock(return_value=True)
        other.join = MagicMock()
        q.currentItem = other
        started2 = threading.Event()
        release2 = threading.Event()

        def slow_probe_other(*args, **kwargs):
            started2.set()
            self.assertTrue(release2.wait(timeout=2))
            return True

        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.oldbeard.connectivity.probe_connectivity", side_effect=slow_probe_other) as probe2,
        ):
            q._maybe_inject_connectivity_check()
            self.assertTrue(started2.wait(timeout=2))
            release2.set()
            thread2 = q._off_queue_probe_thread
            self.assertIsNotNone(thread2)
            thread2.join(timeout=2)
            self.assertFalse(thread2.is_alive())
            probe2.assert_called_once()

    def test_inject_off_queue_failure_retries_until_reachable(self):
        q = SearchQueue()
        stuck = DailySearchQueueItem()
        stuck.started_at = sc_now() - datetime.timedelta(hours=2)
        stuck.is_alive = MagicMock(return_value=True)
        stuck.join = MagicMock()
        q.currentItem = stuck
        started = threading.Event()
        release = threading.Event()
        results = iter((False, True))

        def fail_then_reach(*args, **kwargs):
            started.set()
            self.assertTrue(release.wait(timeout=2))
            return next(results)

        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.oldbeard.connectivity.probe_connectivity", side_effect=fail_then_reach) as probe,
            patch("sickchill.oldbeard.connectivity.delay_after_failure", return_value=0),
        ):
            q.inject_connectivity_check(stuck)
            self.assertTrue(started.wait(timeout=2))
            stuck.join.assert_not_called()
            thread = q._off_queue_probe_thread
            self.assertIsNotNone(thread)
            release.set()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(probe.call_count, 2)

        self.assertFalse(q._connectivity_paused)
        self.assertEqual(q.min_priority, 0)
        self.assertFalse(any(isinstance(item, ConnectivityCheckQueueItem) for item in q.queue))

    def test_inject_off_queue_failure_does_not_queue_behind_hung_item(self):
        q = SearchQueue()
        stuck = DailySearchQueueItem()
        stuck.started_at = sc_now() - datetime.timedelta(hours=2)
        stuck.is_alive = MagicMock(return_value=True)
        stuck.join = MagicMock()
        q.currentItem = stuck
        started = threading.Event()
        release = threading.Event()
        calls = {"n": 0}

        def fail_then_stop(*args, **kwargs):
            calls["n"] += 1
            started.set()
            self.assertTrue(release.wait(timeout=2))
            if calls["n"] >= 2 and q._off_queue_probe_stop is not None:
                q._off_queue_probe_stop.set()
            return False

        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.oldbeard.connectivity.probe_connectivity", side_effect=fail_then_stop),
            patch("sickchill.oldbeard.connectivity.delay_after_failure", return_value=0),
        ):
            q.inject_connectivity_check(stuck)
            self.assertTrue(started.wait(timeout=2))
            self.assertTrue(q._off_queue_probe_running())
            self.assertFalse(any(isinstance(item, ConnectivityCheckQueueItem) for item in q.queue))
            release.set()
            thread = q._off_queue_probe_thread
            self.assertIsNotNone(thread)
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())

        self.assertGreaterEqual(calls["n"], 2)
        self.assertTrue(q._connectivity_paused)
        self.assertFalse(any(isinstance(item, ConnectivityCheckQueueItem) for item in q.queue))

    def test_off_queue_enqueues_when_blocker_exits_mid_probe(self):
        q = SearchQueue()
        stuck = DailySearchQueueItem()
        stuck.started_at = sc_now() - datetime.timedelta(hours=2)
        stuck.is_alive = MagicMock(return_value=True)
        stuck.join = MagicMock()
        q.currentItem = stuck
        started = threading.Event()
        release = threading.Event()

        def fail_probe(*args, **kwargs):
            started.set()
            self.assertTrue(release.wait(timeout=2))
            return False

        def handle_then_free(check_item):
            GenericQueue.handle_connectivity_failure(q, check_item)
            q.currentItem = None

        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.oldbeard.connectivity.probe_connectivity", side_effect=fail_probe),
            patch.object(q, "handle_connectivity_failure", side_effect=handle_then_free),
        ):
            q.inject_connectivity_check(stuck)
            self.assertTrue(started.wait(timeout=2))
            thread = q._off_queue_probe_thread
            self.assertIsNotNone(thread)
            self.assertFalse(any(isinstance(item, ConnectivityCheckQueueItem) for item in q.queue))
            release.set()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())

        retries = [item for item in q.queue if isinstance(item, ConnectivityCheckQueueItem)]
        self.assertEqual(len(retries), 1)
        self.assertEqual(retries[0].attempt, 2)
        self.assertTrue(q._connectivity_paused)

    def test_inject_off_queue_enqueues_when_worker_slot_frees(self):
        q = SearchQueue()
        stuck = DailySearchQueueItem()
        stuck.started_at = sc_now() - datetime.timedelta(hours=2)
        stuck.is_alive = MagicMock(return_value=True)
        stuck.join = MagicMock()
        q.currentItem = stuck
        started = threading.Event()
        release = threading.Event()

        def fail_probe(*args, **kwargs):
            started.set()
            self.assertTrue(release.wait(timeout=2))
            return False

        def wait_and_free(delay):
            q.currentItem = None
            return True

        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.oldbeard.connectivity.probe_connectivity", side_effect=fail_probe),
            patch.object(q, "_wait_connectivity_retry", side_effect=wait_and_free),
        ):
            q.inject_connectivity_check(stuck)
            self.assertTrue(started.wait(timeout=2))
            thread = q._off_queue_probe_thread
            self.assertIsNotNone(thread)
            release.set()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())

        retries = [item for item in q.queue if isinstance(item, ConnectivityCheckQueueItem)]
        self.assertEqual(len(retries), 1)
        self.assertEqual(retries[0].attempt, 2)
        self.assertTrue(q._connectivity_paused)

    def test_off_queue_retry_wait_stops_on_shutdown(self):
        q = SearchQueue()
        stuck = DailySearchQueueItem()
        stuck.started_at = sc_now() - datetime.timedelta(hours=2)
        stuck.is_alive = MagicMock(return_value=True)
        stuck.join = MagicMock()
        q.currentItem = stuck
        in_wait = threading.Event()

        original_wait = SearchQueue._wait_connectivity_retry

        def signal_wait(self, delay):
            in_wait.set()
            return original_wait(self, delay)

        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.oldbeard.connectivity.probe_connectivity", return_value=False),
            patch("sickchill.oldbeard.connectivity.delay_after_failure", return_value=30),
            patch.object(SearchQueue, "_wait_connectivity_retry", signal_wait),
        ):
            q.inject_connectivity_check(stuck)
            self.assertTrue(in_wait.wait(timeout=2))
            thread = q._off_queue_probe_thread
            q.stop_current_item(timeout=0)
            self.assertIsNotNone(thread)
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())

        self.assertFalse(any(isinstance(item, ConnectivityCheckQueueItem) for item in q.queue))

    def test_add_item_accepts_connectivity_check(self):
        q = SearchQueue()
        added = q.add_item(ConnectivityCheckQueueItem(q))
        self.assertIsNotNone(added)
        self.assertIsNone(q.add_item(ConnectivityCheckQueueItem(q)))


class TestRequestFailedInjectsConnectivity(unittest.TestCase):
    def test_is_connectivity_error_for_dns_and_connection(self):
        import requests
        import urllib3

        conn = requests.exceptions.ConnectionError("Max retries exceeded")
        conn.__cause__ = urllib3.exceptions.NameResolutionError("www.torrentday.com", None, OSError("Temporary failure in name resolution"))
        self.assertTrue(connectivity.is_connectivity_error(conn))
        self.assertTrue(connectivity.is_connectivity_error(socket_gaierror()))
        self.assertFalse(connectivity.is_connectivity_error(requests.exceptions.HTTPError("404")))
        self.assertFalse(connectivity.is_connectivity_error(requests.exceptions.SSLError("bad cert")))
        self.assertTrue(connectivity.is_connectivity_error(requests.exceptions.ReadTimeout("read timed out")))

    def test_handle_requests_exception_enqueues_check_once(self):
        import requests

        from sickchill.oldbeard import helpers

        q = SearchQueue()
        scheduler = MagicMock(action=q)
        err = requests.exceptions.ConnectionError(
            "HTTPSConnectionPool(host='www.torrentday.com', port=443): Failed to resolve 'www.torrentday.com' ([Errno -3] Temporary failure in name resolution)"
        )
        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.settings.searchQueueScheduler", scheduler),
            patch.object(q, "stop_current_item") as stop,
        ):
            helpers.handle_requests_exception(err)
            helpers.handle_requests_exception(err)

        checks = [item for item in q.queue if isinstance(item, ConnectivityCheckQueueItem)]
        self.assertEqual(len(checks), 1)
        self.assertTrue(q._connectivity_paused)
        self.assertEqual(q.min_priority, QueuePriorities.CONNECTIVITY)
        stop.assert_not_called()

    def test_http_error_does_not_inject(self):
        import requests

        from sickchill.oldbeard import helpers

        q = SearchQueue()
        scheduler = MagicMock(action=q)
        with patch("sickchill.settings.CONNECTIVITY_CHECK", True), patch("sickchill.settings.searchQueueScheduler", scheduler):
            helpers.handle_requests_exception(requests.exceptions.HTTPError("404 Client Error"))
        self.assertFalse(any(isinstance(item, ConnectivityCheckQueueItem) for item in q.queue))
        self.assertFalse(q._connectivity_paused)

    def test_tvdb_error_with_dns_message_is_connectivity(self):
        error = TVDBv4Error("Failed to resolve 'api4.thetvdb.com' ([Errno -3] Temporary failure in name resolution)")
        self.assertTrue(connectivity.is_connectivity_error(error))

    def test_tvdb_error_with_read_timeout_is_connectivity(self):
        error = TVDBv4Error("HTTPSConnectionPool(host='api4.thetvdb.com', port=443): Read timed out. (read timeout=21)")
        self.assertTrue(connectivity.is_connectivity_error(error))

    def test_indexer_decorator_reraises_timeout_and_pauses_show_queue(self):
        @ExceptionDecorator()
        def load_series():
            raise TVDBv4Error("HTTPSConnectionPool(host='api4.thetvdb.com', port=443): Read timed out. (read timeout=21)")

        search_q = SearchQueue()
        show_q = GenericQueue()
        show_q.queue_name = "SHOWQUEUE"
        with (
            patch("sickchill.settings.CONNECTIVITY_CHECK", True),
            patch("sickchill.settings.searchQueueScheduler", MagicMock(action=search_q)),
            patch("sickchill.settings.showQueueScheduler", MagicMock(action=show_q)),
            patch("sickchill.show.indexers.wrappers.logger") as log,
        ):
            with self.assertRaises(TVDBv4Error):
                load_series()

            self.assertEqual(len([item for item in search_q.queue if isinstance(item, ConnectivityCheckQueueItem)]), 1)
            self.assertTrue(show_q._connectivity_paused)
            self.assertEqual(show_q.min_priority, QueuePriorities.CONNECTIVITY)
            debug_text = " ".join(str(call) for call in log.debug.call_args_list)
            self.assertNotIn("probably does not have this item", debug_text)
            log.warning.assert_called()

            with patch("sickchill.oldbeard.connectivity.probe_connectivity", return_value=True):
                search_q.queue[0].run()
            self.assertFalse(show_q._connectivity_paused)
            self.assertEqual(show_q.min_priority, 0)

    def test_indexer_decorator_still_swallows_missing_item(self):
        from urllib3.exceptions import HTTPError

        @ExceptionDecorator()
        def load_series():
            raise HTTPError("404")

        self.assertEqual(load_series(), [])


def socket_gaierror():
    import socket

    return socket.gaierror(-3, "Temporary failure in name resolution")
