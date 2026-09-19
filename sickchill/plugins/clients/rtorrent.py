from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import Field, register
from sickchill.plugins.clients._torrent import RTORRENT_EXTRA_SCHEMA, TORRENT_COMMON_SCHEMA, TorrentClientPlugin


@register
class RtorrentClient(TorrentClientPlugin):
    id = "rtorrent"
    name = "rTorrent"
    schema: ClassVar[tuple[Field, ...]] = TORRENT_COMMON_SCHEMA + RTORRENT_EXTRA_SCHEMA
