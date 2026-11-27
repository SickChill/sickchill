from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class PushbulletNotifier(LegacyNotifierPlugin):
    id = "pushbullet"
    name = "Pushbullet"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_PUSHBULLET"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Pushbullet",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_pushbullet",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("pushbullet_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("pushbullet_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("pushbullet_notify_onsubtitledownload",)),
        Field(name="api", type="str", default="", legacy_keys=("pushbullet_api",)),
        Field(name="device", type="str", default="", legacy_keys=("pushbullet_device",)),
        Field(name="channel", type="str", default="", legacy_keys=("pushbullet_channel",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_PUSHBULLET = bool(self.ctx.get("enabled"))
        settings.PUSHBULLET_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.PUSHBULLET_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.PUSHBULLET_API = self.ctx.get("api") or ""
        settings.PUSHBULLET_DEVICE = self.ctx.get("device") or ""
        settings.PUSHBULLET_CHANNEL = self.ctx.get("channel") or ""
