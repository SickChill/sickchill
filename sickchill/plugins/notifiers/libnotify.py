from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class LibnotifyNotifier(LegacyNotifierPlugin):
    id = "libnotify"
    name = "Libnotify"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_LIBNOTIFY"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Libnotify",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_libnotify",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("libnotify_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("libnotify_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("libnotify_notify_onsubtitledownload",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_LIBNOTIFY = bool(self.ctx.get("enabled"))
        settings.LIBNOTIFY_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.LIBNOTIFY_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
