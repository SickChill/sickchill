from __future__ import annotations

import logging

from sickchill import settings
from sickchill.plugins.clients.config import sync_clients_from_settings, write_clients_to_cfg
from sickchill.plugins.legacy_maps import ALL_LEGACY_MAPS, CLIENT_SECTION_MAPS
from sickchill.plugins.manager import plugin_manager
from sickchill.plugins.metadata.config import migrate_metadata_from_general, sync_metadata_from_settings, write_metadata_to_cfg
from sickchill.plugins.settings import migrate_client_maps, migrate_legacy_maps, sync_legacy_maps_to_settings, write_legacy_maps_from_settings

logger = logging.getLogger("sickchill.plugins.bootstrap")


def sync_all_plugin_runtime_settings(cfg=None) -> None:
    """Push [extensions], [CLIENTS], and [METADATA] into settings.* for Mako / queues / unconverted code."""
    cfg = cfg if cfg is not None else settings.CFG
    if cfg is None:
        return
    sync_legacy_maps_to_settings(cfg, ALL_LEGACY_MAPS)
    sync_clients_from_settings(cfg)
    sync_metadata_from_settings(cfg)


def write_all_plugin_settings_to_cfg(cfg) -> None:
    """Persist settings.* into [extensions], [CLIENTS], and [METADATA]; drop legacy sections when allowed."""
    write_legacy_maps_from_settings(cfg, ALL_LEGACY_MAPS)
    write_clients_to_cfg(cfg)
    write_metadata_to_cfg(cfg)


def bootstrap_plugins() -> bool:
    """
    One-shot startup:
      1) register/discover plugin classes
      2) migrate notifier legacy maps → [extensions]
      3) migrate client legacy maps → [CLIENTS]
      4) migrate General.metadata_* → [METADATA]
      5) also run Plugin.legacy_sections migrator for converted classes
      6) sync settings.* from [extensions], [CLIENTS], and [METADATA]
    Returns True if config was mutated (caller should save).
    """
    from sickchill.plugins.clients import load_first_party_clients
    from sickchill.plugins.metadata import load_first_party_metadata
    from sickchill.plugins.notifiers import load_first_party_notifiers

    load_first_party_notifiers()
    load_first_party_clients()
    load_first_party_metadata()

    plugins_dir = getattr(settings, "PLUGIN_DIR", None) or None
    if plugins_dir == "":
        plugins_dir = None

    plugin_manager.discover(data_dir=settings.DATA_DIR, plugins_dir=plugins_dir)

    mutated = migrate_legacy_maps(settings.CFG, ALL_LEGACY_MAPS)
    mutated = migrate_client_maps(settings.CFG, CLIENT_SECTION_MAPS) or mutated
    mutated = migrate_metadata_from_general(settings.CFG) or mutated
    mutated = plugin_manager.migrate_settings(settings.CFG) or mutated

    sync_all_plugin_runtime_settings(settings.CFG)
    plugin_manager._instances.clear()

    if mutated:
        logger.info("Plugin legacy settings migrated; config should be saved")
    return mutated
