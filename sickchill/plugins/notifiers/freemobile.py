from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class FreemobileNotifier(LegacyNotifierPlugin):
    id = "freemobile"
    name = "Freemobile"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_FREEMOBILE"
    legacy_sections: ClassVar[tuple[str, ...]] = ("FreeMobile",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_freemobile",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("freemobile_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("freemobile_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("freemobile_notify_onsubtitledownload",)),
        Field(name="id", type="str", default="", legacy_keys=("freemobile_id",)),
        Field(name="apikey", type="str", default="", legacy_keys=("freemobile_apikey",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_FREEMOBILE = bool(self.ctx.get("enabled"))
        settings.FREEMOBILE_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.FREEMOBILE_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.FREEMOBILE_ID = self.ctx.get("id") or ""
        settings.FREEMOBILE_APIKEY = self.ctx.get("apikey") or ""
