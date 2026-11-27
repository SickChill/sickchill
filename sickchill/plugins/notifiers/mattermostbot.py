from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class MattermostbotNotifier(LegacyNotifierPlugin):
    id = "mattermostbot"
    name = "Mattermostbot"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_MATTERMOSTBOT"
    legacy_sections: ClassVar[tuple[str, ...]] = ("MattermostBot",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_mattermostbot",)),
        Field(name="notify_snatch", type="bool", default=False, legacy_keys=("mattermostbot_notify_snatch",)),
        Field(name="notify_download", type="bool", default=False, legacy_keys=("mattermostbot_notify_download",)),
        Field(name="notify_subtitledownload", type="bool", default=False, legacy_keys=("mattermostbot_notify_subtitledownload",)),
        Field(name="token", type="str", default="", legacy_keys=("mattermostbot_token",)),
        Field(name="channel", type="str", default="", legacy_keys=("mattermostbot_channel",)),
        Field(name="url", type="str", default="", legacy_keys=("mattermostbot_url",)),
        Field(name="icon_emoji", type="str", default="", legacy_keys=("mattermostbot_icon_emoji",)),
        Field(name="author", type="str", default="", legacy_keys=("mattermostbot_author",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_MATTERMOSTBOT = bool(self.ctx.get("enabled"))
        settings.MATTERMOSTBOT_NOTIFY_SNATCH = bool(self.ctx.get("notify_snatch"))
        settings.MATTERMOSTBOT_NOTIFY_DOWNLOAD = bool(self.ctx.get("notify_download"))
        settings.MATTERMOSTBOT_NOTIFY_SUBTITLEDOWNLOAD = bool(self.ctx.get("notify_subtitledownload"))
        settings.MATTERMOSTBOT_TOKEN = self.ctx.get("token") or ""
        settings.MATTERMOSTBOT_CHANNEL = self.ctx.get("channel") or ""
        settings.MATTERMOSTBOT_URL = self.ctx.get("url") or ""
        settings.MATTERMOSTBOT_ICON_EMOJI = self.ctx.get("icon_emoji") or ""
        settings.MATTERMOSTBOT_AUTHOR = self.ctx.get("author") or ""
