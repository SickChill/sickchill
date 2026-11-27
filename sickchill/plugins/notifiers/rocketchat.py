from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class RocketchatNotifier(LegacyNotifierPlugin):
    id = "rocketchat"
    name = "Rocketchat"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_ROCKETCHAT"
    legacy_sections: ClassVar[tuple[str, ...]] = ("RocketChat",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_rocketchat",)),
        Field(name="notify_snatch", type="bool", default=False, legacy_keys=("rocketchat_notify_snatch",)),
        Field(name="notify_download", type="bool", default=False, legacy_keys=("rocketchat_notify_download",)),
        Field(name="notify_subtitledownload", type="bool", default=False, legacy_keys=("rocketchat_notify_subtitledownload",)),
        Field(name="webhook", type="str", default="", legacy_keys=("rocketchat_webhook",)),
        Field(name="icon_emoji", type="str", default="", legacy_keys=("rocketchat_icon_emoji",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_ROCKETCHAT = bool(self.ctx.get("enabled"))
        settings.ROCKETCHAT_NOTIFY_SNATCH = bool(self.ctx.get("notify_snatch"))
        settings.ROCKETCHAT_NOTIFY_DOWNLOAD = bool(self.ctx.get("notify_download"))
        settings.ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD = bool(self.ctx.get("notify_subtitledownload"))
        settings.ROCKETCHAT_WEBHOOK = self.ctx.get("webhook") or ""
        settings.ROCKETCHAT_ICON_EMOJI = self.ctx.get("icon_emoji") or ""
