"""Shared schema and wrapper helpers for torrent ClientPlugins."""

from __future__ import annotations

from typing import Any, ClassVar

from sickchill import settings
from sickchill.plugins.api import Field
from sickchill.plugins.kinds.client import ClientPlugin
from sickchill.plugins.settings import _as_bool

TORRENT_COMMON_SCHEMA: tuple[Field, ...] = (
    Field(name="host", type="host", default=""),
    Field(name="username", type="str", default=""),
    Field(name="password", type="password", default="", secret=True),
    Field(name="path", type="str", default=""),
    Field(name="path_incomplete", type="str", default=""),
    Field(name="label", type="str", default=""),
    Field(name="label_anime", type="str", default=""),
    Field(name="paused", type="bool", default=False),
    Field(name="seed_time", type="int", default=0),
    Field(name="verify_cert", type="bool", default=False),
)

TRANSMISSION_EXTRA_SCHEMA: tuple[Field, ...] = (
    Field(name="rpcurl", type="str", default="transmission"),
    Field(name="high_bandwidth", type="bool", default=False),
)

RTORRENT_EXTRA_SCHEMA: tuple[Field, ...] = (Field(name="auth_type", type="str", default="none"),)


def _nonempty(*values: Any) -> Any:
    """First value that is not None/'' (0 and False are kept)."""
    for value in values:
        if value is None or value == "":
            continue
        return value
    return ""


def sync_torrent_ctx_to_settings(ctx, *, overwrite_empty: bool = False) -> None:
    """
    Push client ctx into settings.TORRENT_*.

    By default do **not** blank existing settings with empty ctx values — snatch
    calls Client() with no host/user/pass and must keep saved credentials.
    """

    def _set(attr: str, value: Any, *, as_bool: bool = False, as_int: bool = False) -> None:
        if value is None or value == "":
            if overwrite_empty:
                setattr(settings, attr, False if as_bool else 0 if as_int else "")
            return
        if as_bool:
            setattr(settings, attr, _as_bool(value, False))
        elif as_int:
            try:
                setattr(settings, attr, int(value))
            except (TypeError, ValueError):
                setattr(settings, attr, 0)
        else:
            setattr(settings, attr, value)

    _set("TORRENT_HOST", ctx.get("host"))
    _set("TORRENT_USERNAME", ctx.get("username"))
    _set("TORRENT_PASSWORD", ctx.get("password"))
    _set("TORRENT_PATH", ctx.get("path"))
    _set("TORRENT_PATH_INCOMPLETE", ctx.get("path_incomplete"))
    _set("TORRENT_LABEL", ctx.get("label"))
    _set("TORRENT_LABEL_ANIME", ctx.get("label_anime"))
    if ctx.get("paused") is not None and ctx.get("paused") != "":
        settings.TORRENT_PAUSED = _as_bool(ctx.get("paused"), False)
    if ctx.get("seed_time") is not None and ctx.get("seed_time") != "":
        _set("TORRENT_SEED_TIME", ctx.get("seed_time"), as_int=True)
    if ctx.get("verify_cert") is not None and ctx.get("verify_cert") != "":
        settings.TORRENT_VERIFY_CERT = _as_bool(ctx.get("verify_cert"), False)
    if ctx.get("rpcurl") not in (None, ""):
        settings.TORRENT_RPCURL = ctx.get("rpcurl")
    if ctx.get("high_bandwidth") is not None and ctx.get("high_bandwidth") != "":
        settings.TORRENT_HIGH_BANDWIDTH = _as_bool(ctx.get("high_bandwidth"), False)
    if ctx.get("auth_type") not in (None, ""):
        settings.TORRENT_AUTH_TYPE = ctx.get("auth_type")


class TorrentClientPlugin(ClientPlugin):
    """Wraps sickchill.oldbeard.clients.<id>.Client."""

    version = "1.0.0"
    schema: ClassVar[tuple[Field, ...]] = TORRENT_COMMON_SCHEMA

    def _reload_ctx_from_cfg(self) -> None:
        """Refresh ctx from [CLIENTS][[id]] so save → send does not use a stale cache."""
        from sickchill.plugins.clients._settings_sync import reload_client_ctx

        reload_client_ctx(self)

    def _sync_settings(self) -> None:
        sync_torrent_ctx_to_settings(self.ctx, overwrite_empty=False)

    def _resolve_credentials(self, host=None, username=None, password=None) -> tuple[Any, Any, Any]:
        """explicit args → CLIENTS ctx → settings.* (never blank a filled source)."""
        self._reload_ctx_from_cfg()
        self._sync_settings()
        host = _nonempty(host, self.ctx.get("host"), settings.TORRENT_HOST)
        username = _nonempty(username, self.ctx.get("username"), settings.TORRENT_USERNAME)
        password = _nonempty(password, self.ctx.get("password"), settings.TORRENT_PASSWORD)
        # Keep settings in sync for GenericClient code paths that read globals (path/label/etc.).
        if host:
            settings.TORRENT_HOST = host
        if username:
            settings.TORRENT_USERNAME = username
        if password:
            settings.TORRENT_PASSWORD = password
        return host, username, password

    def _impl(self, host=None, username=None, password=None):
        import importlib

        # Always positional: qBittorrent.Client first param is named `url`, not `host`.
        # Matches legacy getClientInstance(name)(host, username, password).
        mod = importlib.import_module(f"sickchill.oldbeard.clients.{self.id}")
        return mod.Client(host, username, password)

    def send(self, result: Any, host=None, username=None, password=None) -> bool:
        host, username, password = self._resolve_credentials(host, username, password)
        return bool(self._impl(host, username, password).sendTORRENT(result))

    def test_client_connection(self, *args: Any, **kwargs: Any) -> tuple[bool, str]:
        host = kwargs.get("host", args[0] if len(args) > 0 else None)
        username = kwargs.get("username", args[1] if len(args) > 1 else None)
        password = kwargs.get("password", args[2] if len(args) > 2 else None)
        host, username, password = self._resolve_credentials(host, username, password)
        result = self._impl(host, username, password).test_client_connection()
        if isinstance(result, tuple):
            return bool(result[0]), str(result[1] if len(result) > 1 else result[0])
        return bool(result), "ok" if result else "failed"
