from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class JoinNotifier(LegacyNotifierPlugin):
    id = "join"
    name = "Join"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_JOIN"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Join",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_join",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("join_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("join_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("join_notify_onsubtitledownload",)),
        Field(name="id", type="str", default="", legacy_keys=("join_id",)),
        Field(name="apikey", type="str", default="", legacy_keys=("join_apikey",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_JOIN = bool(self.ctx.get("enabled"))
        settings.JOIN_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.JOIN_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.JOIN_ID = self.ctx.get("id") or ""
        settings.JOIN_APIKEY = self.ctx.get("apikey") or ""
