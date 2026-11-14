from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.plugins.api import PluginKind, clear_registry, register
from sickchill.plugins.manager import PluginManager
from sickchill.plugins.settings import migrate_legacy_sections, read_notifier_section


class WebhookNotifierBatchTests(unittest.TestCase):
    def setUp(self):
        clear_registry()
        from sickchill.plugins.notifiers import gotify, slack, telegram

        self.classes = [slack.SlackNotifier, telegram.TelegramNotifier, gotify.GotifyNotifier]
        for cls in self.classes:
            register(cls)
        self.manager = PluginManager()

    def tearDown(self):
        clear_registry()

    def test_plugins_register_and_migrate(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["Slack"] = {"use_slack": "1", "slack_webhook": "https://hooks.slack.com/services/T/B/X", "slack_notify_download": "1"}
        cfg["Telegram"] = {"use_telegram": "1", "telegram_id": "123", "telegram_apikey": "tok", "telegram_notify_onsnatch": "1"}
        cfg["Gotify"] = {"use_gotify": "1", "gotify_host": "http://gotify.local/", "gotify_authorizationtoken": "tok"}

        self.assertTrue(migrate_legacy_sections(cfg, self.classes))
        for section in ("Slack", "Telegram", "Gotify"):
            self.assertNotIn(section, cfg)
        self.assertNotIn("extensions", cfg)

        self.manager._cfg = cfg
        self.manager.discover()
        enabled = {p.id for p in self.manager.enabled(PluginKind.NOTIFIER)}
        self.assertEqual(enabled, {"slack", "telegram", "gotify"})

        slack = read_notifier_section(cfg, "slack")
        self.assertIn("hooks.slack.com", slack.get("webhook", ""))
        telegram = read_notifier_section(cfg, "telegram")
        self.assertEqual(telegram.get("id"), "123")
        gotify = read_notifier_section(cfg, "gotify")
        self.assertEqual(gotify.get("host"), "http://gotify.local/")

    def test_all_first_party_notifiers_load(self):
        from sickchill.plugins.api import clear_registry, registered_classes
        from sickchill.plugins.notifiers import load_first_party_notifiers

        clear_registry()
        load_first_party_notifiers()
        ids = {cls.id for cls in registered_classes()}
        for required in (
            "discord",
            "slack",
            "telegram",
            "gotify",
            "join",
            "kodi",
            "plex",
            "emby",
            "jellyfin",
            "trakt",
            "email",
            "pushbullet",
            "pushover",
        ):
            self.assertIn(required, ids)
        self.assertGreaterEqual(len(ids), 25)
