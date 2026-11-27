from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin
from sickchill.plugins.settings import decrypt_stored_password


@register
class PlexNotifier(LegacyNotifierPlugin):
    id = "plex"
    name = "Plex"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_PLEX_SERVER"
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
        settings.PLEX_SERVER_PASSWORD = decrypt_stored_password(self.ctx.get("server_password"))
        settings.USE_PLEX_CLIENT = bool(self.ctx.get("use_plex_client"))
        settings.PLEX_CLIENT_USERNAME = self.ctx.get("client_username") or ""
        settings.PLEX_CLIENT_PASSWORD = decrypt_stored_password(self.ctx.get("client_password"))
        settings.PLEX_SERVER_HTTPS = bool(self.ctx.get("server_https"))

    def test_notify(self, *args, **kwargs):
        self._sync_settings()
        previous = settings.USE_PLEX_SERVER
        settings.USE_PLEX_SERVER = True
        try:
            impl = self._impl()
            if hasattr(impl, "test_notify"):
                return impl.test_notify(*args, **kwargs)
            if hasattr(impl, "test_notify_pms"):
                if args or kwargs:
                    return impl.test_notify_pms(*args, **kwargs)
                return impl.test_notify_pms(settings.PLEX_SERVER_HOST, settings.PLEX_SERVER_USERNAME, settings.PLEX_SERVER_PASSWORD, settings.PLEX_SERVER_TOKEN)
            return False
        finally:
            settings.USE_PLEX_SERVER = previous
