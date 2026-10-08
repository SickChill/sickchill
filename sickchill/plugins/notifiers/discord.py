from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from sickchill.oldbeard import common
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import NotifierPlugin

if TYPE_CHECKING:
    from sickchill.logging.weblog import UIError


@register
class DiscordNotifier(NotifierPlugin):
    id = "discord"
    name = "Discord"
    version = "1.0.0"
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

    def notify_snatch(self, ep_name: str) -> None:
        if self.ctx.get("notify_snatch"):
            self._queue(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name: str) -> None:
        if self.ctx.get("notify_download"):
            self._queue(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_postprocess(self, ep_name: str) -> None:
        # Discord has no separate postprocess toggle; reuse download preference.
        if self.ctx.get("notify_download"):
            self._queue(common.notifyStrings[common.NOTIFY_POSTPROCESS] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name: str, lang: str = "") -> None:
        if self.ctx.get("notify_subtitle_download"):
            self._queue(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_update(self, new_version: str = "??") -> None:
        update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_UPDATE]
        self._queue(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress: str = "") -> None:
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._queue(title + " - " + update_text.format(ipaddress))

    def notify_logged_error(self, ui_error: UIError) -> None:
        self._queue(f"{ui_error.title} - {ui_error.message}")

    def test_notify(self, webhook: str | None = None, name: str | None = None, avatar: str | None = None, tts=None):
        from sickchill.oldbeard.notifications_queue import DiscordTask

        task = DiscordTask("This is a test notification from SickChill")
        return task._send_discord(
            webhook=webhook or self.ctx.get("webhook"),
            name=name or self.ctx.get("bot_name"),
            avatar=avatar or self.ctx.get("avatar_url"),
            tts=self.ctx.get("tts") if tts is None else tts,
        )

    def test(self) -> tuple[bool, str]:
        ok = bool(self.test_notify())
        return ok, "Discord message successful" if ok else "Discord message failed"

    def _queue(self, message: str, force: bool = False) -> bool:
        from sickchill import settings

        return bool(settings.notificationsTaskScheduler.action.add_item(message, notifier="discord", force_next=force))
