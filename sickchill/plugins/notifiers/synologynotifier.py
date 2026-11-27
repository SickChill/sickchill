from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class SynologynotifierNotifier(LegacyNotifierPlugin):
    id = "synologynotifier"
    name = "Synologynotifier"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_SYNOLOGYNOTIFIER"
    legacy_sections: ClassVar[tuple[str, ...]] = ("SynologyNotifier",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_synologynotifier",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("synologynotifier_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("synologynotifier_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("synologynotifier_notify_onsubtitledownload",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_SYNOLOGYNOTIFIER = bool(self.ctx.get("enabled"))
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
