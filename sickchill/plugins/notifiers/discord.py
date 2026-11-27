from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class DiscordNotifier(LegacyNotifierPlugin):
    id = "discord"
    name = "Discord"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_DISCORD"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Discord",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_discord", "enabled")),
        Field(name="webhook", type="url", default="", required=True, legacy_keys=("discord_webhook", "webhook")),
        Field(name="bot_name", type="str", default="SickChill", legacy_keys=("discord_name", "name")),
        Field(
            name="avatar_url",
            type="url",
            default="https://raw.githubusercontent.com/SickChill/SickChill/master/sickchill/gui/slick/images/sickchill-sc.png",
            legacy_keys=("discord_avatar_url", "avatar_url"),
        ),
        Field(name="tts", type="bool", default=False, legacy_keys=("discord_tts", "tts")),
        Field(name="notify_snatch", type="bool", default=False, legacy_keys=("discord_notify_snatch",)),
        Field(name="notify_download", type="bool", default=False, legacy_keys=("discord_notify_download",)),
        Field(
            name="notify_subtitle_download",
            type="bool",
            default=False,
            legacy_keys=("discord_notify_subtitledownload", "notify_subtitledownload"),
        ),
    )

    def _sync_settings(self) -> None:
        settings.USE_DISCORD = bool(self.ctx.get("enabled"))
        settings.DISCORD_WEBHOOK = self.ctx.get("webhook") or ""
        settings.DISCORD_NAME = self.ctx.get("bot_name") or "SickChill"
        settings.DISCORD_AVATAR_URL = self.ctx.get("avatar_url") or ""
        settings.DISCORD_TTS = bool(self.ctx.get("tts"))
        settings.DISCORD_NOTIFY_SNATCH = bool(self.ctx.get("notify_snatch"))
        settings.DISCORD_NOTIFY_DOWNLOAD = bool(self.ctx.get("notify_download"))
        settings.DISCORD_NOTIFY_SUBTITLEDOWNLOAD = bool(self.ctx.get("notify_subtitle_download"))

    def test(self) -> tuple[bool, str]:
        ok = bool(self.test_notify())
        return ok, "Discord message successful" if ok else "Discord message failed"
