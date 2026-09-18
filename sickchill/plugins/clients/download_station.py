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
        super()._sync_settings()
        # Prefer ctx, but never blank existing DSM settings with empty ctx (same class of bug as qbt).
        host = self.ctx.get("host") or settings.SYNOLOGY_DSM_HOST or settings.TORRENT_HOST or ""
        username = self.ctx.get("username") or settings.SYNOLOGY_DSM_USERNAME or settings.TORRENT_USERNAME or ""
        password = self.ctx.get("password") or settings.SYNOLOGY_DSM_PASSWORD or settings.TORRENT_PASSWORD or ""
        path = self.ctx.get("path") or settings.SYNOLOGY_DSM_PATH or settings.TORRENT_PATH or ""
        if host:
            settings.SYNOLOGY_DSM_HOST = host
            settings.TORRENT_HOST = host
        if username:
            settings.SYNOLOGY_DSM_USERNAME = username
            settings.TORRENT_USERNAME = username
        if password:
            settings.SYNOLOGY_DSM_PASSWORD = password
            settings.TORRENT_PASSWORD = password
        if path:
            settings.SYNOLOGY_DSM_PATH = path
            settings.TORRENT_PATH = path

    def _resolve_credentials(self, host=None, username=None, password=None):
        # Resolve against TORRENT_* / CLIENTS, then fall back to DSM globals.
        from sickchill.plugins.clients._torrent import _nonempty

        host, username, password = super()._resolve_credentials(host, username, password)
        host = _nonempty(host, settings.SYNOLOGY_DSM_HOST)
        username = _nonempty(username, settings.SYNOLOGY_DSM_USERNAME)
        password = _nonempty(password, settings.SYNOLOGY_DSM_PASSWORD)
        if host:
            settings.SYNOLOGY_DSM_HOST = host
            settings.TORRENT_HOST = host
        if username:
            settings.SYNOLOGY_DSM_USERNAME = username
            settings.TORRENT_USERNAME = username
        if password:
            settings.SYNOLOGY_DSM_PASSWORD = password
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
