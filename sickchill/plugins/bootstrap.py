from __future__ import annotations

import logging

from sickchill import settings
from sickchill.plugins.clients.config import sync_clients_from_settings, write_clients_to_cfg
from sickchill.plugins.legacy_maps import ALL_LEGACY_MAPS, CLIENT_SECTION_MAPS
from sickchill.plugins.manager import plugin_manager
from sickchill.plugins.metadata.config import migrate_metadata_from_general, sync_metadata_from_settings, write_metadata_to_cfg
from sickchill.plugins.providers.config import apply_providers_from_cfg, migrate_provider_sections, write_providers_to_cfg
from sickchill.plugins.settings import (
    migrate_client_maps,
    migrate_extensions_notifiers_to_top_level,
    migrate_legacy_maps,
    sync_legacy_maps_to_settings,
    write_legacy_maps_from_settings,
)

logger = logging.getLogger("sickchill.plugins.bootstrap")


def sync_all_plugin_runtime_settings(cfg=None) -> None:
    """Push [NOTIFIERS], [CLIENTS], [METADATA], and [PROVIDERS] into runtime objects / settings.*."""
    cfg = cfg if cfg is not None else settings.CFG
    if cfg is None:
        return
    sync_legacy_maps_to_settings(cfg, ALL_LEGACY_MAPS)
    sync_clients_from_settings(cfg)
    sync_metadata_from_settings(cfg)
    # Providers are object instances (providerList / customs), not settings.* globals.
    if getattr(settings, "providerList", None) is not None:
        from sickchill.plugins.providers.config import custom_providers_from_cfg, providers_section_has_customs

        if providers_section_has_customs(cfg):
            settings.newznab_provider_list, settings.torrent_rss_provider_list = custom_providers_from_cfg(cfg)
            settings.NEWZNAB_DATA = "!!!".join(x.config_string() for x in settings.newznab_provider_list)
        apply_providers_from_cfg(cfg)


def write_all_plugin_settings_to_cfg(cfg) -> None:
    """Persist settings.* / live providers into [NOTIFIERS], [CLIENTS], [METADATA], [PROVIDERS]."""
    write_legacy_maps_from_settings(cfg, ALL_LEGACY_MAPS)
    write_clients_to_cfg(cfg)
    write_metadata_to_cfg(cfg)
    write_providers_to_cfg(cfg)


def bootstrap_plugins() -> bool:
    """
    One-shot startup:
      1) register/discover plugin classes
      2) migrate notifier legacy maps → [NOTIFIERS]
      3) migrate leftover [extensions][[notifiers]] → [NOTIFIERS]
      4) migrate client legacy maps → [CLIENTS]
      5) migrate General.metadata_* → [METADATA]
      6) migrate legacy provider sections / Newznab+TorrentRss blobs → [PROVIDERS]
      7) also run Plugin.legacy_sections migrator for converted classes
      8) sync settings.* / provider objects from plugin sections
    Returns True if config was mutated (caller should save).
    """
    from sickchill.plugins.clients import load_first_party_clients
    from sickchill.plugins.metadata import load_first_party_metadata
    from sickchill.plugins.notifiers import load_first_party_notifiers
    from sickchill.plugins.providers import load_first_party_providers

    load_first_party_notifiers()
    load_first_party_clients()
    load_first_party_metadata()
    load_first_party_providers()

    plugins_dir = getattr(settings, "PLUGIN_DIR", None) or None
    if plugins_dir == "":
        plugins_dir = None

    plugin_manager.discover(data_dir=settings.DATA_DIR, plugins_dir=plugins_dir)

    mutated = migrate_legacy_maps(settings.CFG, ALL_LEGACY_MAPS)
    mutated = migrate_extensions_notifiers_to_top_level(settings.CFG) or mutated
    mutated = migrate_client_maps(settings.CFG, CLIENT_SECTION_MAPS) or mutated
    mutated = migrate_metadata_from_general(settings.CFG) or mutated
    mutated = migrate_provider_sections(settings.CFG) or mutated
    mutated = plugin_manager.migrate_settings(settings.CFG) or mutated

    sync_all_plugin_runtime_settings(settings.CFG)
    plugin_manager._instances.clear()

    if mutated:
        logger.info("Plugin legacy settings migrated; config should be saved")
    return mutated
