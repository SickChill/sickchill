from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class GotifyNotifier(LegacyNotifierPlugin):
    id = "gotify"
    name = "Gotify"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_GOTIFY"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Gotify",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_gotify",)),
        Field(name="host", type="url", default="", required=True, legacy_keys=("gotify_host",)),
        Field(name="authorizationtoken", type="password", default="", required=True, secret=True, legacy_keys=("gotify_authorizationtoken",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("gotify_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("gotify_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("gotify_notify_onsubtitledownload",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_GOTIFY = bool(self.ctx.get("enabled"))
        settings.GOTIFY_HOST = self.ctx.get("host") or ""
        settings.GOTIFY_AUTHORIZATIONTOKEN = self.ctx.get("authorizationtoken") or ""
        settings.GOTIFY_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.GOTIFY_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.GOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
