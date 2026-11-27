from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class PytivoNotifier(LegacyNotifierPlugin):
    id = "pytivo"
    name = "Pytivo"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_PYTIVO"
    legacy_sections: ClassVar[tuple[str, ...]] = ("pyTivo",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_pytivo",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("pytivo_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("pytivo_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("pytivo_notify_onsubtitledownload",)),
        Field(name="host", type="str", default="", legacy_keys=("pytivo_host",)),
        Field(name="share_name", type="str", default="", legacy_keys=("pytivo_share_name",)),
        Field(name="tivo_name", type="str", default="", legacy_keys=("pytivo_tivo_name",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_PYTIVO = bool(self.ctx.get("enabled"))
        settings.PYTIVO_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.PYTIVO_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.PYTIVO_HOST = self.ctx.get("host") or ""
        settings.PYTIVO_SHARE_NAME = self.ctx.get("share_name") or ""
        settings.PYTIVO_TIVO_NAME = self.ctx.get("tivo_name") or ""
