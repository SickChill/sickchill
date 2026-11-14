"""First-party metadata generator plugins.

Import individual modules for @register side effects:
``importlib.import_module("sickchill.plugins.metadata.<id>")``.
"""

from __future__ import annotations

import importlib
import logging

logger = logging.getLogger("sickchill.plugins.metadata")

FIRST_PARTY_METADATA_MODULES = (
    "kodi",
    "mediabrowser",
    "sony_ps3",
    "wdtv",
    "tivo",
    "mede8er",
)


def load_first_party_metadata() -> None:
    import sys

    for name in FIRST_PARTY_METADATA_MODULES:
        full = f"sickchill.plugins.metadata.{name}"
        try:
            if full in sys.modules:
                importlib.reload(sys.modules[full])
            else:
                importlib.import_module(full)
        except Exception as error:
            logger.exception("Failed to load metadata plugin %s: %s", name, error)
