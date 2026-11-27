from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class MattermostNotifier(LegacyNotifierPlugin):
    id = "mattermost"
    name = "Mattermost"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_MATTERMOST"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Mattermost",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_mattermost",)),
        Field(name="notify_snatch", type="bool", default=False, legacy_keys=("mattermost_notify_snatch",)),
        Field(name="notify_download", type="bool", default=False, legacy_keys=("mattermost_notify_download",)),
        Field(name="notify_subtitledownload", type="bool", default=False, legacy_keys=("mattermost_notify_subtitledownload",)),
        Field(name="username", type="str", default="", legacy_keys=("mattermost_username",)),
        Field(name="webhook", type="str", default="", legacy_keys=("mattermost_webhook",)),
        Field(name="icon_emoji", type="str", default="", legacy_keys=("mattermost_icon_emoji",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_MATTERMOST = bool(self.ctx.get("enabled"))
        settings.MATTERMOST_NOTIFY_SNATCH = bool(self.ctx.get("notify_snatch"))
        settings.MATTERMOST_NOTIFY_DOWNLOAD = bool(self.ctx.get("notify_download"))
        settings.MATTERMOST_NOTIFY_SUBTITLEDOWNLOAD = bool(self.ctx.get("notify_subtitledownload"))
        settings.MATTERMOST_USERNAME = self.ctx.get("username") or ""
        settings.MATTERMOST_WEBHOOK = self.ctx.get("webhook") or ""
        settings.MATTERMOST_ICON_EMOJI = self.ctx.get("icon_emoji") or ""
