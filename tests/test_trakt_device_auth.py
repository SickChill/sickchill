"""Mocked unit tests for Trakt device-code OAuth (no live Trakt API)."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from sickchill import settings
from sickchill.oldbeard.trakt_api import (
    TraktAPI,
    clear_revoked_trakt_defaults,
    trakt_credentials_configured,
    traktDeviceCodeExpiredException,
    traktDeviceCodePendingException,
    traktException,
    traktRateLimitException,
)
from sickchill.oldbeard.trakt_api.trakt import _MAX_RETRY_AFTER_SECONDS, _parse_retry_after


class TraktDeviceCodeAPITests(unittest.TestCase):
    def _api(self) -> TraktAPI:
        with patch.object(TraktAPI, "__init__", lambda self, *a, **k: None):
            api = TraktAPI()  # type: ignore[call-arg]
        api.ssl_verify = False
        api.verify = False
        api.timeout = 10
        api.headers = {}
        api.auth_url = "https://auth.trakt.tv/"
        return api

    @patch.object(TraktAPI, "traktRequest")
    def test_device_code_start_ok(self, trakt_request):
        trakt_request.return_value = {
            "device_code": "dev-1",
            "user_code": "ABCD-1234",
            "verification_url": "https://trakt.tv/activate",
            "expires_in": 600,
            "interval": 5,
        }
        api = self._api()
        payload = api.device_code_start()
        self.assertEqual(payload["device_code"], "dev-1")
        self.assertEqual(payload["user_code"], "ABCD-1234")
        trakt_request.assert_called()

    @patch.object(TraktAPI, "traktRequest")
    def test_device_code_start_invalid(self, trakt_request):
        trakt_request.return_value = {"error": "nope"}
        api = self._api()
        with self.assertRaises(traktException):
            api.device_code_start()

    @patch("sickchill.oldbeard.trakt_api.trakt._persist_tokens")
    @patch("sickchill.oldbeard.trakt_api.trakt.requests.post")
    def test_device_code_poll_authorized(self, post, _persist):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"access_token": "access", "refresh_token": "refresh"}
        post.return_value = response
        api = self._api()
        with patch("sickchill.oldbeard.trakt_api.trakt._safe_json", return_value={"access_token": "access", "refresh_token": "refresh"}):
            self.assertTrue(api.device_code_poll("dev-1"))

    @patch("sickchill.oldbeard.trakt_api.trakt.requests.post")
    def test_device_code_poll_pending(self, post):
        response = MagicMock()
        response.status_code = 400
        post.return_value = response
        api = self._api()
        with self.assertRaises(traktDeviceCodePendingException):
            api.device_code_poll("dev-1")

    @patch("sickchill.oldbeard.trakt_api.trakt.requests.post")
    def test_device_code_poll_expired_status(self, post):
        response = MagicMock()
        response.status_code = 410
        post.return_value = response
        api = self._api()
        with self.assertRaises(traktDeviceCodeExpiredException):
            api.device_code_poll("dev-1")

    @patch("sickchill.oldbeard.trakt_api.trakt.requests.post")
    def test_device_code_poll_rate_limit(self, post):
        response = MagicMock()
        response.status_code = 429
        post.return_value = response
        api = self._api()
        with self.assertRaises(traktRateLimitException):
            api.device_code_poll("dev-1")


class TraktRetryAfterClampTests(unittest.TestCase):
    def test_parse_retry_after_clamps(self):
        self.assertEqual(_parse_retry_after(None), 2.0)
        self.assertEqual(_parse_retry_after("1"), 1.0)
        self.assertEqual(_parse_retry_after("30"), 30.0)
        self.assertEqual(_parse_retry_after("999"), _MAX_RETRY_AFTER_SECONDS)
        self.assertEqual(_parse_retry_after("nope"), 2.0)


class TraktCredentialsConfigTests(unittest.TestCase):
    def tearDown(self):
        settings.TRAKT_API_KEY = ""
        settings.TRAKT_API_SECRET = ""
        settings.TRAKT_ACCESS_TOKEN = ""
        settings.TRAKT_REFRESH_TOKEN = ""

    def test_credentials_configured_requires_both(self):
        settings.TRAKT_API_KEY = ""
        settings.TRAKT_API_SECRET = ""
        self.assertFalse(trakt_credentials_configured())
        settings.TRAKT_API_KEY = "abc"
        self.assertFalse(trakt_credentials_configured())
        settings.TRAKT_API_SECRET = "def"
        self.assertTrue(trakt_credentials_configured())

    def test_clear_revoked_defaults(self):
        revoked = next(iter(settings.TRAKT_REVOKED_CLIENT_IDS))
        settings.TRAKT_API_KEY = revoked
        settings.TRAKT_API_SECRET = "dead-secret"
        settings.TRAKT_ACCESS_TOKEN = "tok"
        settings.TRAKT_REFRESH_TOKEN = "ref"
        self.assertTrue(clear_revoked_trakt_defaults())
        self.assertEqual(settings.TRAKT_API_KEY, "")
        self.assertEqual(settings.TRAKT_API_SECRET, "")
        self.assertEqual(settings.TRAKT_ACCESS_TOKEN, "")
        self.assertEqual(settings.TRAKT_REFRESH_TOKEN, "")
        self.assertFalse(clear_revoked_trakt_defaults())


class TraktHomeDeviceAuthEndpointTests(unittest.TestCase):
    """Exercise Home.start/pollTraktDeviceAuth with a mocked TraktAPI."""

    def _home(self):
        from sickchill.views.home import Home

        home = Home.__new__(Home)
        home.set_header = MagicMock()
        home.get_body_argument = MagicMock(return_value="")
        return home

    @patch("sickchill.views.home.TraktAPI")
    def test_start_success(self, trakt_cls):
        home = self._home()
        instance = trakt_cls.return_value
        instance.device_code_start.return_value = {
            "device_code": "dev-1",
            "user_code": "WXYZ-9999",
            "verification_url": "https://trakt.tv/activate",
            "expires_in": 600,
            "interval": 5,
        }
        raw = home.startTraktDeviceAuth()
        data = json.loads(raw)
        self.assertEqual(data["user_code"], "WXYZ-9999")
        self.assertEqual(data["device_code"], "dev-1")
        self.assertNotIn("error", data)

    @patch("sickchill.views.home.TraktAPI")
    def test_start_failure(self, trakt_cls):
        home = self._home()
        trakt_cls.return_value.device_code_start.side_effect = traktException("boom")
        raw = home.startTraktDeviceAuth()
        data = json.loads(raw)
        self.assertIn("error", data)

    @patch("sickchill.views.home.TraktAPI")
    def test_poll_authorized(self, trakt_cls):
        home = self._home()
        home.get_body_argument = MagicMock(return_value="dev-1")
        trakt_cls.return_value.device_code_poll.return_value = True
        data = json.loads(home.pollTraktDeviceAuth())
        self.assertEqual(data["status"], "authorized")

    @patch("sickchill.views.home.TraktAPI")
    def test_poll_pending(self, trakt_cls):
        home = self._home()
        home.get_body_argument = MagicMock(return_value="dev-1")
        trakt_cls.return_value.device_code_poll.side_effect = traktDeviceCodePendingException("wait")
        data = json.loads(home.pollTraktDeviceAuth())
        self.assertEqual(data["status"], "pending")

    @patch("sickchill.views.home.TraktAPI")
    def test_poll_expired(self, trakt_cls):
        home = self._home()
        home.get_body_argument = MagicMock(return_value="dev-1")
        trakt_cls.return_value.device_code_poll.side_effect = traktDeviceCodeExpiredException("gone")
        data = json.loads(home.pollTraktDeviceAuth())
        self.assertEqual(data["status"], "expired")

    @patch("sickchill.views.home.TraktAPI")
    def test_poll_slow_down(self, trakt_cls):
        home = self._home()
        home.get_body_argument = MagicMock(return_value="dev-1")
        trakt_cls.return_value.device_code_poll.side_effect = traktRateLimitException("slow down")
        data = json.loads(home.pollTraktDeviceAuth())
        self.assertEqual(data["status"], "slow_down")
        self.assertIn("slow down", data["message"])

    def test_poll_missing_code(self):
        home = self._home()
        home.get_body_argument = MagicMock(return_value="")
        data = json.loads(home.pollTraktDeviceAuth())
        self.assertEqual(data["status"], "error")


if __name__ == "__main__":
    unittest.main()
