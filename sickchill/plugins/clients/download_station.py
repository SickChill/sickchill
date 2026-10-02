from __future__ import annotations

from typing import Any, ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.clients._torrent import TORRENT_COMMON_SCHEMA, TorrentClientPlugin


@register
class DownloadStationClient(TorrentClientPlugin):
    id = "download_station"
    name = "DownloadStation"
    schema: ClassVar[tuple[Field, ...]] = TORRENT_COMMON_SCHEMA

    def _sync_settings(self) -> None:
        from sickchill.plugins.clients._torrent import _plaintext_client_password

        super()._sync_settings()
        method_matches = getattr(settings, "TORRENT_METHOD", None) == self.id
        # Prefer ctx, but never blank existing DSM settings with empty ctx (same class of bug as qbt).
        torrent_host = settings.TORRENT_HOST if method_matches else ""
        torrent_username = settings.TORRENT_USERNAME if method_matches else ""
        torrent_password = settings.TORRENT_PASSWORD if method_matches else ""
        torrent_path = settings.TORRENT_PATH if method_matches else ""
        host = self.ctx.get("host") or settings.SYNOLOGY_DSM_HOST or torrent_host or ""
        username = self.ctx.get("username") or settings.SYNOLOGY_DSM_USERNAME or torrent_username or ""
        password = _plaintext_client_password(self.ctx.get("password")) or settings.SYNOLOGY_DSM_PASSWORD or torrent_password or ""
        path = self.ctx.get("path") or settings.SYNOLOGY_DSM_PATH or torrent_path or ""
        if host:
            settings.SYNOLOGY_DSM_HOST = host
            if method_matches:
                settings.TORRENT_HOST = host
        if username:
            settings.SYNOLOGY_DSM_USERNAME = username
            if method_matches:
                settings.TORRENT_USERNAME = username
        if password:
            settings.SYNOLOGY_DSM_PASSWORD = password
            if method_matches:
                settings.TORRENT_PASSWORD = password
        if path:
            settings.SYNOLOGY_DSM_PATH = path
            if method_matches:
                settings.TORRENT_PATH = path

    def _resolve_credentials(self, host=None, username=None, password=None):
        # Resolve against CLIENTS / DSM globals; TORRENT_* only when DS is the torrent method.
        from sickchill.plugins.clients._torrent import _nonempty, _plaintext_client_password

        self._reload_ctx_from_cfg()
        method_matches = getattr(settings, "TORRENT_METHOD", None) == self.id
        if method_matches:
            self._sync_settings()
        host = _nonempty(host, self.ctx.get("host"), settings.TORRENT_HOST if method_matches else None, settings.SYNOLOGY_DSM_HOST)
        username = _nonempty(username, self.ctx.get("username"), settings.TORRENT_USERNAME if method_matches else None, settings.SYNOLOGY_DSM_USERNAME)
        password = _nonempty(
            password,
            _plaintext_client_password(self.ctx.get("password")),
            settings.TORRENT_PASSWORD if method_matches else None,
            settings.SYNOLOGY_DSM_PASSWORD,
        )
        if host:
            settings.SYNOLOGY_DSM_HOST = host
            if method_matches:
                settings.TORRENT_HOST = host
        if username:
            settings.SYNOLOGY_DSM_USERNAME = username
            if method_matches:
                settings.TORRENT_USERNAME = username
        if password:
            settings.SYNOLOGY_DSM_PASSWORD = password
            if method_matches:
                settings.TORRENT_PASSWORD = password
        return host, username, password

    def send(self, result: Any, host=None, username=None, password=None) -> bool:
        host, username, password = self._resolve_credentials(host, username, password)
        impl = self._impl(host, username, password)
        if getattr(result, "is_nzb", False) or getattr(result, "is_nzbdata", False):
            return bool(impl.send_nzb(result))
        return bool(impl.sendTORRENT(result))

    def send_nzb(self, result: Any, host=None, username=None, password=None) -> bool:
        return self.send(result, host=host, username=username, password=password)
