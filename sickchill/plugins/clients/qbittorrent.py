from __future__ import annotations

from sickchill.plugins.api import register
from sickchill.plugins.clients._torrent import TorrentClientPlugin


@register
class QbittorrentClient(TorrentClientPlugin):
    id = "qbittorrent"
    name = "qBittorrent"
