from __future__ import annotations

from typing import Any, ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.clients._settings_sync import reload_client_ctx, set_if_present
from sickchill.plugins.kinds.client import ClientPlugin


@register
class NzbgetClient(ClientPlugin):
    id = "nzbget"
    name = "NZBget"
    version = "1.0.0"
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="username", type="str", default="nzbget"),
        Field(name="password", type="password", default="", secret=True),
        Field(name="category", type="str", default="tv"),
        Field(name="category_backlog", type="str", default=""),
        Field(name="category_anime", type="str", default="anime"),
        Field(name="category_anime_backlog", type="str", default=""),
        Field(name="host", type="host", default=""),
        Field(name="use_https", type="bool", default=False),
        Field(name="priority", type="int", default=100),
    )

    def _sync_settings(self) -> None:
        # Never blank saved NZBGET_* with an empty/stale ctx (same failure mode as qBittorrent).
        reload_client_ctx(self)
        set_if_present(settings, "NZBGET_USERNAME", self.ctx.get("username"))
        set_if_present(settings, "NZBGET_PASSWORD", self.ctx.get("password"))
        set_if_present(settings, "NZBGET_CATEGORY", self.ctx.get("category"))
        set_if_present(settings, "NZBGET_CATEGORY_BACKLOG", self.ctx.get("category_backlog"))
        set_if_present(settings, "NZBGET_CATEGORY_ANIME", self.ctx.get("category_anime"))
        set_if_present(settings, "NZBGET_CATEGORY_ANIME_BACKLOG", self.ctx.get("category_anime_backlog"))
        set_if_present(settings, "NZBGET_HOST", self.ctx.get("host"))
        if self.ctx.get("use_https") is not None and self.ctx.get("use_https") != "":
            set_if_present(settings, "NZBGET_USE_HTTPS", self.ctx.get("use_https"), as_bool=True)
        if self.ctx.get("priority") is not None and self.ctx.get("priority") != "":
            set_if_present(settings, "NZBGET_PRIORITY", self.ctx.get("priority"), as_int=True, default_int=100)

    def send(self, result: Any, proper: bool = False, **_kwargs) -> bool:
        self._sync_settings()
        from sickchill.oldbeard import nzbget

        return bool(nzbget.send_nzb(result, proper))

    def test_client_connection(self, *args: Any, **kwargs: Any) -> tuple[bool, str]:
        self._sync_settings()
        host = kwargs.get("host") or (args[0] if args else None) or settings.NZBGET_HOST
        if not host:
            return False, "NZBget host is not configured"
        return True, f"NZBget settings loaded for {host}"
