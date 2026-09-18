"""METADATA section sync between config.ini and settings.* packed strings."""

from __future__ import annotations

import logging
from typing import Any

from configobj import ConfigObj

from sickchill.plugins.settings import _as_bool, read_metadata_section, write_metadata_section

logger = logging.getLogger("sickchill.plugins.metadata")

METADATA_FLAG_NAMES: tuple[str, ...] = (
    "show_metadata",
    "episode_metadata",
    "fanart",
    "poster",
    "banner",
    "episode_thumbnails",
    "season_posters",
    "season_banners",
    "season_all_poster",
    "season_all_banner",
)

DEFAULT_PACKED = "0|0|0|0|0|0|0|0|0|0"

# plugin_id, settings_attr, General legacy key, dict display name, provider module
METADATA_GENERATORS: tuple[tuple[str, str, str, str, str], ...] = (
    ("kodi", "METADATA_KODI", "metadata_kodi", "KODI", "sickchill.providers.metadata.kodi"),
    ("mediabrowser", "METADATA_MEDIABROWSER", "metadata_mediabrowser", "MediaBrowser", "sickchill.providers.metadata.mediabrowser"),
    ("sony_ps3", "METADATA_PS3", "metadata_ps3", "Sony PS3", "sickchill.providers.metadata.ps3"),
    ("wdtv", "METADATA_WDTV", "metadata_wdtv", "WDTV", "sickchill.providers.metadata.wdtv"),
    ("tivo", "METADATA_TIVO", "metadata_tivo", "TIVO", "sickchill.providers.metadata.tivo"),
    ("mede8er", "METADATA_MEDE8ER", "metadata_mede8er", "Mede8er", "sickchill.providers.metadata.mede8er"),
)

_GENERAL_METADATA_KEYS = tuple(item[2] for item in METADATA_GENERATORS)


def unpack_packed_config(packed: str | None) -> dict[str, bool]:
    """Unpack ``0|1|…`` into the 10 metadata flag bools."""
    raw = (packed or DEFAULT_PACKED).strip() or DEFAULT_PACKED
    parts = raw.split("|")
    values: list[bool] = []
    for index, name in enumerate(METADATA_FLAG_NAMES):
        try:
            values.append(bool(int(parts[index])) if index < len(parts) else False)
        except (TypeError, ValueError):
            values.append(False)
    return dict(zip(METADATA_FLAG_NAMES, values, strict=True))


def pack_flags(flags: dict[str, Any] | None) -> str:
    """Pack flag dict / section into ``0|1|…`` matching GenericMetadata.get_config."""
    flags = flags or {}
    bits: list[str] = []
    for name in METADATA_FLAG_NAMES:
        bits.append("1" if _as_bool(flags.get(name), False) else "0")
    return "|".join(bits)


def _section_has_flags(section: dict[str, Any] | None) -> bool:
    if not section:
        return False
    return any(name in section for name in METADATA_FLAG_NAMES)


def migrate_metadata_from_general(cfg: ConfigObj) -> bool:
    """
    One-shot: unpack General.metadata_* packed strings into [METADATA][[id]] bools.
    Strip the six keys from General only (never delete [General]).
    INFO only when real values moved; empty/no-op cleanup is silent and not mutated.
    """
    mutated = False
    general = cfg.get("General") if cfg is not None and "General" in cfg else None

    for plugin_id, _attr, general_key, _name, _module in METADATA_GENERATORS:
        section = read_metadata_section(cfg, plugin_id)
        legacy_packed = None
        if general is not None and general_key in general:
            legacy_packed = general.get(general_key)

        if not _section_has_flags(section) and legacy_packed not in (None, ""):
            flags = unpack_packed_config(str(legacy_packed))
            write_metadata_section(cfg, plugin_id, flags)
            logger.info(
                "Plugin migrator: moved General.%s -> METADATA[[%s]] (%s)",
                general_key,
                plugin_id,
                pack_flags(flags),
            )
            mutated = True
        elif not _section_has_flags(section):
            # Ensure a stable empty section shape only when we already mutated elsewhere?
            # Prefer not creating empty METADATA shells on clean installs.
            pass

    if general is None:
        return mutated

    stripped_real = False
    for key in _GENERAL_METADATA_KEYS:
        if key not in general:
            continue
        value = general.get(key)
        del general[key]
        # Empty / default leftovers recreated by old check_setting_str: silent, no mutate.
        if value not in (None, "", DEFAULT_PACKED):
            stripped_real = True
            logger.debug("Plugin migrator: stripped General.%s after METADATA migrate", key)

    # If we only scrubbed empty/default keys, do not force a config save.
    if stripped_real:
        mutated = True

    return mutated


def sync_metadata_from_settings(cfg: ConfigObj) -> None:
    """Push [METADATA][[id]] bools into settings.METADATA_* packed strings."""
    from sickchill import settings as sc_settings

    for plugin_id, settings_attr, _general_key, _name, _module in METADATA_GENERATORS:
        section = read_metadata_section(cfg, plugin_id)
        if not _section_has_flags(section):
            continue
        setattr(sc_settings, settings_attr, pack_flags(section))


def write_metadata_to_cfg(cfg: ConfigObj) -> None:
    """Persist settings.METADATA_* packed strings into [METADATA]; strip General metadata_*."""
    from sickchill import settings as sc_settings

    for plugin_id, settings_attr, _general_key, _name, _module in METADATA_GENERATORS:
        packed = getattr(sc_settings, settings_attr, None) or DEFAULT_PACKED
        write_metadata_section(cfg, plugin_id, unpack_packed_config(str(packed)))

    if "General" in cfg:
        general = cfg["General"]
        for key in _GENERAL_METADATA_KEYS:
            if key in general:
                del general[key]


def refresh_metadata_provider_dict() -> None:
    """Rebuild settings.metadata_provider_dict from modules + current packed settings."""
    import importlib

    from sickchill import settings as sc_settings

    result = {}
    for _plugin_id, settings_attr, _general_key, _name, module_path in METADATA_GENERATORS:
        mod = importlib.import_module(module_path)
        generator = mod.metadata_class()
        packed = getattr(sc_settings, settings_attr, None) or DEFAULT_PACKED
        generator.set_config(str(packed))
        result[generator.name] = generator
    sc_settings.metadata_provider_dict = result


def packed_from_metadata_or_general(cfg: ConfigObj | None, plugin_id: str, general_key: str, default: str = DEFAULT_PACKED) -> str:
    """Prefer [METADATA][[id]]; else peek General (no create); else default."""
    if cfg is not None:
        section = read_metadata_section(cfg, plugin_id)
        if _section_has_flags(section):
            return pack_flags(section)
        try:
            if "General" in cfg and general_key in cfg["General"]:
                value = cfg["General"][general_key]
                if value not in (None, ""):
                    return str(value)
        except (KeyError, TypeError):
            pass
    return default
