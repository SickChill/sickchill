from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import Field, register
from sickchill.plugins.clients._torrent import TORRENT_COMMON_SCHEMA, TRANSMISSION_EXTRA_SCHEMA, TorrentClientPlugin


@register
class TransmissionClient(TorrentClientPlugin):
    id = "transmission"
    name = "Transmission"
    schema: ClassVar[tuple[Field, ...]] = TORRENT_COMMON_SCHEMA + TRANSMISSION_EXTRA_SCHEMA
