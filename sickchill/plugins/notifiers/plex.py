from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import NotifierPlugin


@register
class PlexNotifier(NotifierPlugin):
    id = "plex"
    name = "Plex"
    version = "1.0.0"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Plex",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="use_plex_server", type="bool", default=False, legacy_keys=("use_plex_server",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("plex_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("plex_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("plex_notify_onsubtitledownload",)),
        Field(name="update_library", type="bool", default=False, legacy_keys=("plex_update_library",)),
        Field(name="server_host", type="str", default="", legacy_keys=("plex_server_host",)),
        Field(name="server_token", type="str", default="", legacy_keys=("plex_server_token",)),
        Field(name="client_host", type="str", default="", legacy_keys=("plex_client_host",)),
        Field(name="server_username", type="str", default="", legacy_keys=("plex_server_username",)),
        Field(name="server_password", type="str", default="", legacy_keys=("plex_server_password",)),
        Field(name="use_plex_client", type="bool", default=False, legacy_keys=("use_plex_client",)),
        Field(name="client_username", type="str", default="", legacy_keys=("plex_client_username",)),
        Field(name="client_password", type="str", default="", legacy_keys=("plex_client_password",)),
        Field(name="server_https", type="bool", default=False, legacy_keys=("plex_server_https",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_PLEX_SERVER = bool(self.ctx.get("use_plex_server"))
        settings.PLEX_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.PLEX_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.PLEX_UPDATE_LIBRARY = bool(self.ctx.get("update_library"))
        settings.PLEX_SERVER_HOST = self.ctx.get("server_host") or ""
        settings.PLEX_SERVER_TOKEN = self.ctx.get("server_token") or ""
        settings.PLEX_CLIENT_HOST = self.ctx.get("client_host") or ""
        settings.PLEX_SERVER_USERNAME = self.ctx.get("server_username") or ""
        settings.PLEX_SERVER_PASSWORD = self.ctx.get("server_password") or ""
        settings.USE_PLEX_CLIENT = bool(self.ctx.get("use_plex_client"))
        settings.PLEX_CLIENT_USERNAME = self.ctx.get("client_username") or ""
        settings.PLEX_CLIENT_PASSWORD = self.ctx.get("client_password") or ""
        settings.PLEX_SERVER_HTTPS = bool(self.ctx.get("server_https"))

    def _impl(self):
        from sickchill.oldbeard.notifiers import plex as _mod

        return _mod.Notifier()

    def notify_snatch(self, ep_name, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_snatch"):
            return impl.notify_snatch(ep_name, *args, **kwargs)
        return None

    def notify_download(self, ep_name, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_download"):
            return impl.notify_download(ep_name, *args, **kwargs)
        return None

    def notify_postprocess(self, ep_name, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_postprocess"):
            return impl.notify_postprocess(ep_name, *args, **kwargs)
        return None

    def notify_subtitle_download(self, ep_name, lang="", *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_subtitle_download"):
            return impl.notify_subtitle_download(ep_name, lang, *args, **kwargs)
        return None

    def notify_update(self, new_version="??", *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_update"):
            return impl.notify_update(new_version, *args, **kwargs)
        return None

    def notify_login(self, ipaddress="", *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_login"):
            return impl.notify_login(ipaddress, *args, **kwargs)
        return None

    def notify_logged_error(self, ui_error, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_logged_error"):
            return impl.notify_logged_error(ui_error, *args, **kwargs)
        return None

    def test_notify(self, *args, **kwargs):
        self._sync_settings()
        previous = settings.USE_PLEX_SERVER
        settings.USE_PLEX_SERVER = True
        try:
            impl = self._impl()
            if hasattr(impl, "test_notify"):
                return impl.test_notify(*args, **kwargs)
            if hasattr(impl, "test_notify_pms"):
                return impl.test_notify_pms(*args, **kwargs)
            return False
        finally:
            settings.USE_PLEX_SERVER = previous

    def test(self):
        result = self.test_notify()
        if isinstance(result, tuple):
            return bool(result[0]), str(result[1] if len(result) > 1 else result[0])
        return bool(result), "ok" if result else "failed"

    def update_library(self, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "update_library"):
            return impl.update_library(*args, **kwargs)
        return None

    def __getattr__(self, name):
        # Forward library helpers (addFolder, update_watchlist, play_episode, ...)
        if name.startswith("_"):
            raise AttributeError(name)
        self._sync_settings()
        impl = self._impl()
        return getattr(impl, name)
