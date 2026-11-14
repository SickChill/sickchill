from __future__ import annotations

from typing import Any, ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.client import ClientPlugin


@register
class BlackholeClient(ClientPlugin):
    id = "blackhole"
    name = "Black Hole"
    version = "1.0.0"
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="nzb_dir", type="str", default=""),
        Field(name="torrent_dir", type="str", default=""),
    )

    def _sync_settings(self) -> None:
        settings.NZB_DIR = self.ctx.get("nzb_dir") or settings.NZB_DIR or ""
        settings.TORRENT_DIR = self.ctx.get("torrent_dir") or settings.TORRENT_DIR or ""

    def send(self, result: Any, **_kwargs) -> bool:
        self._sync_settings()
        from sickchill.oldbeard.search import _download_result

        return bool(_download_result(result))

    def test_client_connection(self, *args: Any, **kwargs: Any) -> tuple[bool, str]:
        self._sync_settings()
        return True, "Black hole does not require a live connection"
