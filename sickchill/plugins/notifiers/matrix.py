from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class MatrixNotifier(LegacyNotifierPlugin):
    id = "matrix"
    name = "Matrix"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_MATRIX"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Matrix",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_matrix",)),
        Field(name="notify_snatch", type="bool", default=False, legacy_keys=("matrix_notify_snatch",)),
        Field(name="notify_download", type="bool", default=False, legacy_keys=("matrix_notify_download",)),
        Field(name="notify_subtitledownload", type="bool", default=False, legacy_keys=("matrix_notify_subtitledownload",)),
        Field(name="api_token", type="str", default="", legacy_keys=("matrix_api_token",)),
        Field(name="server", type="str", default="", legacy_keys=("matrix_server",)),
        Field(name="room", type="str", default="", legacy_keys=("matrix_room",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_MATRIX = bool(self.ctx.get("enabled"))
        settings.MATRIX_NOTIFY_SNATCH = bool(self.ctx.get("notify_snatch"))
        settings.MATRIX_NOTIFY_DOWNLOAD = bool(self.ctx.get("notify_download"))
        settings.MATRIX_NOTIFY_SUBTITLEDOWNLOAD = bool(self.ctx.get("notify_subtitledownload"))
        settings.MATRIX_API_TOKEN = self.ctx.get("api_token") or ""
        settings.MATRIX_SERVER = self.ctx.get("server") or ""
        settings.MATRIX_ROOM = self.ctx.get("room") or ""
