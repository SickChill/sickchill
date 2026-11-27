from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class JellyfinNotifier(LegacyNotifierPlugin):
    id = "jellyfin"
    name = "Jellyfin"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_JELLYFIN"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Jellyfin",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_jellyfin",)),
        Field(name="host", type="str", default="", legacy_keys=("jellyfin_host",)),
        Field(name="apikey", type="str", default="", legacy_keys=("jellyfin_apikey",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_JELLYFIN = bool(self.ctx.get("enabled"))
        settings.JELLYFIN_HOST = self.ctx.get("host") or ""
        settings.JELLYFIN_APIKEY = self.ctx.get("apikey") or ""
