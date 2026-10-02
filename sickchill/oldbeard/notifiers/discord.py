"""Legacy Discord notifier shim — delivery lives in sickchill.plugins.notifiers.discord."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sickchill.plugins.api import PluginKind

if TYPE_CHECKING:
    from sickchill.logging.weblog import UIError


class Notifier(object):
    """Thin shim for UI testDiscord; prefer NotifierPlugin broadcast paths."""

    def _plugin(self):
        try:
            from sickchill.plugins.manager import plugin_manager

            return plugin_manager.instance(PluginKind.NOTIFIER, "discord")
        except Exception:
            return None

    def notify_snatch(self, ep_name):
        plugin = self._plugin()
        if plugin:
            plugin.notify_snatch(ep_name)

    def notify_download(self, ep_name):
        plugin = self._plugin()
        if plugin:
            plugin.notify_download(ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        plugin = self._plugin()
        if plugin:
            plugin.notify_subtitle_download(ep_name, lang)

    def notify_update(self, new_version="??"):
        plugin = self._plugin()
        if plugin:
            plugin.notify_update(new_version)

    def notify_login(self, ipaddress=""):
        plugin = self._plugin()
        if plugin:
            plugin.notify_login(ipaddress)

    def notify_logged_error(self, ui_error: "UIError"):
        plugin = self._plugin()
        if plugin:
            plugin.notify_logged_error(ui_error)

    def test_notify(self, webhook: str | None = None, name: str | None = None, avatar: str | None = None, tts=None):
        plugin = self._plugin()
        if plugin is not None:
            return plugin.test_notify(webhook=webhook, name=name, avatar=avatar, tts=tts)
        from sickchill.oldbeard.notifications_queue import DiscordTask

        task = DiscordTask("This is a test notification from SickChill")
        return task._send_discord(webhook=webhook, name=name, avatar=avatar, tts=tts)
