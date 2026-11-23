"""Kodi HTTP JSON-RPC helper used by the Kodi notifier."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import requests

from sickchill.oldbeard.kodi_jsonrpc import KodiClient, KodiRPCError
from sickchill.oldbeard.notifiers.kodi import Notifier


class TestKodiClient(unittest.TestCase):
    def test_call_posts_jsonrpc_envelope(self):
        client = KodiClient("192.168.1.9", username="kodi", password="secret", port=8081)
        mock_response = MagicMock()
        mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": "OK"}
        mock_response.raise_for_status = MagicMock()
        with patch.object(client._session, "post", return_value=mock_response) as post:
            result = client.GUI.ShowNotification(title="T", message="M", image="http://logo")

        self.assertEqual(result["result"], "OK")
        args, kwargs = post.call_args
        self.assertEqual(args[0], "http://192.168.1.9:8081/jsonrpc")
        payload = kwargs["json"]
        self.assertEqual(payload["jsonrpc"], "2.0")
        self.assertEqual(payload["method"], "GUI.ShowNotification")
        self.assertEqual(payload["params"], {"title": "T", "message": "M", "image": "http://logo"})
        self.assertEqual(client._session.auth, ("kodi", "secret"))

    def test_scan_omits_empty_params(self):
        client = KodiClient("kodi.local")
        mock_response = MagicMock()
        mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": "OK"}
        mock_response.raise_for_status = MagicMock()
        with patch.object(client._session, "post", return_value=mock_response) as post:
            client.VideoLibrary.Scan()
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["method"], "VideoLibrary.Scan")
        self.assertNotIn("params", payload)

    def test_non_object_json_becomes_kodi_rpc_error(self):
        client = KodiClient("192.168.1.9")
        mock_response = MagicMock()
        mock_response.json.return_value = ["pong"]
        mock_response.raise_for_status = MagicMock()
        with patch.object(client._session, "post", return_value=mock_response):
            with self.assertRaises(KodiRPCError):
                client.ping()

    def test_jsonrpc_error_becomes_kodi_rpc_error(self):
        client = KodiClient("192.168.1.9")
        mock_response = MagicMock()
        mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}
        mock_response.raise_for_status = MagicMock()
        with patch.object(client._session, "post", return_value=mock_response):
            with self.assertRaises(KodiRPCError):
                client.ping()

    def test_timeout_becomes_kodi_rpc_error(self):
        client = KodiClient("192.168.1.9")
        with patch.object(client._session, "post", side_effect=requests.Timeout("timed out")):
            with self.assertRaises(KodiRPCError):
                client.ping()


class TestKodiNotifierSetup(unittest.TestCase):
    def test_setup_pings_and_keeps_reachable_host(self):
        notifier = Notifier()
        with patch("sickchill.oldbeard.notifiers.kodi.settings") as kodi_settings:
            kodi_settings.KODI_HOST = "box.lan:9090"
            kodi_settings.KODI_USERNAME = "kodi"
            kodi_settings.KODI_PASSWORD = "pw"
            with patch("sickchill.oldbeard.notifiers.kodi.KodiClient") as client_cls:
                instance = MagicMock()
                instance.host = "box.lan"
                instance.Settings.GetSettingValue.return_value = {"result": {"value": "Living Room"}}
                client_cls.return_value = instance
                notifier.setup()

        client_cls.assert_called_once_with("box.lan", "kodi", "pw", port=9090)
        instance.ping.assert_called_once()
        self.assertEqual(notifier.connections, [instance])
        self.assertEqual(instance.name, "Living Room")

    def test_setup_skips_host_when_ping_fails(self):
        notifier = Notifier()
        with patch("sickchill.oldbeard.notifiers.kodi.settings") as kodi_settings:
            kodi_settings.KODI_HOST = "dead.lan"
            kodi_settings.KODI_USERNAME = ""
            kodi_settings.KODI_PASSWORD = ""
            with patch("sickchill.oldbeard.notifiers.kodi.KodiClient") as client_cls:
                instance = MagicMock()
                instance.ping.side_effect = KodiRPCError("down")
                client_cls.return_value = instance
                notifier.setup()

        self.assertEqual(notifier.connections, [])
