from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class EmbyNotifier(LegacyNotifierPlugin):
    id = "emby"
    name = "Emby"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_EMBY"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Emby",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_emby",)),
        Field(name="host", type="str", default="", legacy_keys=("emby_host",)),
        Field(name="apikey", type="str", default="", legacy_keys=("emby_apikey",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_EMBY = bool(self.ctx.get("enabled"))
        settings.EMBY_HOST = self.ctx.get("host") or ""
        settings.EMBY_APIKEY = self.ctx.get("apikey") or ""
