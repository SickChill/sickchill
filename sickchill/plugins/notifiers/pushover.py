from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class PushoverNotifier(LegacyNotifierPlugin):
    id = "pushover"
    name = "Pushover"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_PUSHOVER"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Pushover",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_pushover",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("pushover_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("pushover_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("pushover_notify_onsubtitledownload",)),
        Field(name="userkey", type="str", default="", legacy_keys=("pushover_userkey",)),
        Field(name="apikey", type="str", default="", legacy_keys=("pushover_apikey",)),
        Field(name="device", type="str", default="", legacy_keys=("pushover_device",)),
        Field(name="sound", type="str", default="", legacy_keys=("pushover_sound",)),
        Field(name="priority", type="str", default="", legacy_keys=("pushover_priority",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_PUSHOVER = bool(self.ctx.get("enabled"))
        settings.PUSHOVER_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.PUSHOVER_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.PUSHOVER_USERKEY = self.ctx.get("userkey") or ""
        settings.PUSHOVER_APIKEY = self.ctx.get("apikey") or ""
        settings.PUSHOVER_DEVICE = self.ctx.get("device") or ""
        settings.PUSHOVER_SOUND = self.ctx.get("sound") or ""
        settings.PUSHOVER_PRIORITY = self.ctx.get("priority") or ""
