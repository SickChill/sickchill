from __future__ import annotations

from typing import Any, ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.clients._settings_sync import reload_client_ctx, set_if_present
from sickchill.plugins.kinds.client import ClientPlugin


@register
class SabnzbdClient(ClientPlugin):
    id = "sabnzbd"
    name = "SABnzbd"
    version = "1.0.0"
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="username", type="str", default=""),
        Field(name="password", type="password", default="", secret=True),
        Field(name="apikey", type="password", default="", secret=True),
        Field(name="category", type="str", default="tv"),
        Field(name="category_backlog", type="str", default=""),
        Field(name="category_anime", type="str", default="anime"),
        Field(name="category_anime_backlog", type="str", default=""),
        Field(name="host", type="host", default=""),
        Field(name="forced", type="bool", default=False),
    )

    def _sync_settings(self) -> None:
        # Never blank saved SAB_* with an empty/stale ctx (same failure mode as qBittorrent).
        reload_client_ctx(self)
        set_if_present(settings, "SAB_USERNAME", self.ctx.get("username"))
        set_if_present(settings, "SAB_PASSWORD", self.ctx.get("password"))
        set_if_present(settings, "SAB_APIKEY", self.ctx.get("apikey"))
        set_if_present(settings, "SAB_CATEGORY", self.ctx.get("category"))
        set_if_present(settings, "SAB_CATEGORY_BACKLOG", self.ctx.get("category_backlog"))
        set_if_present(settings, "SAB_CATEGORY_ANIME", self.ctx.get("category_anime"))
        set_if_present(settings, "SAB_CATEGORY_ANIME_BACKLOG", self.ctx.get("category_anime_backlog"))
        set_if_present(settings, "SAB_HOST", self.ctx.get("host"))
        if self.ctx.get("forced") is not None and self.ctx.get("forced") != "":
            set_if_present(settings, "SAB_FORCED", self.ctx.get("forced"), as_bool=True)

    def send(self, result: Any, **_kwargs) -> bool:
        self._sync_settings()
        from sickchill.oldbeard import sab

        return bool(sab.send_nzb(result))

    def test_client_connection(self, *args: Any, **kwargs: Any) -> tuple[bool, str]:
        self._sync_settings()
        host = kwargs.get("host") or (args[0] if args else None) or settings.SAB_HOST
        if not host:
            return False, "SABnzbd host is not configured"
        username = kwargs.get("username") or (args[1] if len(args) > 1 else None) or settings.SAB_USERNAME
        password = kwargs.get("password") or (args[2] if len(args) > 2 else None) or settings.SAB_PASSWORD
        apikey = kwargs.get("apikey") or (args[3] if len(args) > 3 else None) or settings.SAB_APIKEY
        from sickchill.oldbeard import sab

        connection, access_msg = sab.get_sab_acces_method(host)
        if not connection:
            return False, f"Unable to connect to host ({access_msg})"
        authed, auth_msg = sab.test_client_connection(host, username, password, apikey)
        if authed:
            return True, "Success. Connected and authenticated"
        return False, f"Authentication failed ({access_msg}): {auth_msg}"
