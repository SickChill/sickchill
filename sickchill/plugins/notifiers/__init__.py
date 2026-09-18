"""First-party notifier plugins.

Import individual modules for @register side effects (avoid circular package imports):
``importlib.import_module("sickchill.plugins.notifiers.<id>")``.
"""

from __future__ import annotations

import importlib
import logging

logger = logging.getLogger("sickchill.plugins.notifiers")

FIRST_PARTY_NOTIFIER_MODULES = (
    "discord",
    "slack",
    "telegram",
    "gotify",
    "join",
    "freemobile",
    "pushbullet",
    "pushover",
    "prowl",
    "libnotify",
    "mattermost",
    "mattermostbot",
    "rocketchat",
    "matrix",
    "email",
    "twitter",
    "twilio",
    "synologynotifier",
    "kodi",
    "plex",
    "emby",
    "jellyfin",
    "nmj",
    "nmjv2",
    "synoindex",
    "pytivo",
    "trakt",
)


def load_first_party_notifiers() -> None:
    import sys

    for name in FIRST_PARTY_NOTIFIER_MODULES:
        full = f"sickchill.plugins.notifiers.{name}"
        try:
            if full in sys.modules:
                importlib.reload(sys.modules[full])
            else:
                importlib.import_module(full)
        except Exception as error:
            logger.exception("Failed to load notifier plugin %s: %s", name, error)
