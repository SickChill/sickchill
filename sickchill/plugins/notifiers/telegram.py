from __future__ import annotations

from typing import ClassVar

from sickchill.oldbeard.common import (
    NOTIFY_DOWNLOAD,
    NOTIFY_LOGIN,
    NOTIFY_LOGIN_TEXT,
    NOTIFY_SNATCH,
    NOTIFY_SUBTITLE_DOWNLOAD,
    NOTIFY_UPDATE,
    NOTIFY_UPDATE_TEXT,
    notifyStrings,
)
from sickchill.oldbeard.helpers import getURL, make_session
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import NotifierPlugin


@register
class TelegramNotifier(NotifierPlugin):
    id = "telegram"
    name = "Telegram"
    version = "1.0.0"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Telegram",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_telegram",)),
        Field(name="id", type="str", default="", required=True, legacy_keys=("telegram_id",)),
        Field(name="apikey", type="password", default="", required=True, secret=True, legacy_keys=("telegram_apikey",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("telegram_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("telegram_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("telegram_notify_onsubtitledownload",)),
    )

    def __init__(self, ctx):
        super().__init__(ctx)
        self.session = make_session()

    def notify_snatch(self, ep_name: str, title=notifyStrings[NOTIFY_SNATCH]) -> None:
        if self.ctx.get("notify_onsnatch"):
            self._notify(title, ep_name)

    def notify_download(self, ep_name: str, title=notifyStrings[NOTIFY_DOWNLOAD]) -> None:
        if self.ctx.get("notify_ondownload"):
            self._notify(title, ep_name)

    def notify_postprocess(self, ep_name: str) -> None:
        if self.ctx.get("notify_ondownload"):
            self._notify(notifyStrings[NOTIFY_DOWNLOAD], ep_name)

    def notify_subtitle_download(self, ep_name: str, lang: str = "", title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]) -> None:
        if self.ctx.get("notify_onsubtitledownload"):
            self._notify(title, f"{ep_name}: {lang}")

    def notify_update(self, new_version: str = "??") -> None:
        self._notify(notifyStrings[NOTIFY_UPDATE], notifyStrings[NOTIFY_UPDATE_TEXT] + new_version)

    def notify_login(self, ipaddress: str = "") -> None:
        self._notify(notifyStrings[NOTIFY_LOGIN], notifyStrings[NOTIFY_LOGIN_TEXT].format(ipaddress))

    def test_notify(self, id=None, api_key=None):
        return self._notify("Test", "This is a test notification from SickChill", id=id, api_key=api_key, force=True)

    def test(self) -> tuple[bool, str]:
        ok, message = self.test_notify()
        return bool(ok), str(message)

    def _notify(self, title, message, id=None, api_key=None, force=False):
        if not (force or self.ctx.get("enabled")):
            self.ctx.logger.debug("Notification for Telegram not enabled, skipping this notification")
            return False, "Disabled"
        chat_id = id or self.ctx.get("id")
        token = api_key or self.ctx.get("apikey")
        self.ctx.logger.debug("Sending a Telegram message for %s", message)
        params = {"chat_id": chat_id, "text": f"{title} : {message}"}
        response = getURL(
            f"https://api.telegram.org/bot{token}/sendMessage",
            params=params,
            session=self.session,
            returns="json",
        )
        result_message = ("Sending Telegram message failed, check the log", "Telegram message sent successfully.")[bool(response)]
        self.ctx.logger.info(result_message)
        return bool(response), result_message
