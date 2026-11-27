from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class SlackNotifier(LegacyNotifierPlugin):
    id = "slack"
    name = "Slack"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_SLACK"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Slack",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_slack",)),
        Field(name="webhook", type="url", default="", required=True, legacy_keys=("slack_webhook",)),
        Field(name="icon_emoji", type="str", default="", legacy_keys=("slack_icon_emoji",)),
        Field(name="notify_snatch", type="bool", default=False, legacy_keys=("slack_notify_snatch",)),
        Field(name="notify_download", type="bool", default=False, legacy_keys=("slack_notify_download",)),
        Field(name="notify_subtitledownload", type="bool", default=False, legacy_keys=("slack_notify_subtitledownload",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_SLACK = bool(self.ctx.get("enabled"))
        settings.SLACK_WEBHOOK = self.ctx.get("webhook") or ""
        settings.SLACK_ICON_EMOJI = self.ctx.get("icon_emoji") or ""
        settings.SLACK_NOTIFY_SNATCH = bool(self.ctx.get("notify_snatch"))
        settings.SLACK_NOTIFY_DOWNLOAD = bool(self.ctx.get("notify_download"))
        settings.SLACK_NOTIFY_SUBTITLEDOWNLOAD = bool(self.ctx.get("notify_subtitledownload"))
