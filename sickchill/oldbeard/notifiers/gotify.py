"""Legacy Gotify shim — delivery lives in sickchill.plugins.notifiers.gotify."""

from __future__ import annotations

from sickchill.plugins.api import PluginKind


class Notifier(object):
    def _plugin(self):
        try:
            from sickchill.plugins.manager import plugin_manager

            return plugin_manager.instance(PluginKind.NOTIFIER, "gotify")
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

    def test_notify(self, host=None, token=None):
        plugin = self._plugin()
        if plugin is not None:
            return plugin.test_notify(host=host, token=token)
        from sickchill.plugins.api import PluginContext, PluginKind
        from sickchill.plugins.notifiers.gotify import GotifyNotifier

        ctx = PluginContext(
            kind=PluginKind.NOTIFIER,
            plugin_id="gotify",
            _data={"enabled": True, "host": host or "", "authorizationtoken": token or ""},
        )
        return GotifyNotifier(ctx).test_notify(host=host, token=token)
