from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class SynoindexNotifier(LegacyNotifierPlugin):
    id = "synoindex"
    name = "Synoindex"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_SYNOINDEX"
    # Do not list "Synology" here — migrate_legacy_sections would delete the whole
    # shared section. SYNOINDEX_MAP (delete_section=False) handles use_synoindex.
    legacy_sections: ClassVar[tuple[str, ...]] = ()
    schema: ClassVar[tuple[Field, ...]] = (Field(name="enabled", type="bool", default=False, legacy_keys=("use_synoindex",)),)

    def _sync_settings(self) -> None:
        settings.USE_SYNOINDEX = bool(self.ctx.get("enabled"))
