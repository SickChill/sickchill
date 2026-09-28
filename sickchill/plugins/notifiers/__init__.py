"""First-party notifier plugins.

Import individual modules for @register side effects (avoid circular package imports):
``importlib.import_module("sickchill.plugins.notifiers.<id>")``.
"""

from __future__ import annotations

import importlib
import inspect
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

    from sickchill.plugins.api import Plugin, register

    for name in FIRST_PARTY_NOTIFIER_MODULES:
        full = f"sickchill.plugins.notifiers.{name}"
        try:
            if full in sys.modules:
                # Re-register classes from the already-imported module so identities stay
                # stable across clear_registry() in tests (reload would create new classes).
                module = sys.modules[full]
                for obj in vars(module).values():
                    if not inspect.isclass(obj):
                        continue
                    try:
                        if not issubclass(obj, Plugin) or obj is Plugin:
                            continue
                    except TypeError:
                        continue
                    if getattr(obj, "__module__", None) != full:
                        continue
                    if not getattr(obj, "id", None):
                        continue
                    register(obj)
            else:
                importlib.import_module(full)
        except Exception as error:
            logger.exception("Failed to load notifier plugin %s: %s", name, error)
