"""First-party download client plugins.

Import individual modules for @register side effects:
``importlib.import_module("sickchill.plugins.clients.<id>")``.
"""

from __future__ import annotations

import importlib
import logging

logger = logging.getLogger("sickchill.plugins.clients")

FIRST_PARTY_CLIENT_MODULES = (
    "blackhole",
    "deluge",
    "deluged",
    "download_station",
    "mlnet",
    "nzbget",
    "putio",
    "qbittorrent",
    "rtorrent",
    "sabnzbd",
    "transmission",
    "utorrent",
)


def load_first_party_clients() -> None:
    import sys

    for name in FIRST_PARTY_CLIENT_MODULES:
        full = f"sickchill.plugins.clients.{name}"
        try:
            if full in sys.modules:
                importlib.reload(sys.modules[full])
            else:
                importlib.import_module(full)
        except Exception as error:
            logger.exception("Failed to load client plugin %s: %s", name, error)
