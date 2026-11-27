from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class Nmjv2Notifier(LegacyNotifierPlugin):
    id = "nmjv2"
    name = "Nmjv2"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_NMJv2"
    legacy_sections: ClassVar[tuple[str, ...]] = ("NMJv2",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_nmjv2",)),
        Field(name="host", type="str", default="", legacy_keys=("nmjv2_host",)),
        Field(name="database", type="str", default="", legacy_keys=("nmjv2_database",)),
        Field(name="dbloc", type="str", default="", legacy_keys=("nmjv2_dbloc",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_NMJv2 = bool(self.ctx.get("enabled"))
        settings.NMJv2_HOST = self.ctx.get("host") or ""
        settings.NMJv2_DATABASE = self.ctx.get("database") or ""
        settings.NMJv2_DBLOC = self.ctx.get("dbloc") or ""
