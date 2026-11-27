from __future__ import annotations

from typing import TYPE_CHECKING

from sickchill import common, settings

if TYPE_CHECKING:
    from sickchill.logging.weblog import UIError


class Notifier(object):
    def notify_snatch(self, ep_name):
        if settings.DISCORD_NOTIFY_SNATCH:
            self._queue(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name):
        if settings.DISCORD_NOTIFY_DOWNLOAD:
            self._queue(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_postprocess(self, ep_name):
        if settings.DISCORD_NOTIFY_DOWNLOAD:
            self._queue(common.notifyStrings[common.NOTIFY_POSTPROCESS] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name, lang=""):
        if settings.DISCORD_NOTIFY_SUBTITLEDOWNLOAD:
            self._queue(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_update(self, new_version="??"):
        update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_UPDATE]
        self._queue(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._queue(title + " - " + update_text.format(ipaddress))

    def notify_logged_error(self, ui_error: UIError):
        self._queue(f"{ui_error.title} - {ui_error.message}")

    def test_notify(self, webhook: str | None = None, name: str | None = None, avatar: str | None = None, tts=None):
        from sickchill.notifiers.notifications_queue import DiscordTask

        task = DiscordTask("This is a test notification from SickChill")
        return task._send_discord(
            webhook=webhook or settings.DISCORD_WEBHOOK,
            name=name or settings.DISCORD_NAME,
            avatar=avatar or settings.DISCORD_AVATAR_URL,
            tts=settings.DISCORD_TTS if tts is None else tts,
        )

    def _queue(self, message: str, force: bool = False) -> bool:
        return bool(settings.notificationsTaskScheduler.action.add_item(message, notifier="discord", force_next=force))
