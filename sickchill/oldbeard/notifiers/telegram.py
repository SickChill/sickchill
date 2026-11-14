"""Legacy Telegram shim — delivery lives in sickchill.plugins.notifiers.telegram."""

from __future__ import annotations

from sickchill.plugins.api import PluginKind


class Notifier(object):
    def _plugin(self):
        try:
            from sickchill.plugins.manager import plugin_manager

            return plugin_manager.instance(PluginKind.NOTIFIER, "telegram")
        except Exception:
            return None

    def notify_snatch(self, ep_name, title=None):
        plugin = self._plugin()
        if plugin:
            plugin.notify_snatch(ep_name) if title is None else plugin.notify_snatch(ep_name, title)

    def notify_download(self, ep_name, title=None):
        plugin = self._plugin()
        if plugin:
            plugin.notify_download(ep_name) if title is None else plugin.notify_download(ep_name, title)

    def notify_subtitle_download(self, ep_name, lang, title=None):
        plugin = self._plugin()
        if plugin:
            if title is None:
                plugin.notify_subtitle_download(ep_name, lang)
            else:
                plugin.notify_subtitle_download(ep_name, lang, title)

    def notify_update(self, new_version="??"):
        plugin = self._plugin()
        if plugin:
            plugin.notify_update(new_version)

    def notify_login(self, ipaddress=""):
        plugin = self._plugin()
        if plugin:
            plugin.notify_login(ipaddress)

    def test_notify(self, id=None, api_key=None):
        plugin = self._plugin()
        if plugin is not None:
            return plugin.test_notify(id=id, api_key=api_key)
        # Force path for UI test when plugin disabled: build ephemeral send via plugin class helpers
        from sickchill.plugins.api import PluginContext, PluginKind
        from sickchill.plugins.notifiers.telegram import TelegramNotifier

        ctx = PluginContext(
            kind=PluginKind.NOTIFIER,
            plugin_id="telegram",
            _data={"enabled": True, "id": id or "", "apikey": api_key or ""},
        )
        return TelegramNotifier(ctx).test_notify(id=id, api_key=api_key)
