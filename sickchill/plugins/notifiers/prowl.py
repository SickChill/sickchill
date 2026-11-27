from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class ProwlNotifier(LegacyNotifierPlugin):
    id = "prowl"
    name = "Prowl"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_PROWL"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Prowl",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_prowl",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("prowl_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("prowl_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("prowl_notify_onsubtitledownload",)),
        Field(name="api", type="str", default="", legacy_keys=("prowl_api",)),
        Field(name="priority", type="str", default="", legacy_keys=("prowl_priority",)),
        Field(name="message_title", type="str", default="", legacy_keys=("prowl_message_title",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_PROWL = bool(self.ctx.get("enabled"))
        settings.PROWL_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.PROWL_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.PROWL_API = self.ctx.get("api") or ""
        settings.PROWL_PRIORITY = self.ctx.get("priority") or ""
        settings.PROWL_MESSAGE_TITLE = self.ctx.get("message_title") or ""
