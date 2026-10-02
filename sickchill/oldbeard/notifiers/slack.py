"""Legacy Slack shim — delivery lives in sickchill.plugins.notifiers.slack."""

from __future__ import annotations

from sickchill.plugins.api import PluginKind


class Notifier(object):
    def _plugin(self):
        try:
            from sickchill.plugins.manager import plugin_manager

            return plugin_manager.instance(PluginKind.NOTIFIER, "slack")
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

    def test_notify(self):
        plugin = self._plugin()
        if plugin is not None:
            return plugin.test_notify()
        from sickchill import settings
        from sickchill.plugins.api import PluginContext, PluginKind
        from sickchill.plugins.notifiers.slack import SlackNotifier

        ctx = PluginContext(
            kind=PluginKind.NOTIFIER,
            plugin_id="slack",
            _data={
                "enabled": True,
                "webhook": settings.SLACK_WEBHOOK or "",
                "icon_emoji": settings.SLACK_ICON_EMOJI or "",
            },
        )
        return SlackNotifier(ctx).test_notify()
