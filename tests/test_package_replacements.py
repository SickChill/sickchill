"""Coverage for the small stdlib/requests replacements of former PyPI deps."""

from __future__ import annotations

import datetime
import unittest
from unittest.mock import MagicMock, patch

import requests

from sickchill.helper.common import valid_url
from sickchill.oldbeard.notifiers.tweet import Notifier as TwitterNotifier
from sickchill.oldbeard.providers.btn import Provider as BTNProvider
from sickchill.oldbeard.scdatetime import _format_timeago, sctimeago


class ValidUrlTests(unittest.TestCase):
    def test_http_https(self):
        self.assertTrue(valid_url("https://example.com/path"))
        self.assertTrue(valid_url("http://jackett:9117/api"))
        self.assertTrue(valid_url("http://localhost:8081"))

    def test_rejects_non_http(self):
        self.assertFalse(valid_url(""))
        self.assertFalse(valid_url(None))
        self.assertFalse(valid_url("not a url"))
        self.assertFalse(valid_url("magnet:?xt=urn:btih:abc"))
        self.assertFalse(valid_url("ftp://example.com/file"))


class TimeagoTests(unittest.TestCase):
    def test_format_matches_previous_package(self):
        self.assertEqual(_format_timeago(datetime.timedelta(seconds=3)), "just now")
        self.assertEqual(_format_timeago(datetime.timedelta(seconds=12)), "12 seconds ago")
        self.assertEqual(_format_timeago(datetime.timedelta(minutes=1)), "1 minute ago")
        self.assertEqual(_format_timeago(datetime.timedelta(hours=3)), "3 hours ago")
        self.assertEqual(_format_timeago(datetime.timedelta(hours=-2)), "in 2 hours")

    def test_timedelta_is_treated_as_offset_from_now(self):
        text = sctimeago(datetime.timedelta(hours=2))
        self.assertTrue(text.startswith("in "))


class BtnJsonRpcTests(unittest.TestCase):
    def test_get_torrents_positional_params(self):
        provider = BTNProvider()
        provider.api_key = "secret-key"
        mock_response = MagicMock()
        mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": {"torrents": {}, "results": 0}}
        mock_response.raise_for_status = MagicMock()
        with patch("sickchill.oldbeard.providers.btn.requests.post", return_value=mock_response) as post:
            with patch("sickchill.oldbeard.providers.btn.time.sleep"):
                data = provider._api_call({"series": "Show"}, 1000, 0)

        self.assertEqual(data, {"torrents": {}, "results": 0})
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["method"], "getTorrents")
        self.assertEqual(payload["params"], ["secret-key", {"series": "Show"}, 1000, 0])
        self.assertEqual(post.call_args.args[0], "https://api.broadcasthe.net")

    def test_invalid_api_key_becomes_api_error(self):
        provider = BTNProvider()
        provider.api_key = "bad"
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": {"code": -32001, "message": "Invalid API Key"}}
        mock_response.raise_for_status = MagicMock()
        with patch("sickchill.oldbeard.providers.btn.requests.post", return_value=mock_response):
            data = provider._api_call()
        self.assertIn("api-error", data)


class TwitterNotifierTests(unittest.TestCase):
    def test_send_tweet_posts_status(self):
        notifier = TwitterNotifier()
        session = MagicMock()
        response = MagicMock()
        session.post.return_value = response
        with patch.object(notifier, "_api_session", return_value=session):
            self.assertTrue(notifier._send_tweet("hello from sickchill"))
        session.post.assert_called_once()
        args, kwargs = session.post.call_args
        self.assertEqual(args[0], "https://api.x.com/1.1/statuses/update.json")
        self.assertEqual(kwargs["data"]["status"], "hello from sickchill")
        response.raise_for_status.assert_called_once()

    def test_send_tweet_timeout(self):
        notifier = TwitterNotifier()
        session = MagicMock()
        session.post.side_effect = requests.Timeout("nope")
        with patch.object(notifier, "_api_session", return_value=session):
            self.assertFalse(notifier._send_tweet("hello"))
