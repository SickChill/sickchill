from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class NmjNotifier(LegacyNotifierPlugin):
    id = "nmj"
    name = "Nmj"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_NMJ"
    legacy_sections: ClassVar[tuple[str, ...]] = ("NMJ",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_nmj",)),
        Field(name="host", type="str", default="", legacy_keys=("nmj_host",)),
        Field(name="database", type="str", default="", legacy_keys=("nmj_database",)),
        Field(name="mount", type="str", default="", legacy_keys=("nmj_mount",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_NMJ = bool(self.ctx.get("enabled"))
        settings.NMJ_HOST = self.ctx.get("host") or ""
        settings.NMJ_DATABASE = self.ctx.get("database") or ""
        settings.NMJ_MOUNT = self.ctx.get("mount") or ""
