from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class TelegramNotifier(LegacyNotifierPlugin):
    id = "telegram"
    name = "Telegram"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_TELEGRAM"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Telegram",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_telegram",)),
        Field(name="id", type="str", default="", required=True, legacy_keys=("telegram_id",)),
        Field(name="apikey", type="password", default="", required=True, secret=True, legacy_keys=("telegram_apikey",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("telegram_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("telegram_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("telegram_notify_onsubtitledownload",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_TELEGRAM = bool(self.ctx.get("enabled"))
        settings.TELEGRAM_ID = self.ctx.get("id") or ""
        settings.TELEGRAM_APIKEY = self.ctx.get("apikey") or ""
        settings.TELEGRAM_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.TELEGRAM_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
