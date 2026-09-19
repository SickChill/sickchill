from __future__ import annotations

import logging
from typing import Any

from configobj import ConfigObj

from sickchill.plugins.api import Field, Plugin, PluginKind

logger = logging.getLogger("sickchill.plugins.settings")


def ensure_extension_section(cfg: ConfigObj, kind: PluginKind, plugin_id: str) -> dict[str, Any]:
    extensions = cfg.setdefault("extensions", {})
    kind_section = extensions.setdefault(kind.value, {})
    plugin_section = kind_section.setdefault(plugin_id, {})
    return plugin_section


def read_plugin_section(cfg: ConfigObj, kind: PluginKind, plugin_id: str) -> dict[str, Any]:
    try:
        return dict(cfg["extensions"][kind.value][plugin_id])
    except (KeyError, TypeError):
        return {}


def write_plugin_section(cfg: ConfigObj, kind: PluginKind, plugin_id: str, data: dict[str, Any]) -> None:
    section = ensure_extension_section(cfg, kind, plugin_id)
    section.clear()
    section.update(data)


def ensure_client_section(cfg: ConfigObj, client_id: str) -> dict[str, Any]:
    """Ensure top-level [CLIENTS][[client_id]] (not under [extensions])."""
    clients = cfg.setdefault("CLIENTS", {})
    return clients.setdefault(client_id, {})


def read_client_section(cfg: ConfigObj, client_id: str) -> dict[str, Any]:
    try:
        return dict(cfg["CLIENTS"][client_id])
    except (KeyError, TypeError):
        return {}


def write_client_section(cfg: ConfigObj, client_id: str, data: dict[str, Any]) -> None:
    section = ensure_client_section(cfg, client_id)
    section.clear()
    section.update(data)


def ensure_metadata_section(cfg: ConfigObj, metadata_id: str) -> dict[str, Any]:
    """Ensure top-level [METADATA][[metadata_id]] (not under [extensions])."""
    metadata = cfg.setdefault("METADATA", {})
    return metadata.setdefault(metadata_id, {})


def read_metadata_section(cfg: ConfigObj, metadata_id: str) -> dict[str, Any]:
    try:
        return dict(cfg["METADATA"][metadata_id])
    except (KeyError, TypeError):
        return {}


def write_metadata_section(cfg: ConfigObj, metadata_id: str, data: dict[str, Any]) -> None:
    section = ensure_metadata_section(cfg, metadata_id)
    section.clear()
    section.update(data)


def _coerce_default(field_def: Field) -> Any:
    if field_def.type == "bool":
        return bool(field_def.default)
    return field_def.default


def _section_keys(section) -> list[str]:
    return [k for k in section if not str(k).startswith("#")]


def _legacy_has_values(legacy) -> bool:
    """True if the legacy INI section has any non-empty values."""
    if legacy is None:
        return False
    for key in _section_keys(legacy):
        if legacy[key] not in (None, ""):
            return True
    return False


def _log_migrated(legacy_section: str, destinations: list[str], copied_keys: list[str]) -> None:
    """One INFO line when something actually moved out of a legacy section."""
    if not copied_keys:
        return
    dest = ", ".join(destinations) if destinations else "extensions"
    keys = ", ".join(sorted(set(copied_keys)))
    logger.info("Plugin migrator: moved [%s] -> %s (%s)", legacy_section, dest, keys)


def _log_removed_legacy(legacy_section: str, *, moved: bool, unmapped: list[str] | None = None) -> None:
    """Log only when real values were migrated. Silent for empty/no-op cleanups (every-boot noise)."""
    if not moved:
        return
    if unmapped:
        logger.info(
            "Plugin migrator: dropping unmapped keys from [%s]: %s",
            legacy_section,
            ", ".join(sorted(str(k) for k in unmapped)),
        )
    logger.info("Plugin migrator: removed legacy section [%s]", legacy_section)


def migrate_legacy_sections(cfg: ConfigObj, plugin_classes: list[type[Plugin]]) -> bool:
    """
    For each plugin with legacy_sections:
      - ensure [extensions][[kind]][[[id]]]
      - for each Field, if dest missing, copy from the first matching legacy key
      - DELETE each legacy section from cfg entirely
    Return True if cfg mutated.
    """
    mutated = False
    # legacy_section -> (destinations, copied_keys)
    moved: dict[str, tuple[set[str], list[str]]] = {}

    for cls in plugin_classes:
        if not getattr(cls, "legacy_sections", ()):
            continue

        section = ensure_extension_section(cfg, cls.kind, cls.id)
        dest = f"extensions.{cls.kind.value}.{cls.id}"
        for field_def in cls.all_fields():
            if field_def.name in section and section[field_def.name] not in (None, ""):
                continue
            keys = field_def.legacy_keys or (field_def.name,)
            copied = False
            for legacy_section in cls.legacy_sections:
                if legacy_section not in cfg:
                    continue
                legacy = cfg[legacy_section]
                for key in keys:
                    if key in legacy and legacy[key] not in (None, ""):
                        section[field_def.name] = legacy[key]
                        logger.debug(
                            "Plugin migrator: copied %s.%s -> %s.%s",
                            legacy_section,
                            key,
                            dest,
                            field_def.name,
                        )
                        destinations, copied_keys = moved.setdefault(legacy_section, (set(), []))
                        destinations.add(dest)
                        copied_keys.append(key)
                        mutated = True
                        copied = True
                        break
                if copied:
                    break
            if field_def.name not in section:
                section[field_def.name] = _coerce_default(field_def)

        for legacy_section in cls.legacy_sections:
            if legacy_section not in cfg:
                continue
            destinations, copied_keys = moved.get(legacy_section, (set(), []))
            had_values = bool(copied_keys) or _legacy_has_values(cfg[legacy_section])
            _log_migrated(legacy_section, sorted(destinations), copied_keys)
            leftover = _section_keys(cfg[legacy_section])
            mapped = {key for field_def in cls.all_fields() for key in (field_def.legacy_keys or (field_def.name,))}
            unmapped = [k for k in leftover if k not in mapped]
            _log_removed_legacy(legacy_section, moved=bool(copied_keys), unmapped=unmapped)
            del cfg[legacy_section]
            # Empty sections are re-created by check_section every boot — deleting them
            # is in-memory cleanup only, not a config migration worth saving/logging.
            if had_values or copied_keys:
                mutated = True
            moved.pop(legacy_section, None)

    return mutated


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def migrate_legacy_maps(cfg: ConfigObj, maps) -> bool:
    """
    One-shot structural migrate: copy declared legacy INI sections into
    [extensions][[kind]][[[id]]] and optionally delete the legacy section.
    Does not require Plugin classes (hybrid config strategy).
    """
    from sickchill.plugins.legacy_maps import LegacyMap

    mutated = False
    # Defer delete so multiple maps can read the same legacy section; log once per section.
    sections_to_delete: dict[str, tuple[set[str], list[str]]] = {}  # section -> (dests, keys)
    sections_to_strip: dict[str, tuple[set[str], list[str], set[str]]] = {}  # section -> (dests, keys, mapped)

    for legacy_map in maps:
        assert isinstance(legacy_map, LegacyMap)
        kind = PluginKind(legacy_map.kind)
        section = ensure_extension_section(cfg, kind, legacy_map.plugin_id)
        legacy = cfg.get(legacy_map.legacy_section) if legacy_map.legacy_section in cfg else None
        dest = f"extensions.{legacy_map.kind}.{legacy_map.plugin_id}"
        copied_here: list[str] = []

        for field_def in legacy_map.fields:
            if field_def.name in section and section[field_def.name] not in (None, ""):
                continue
            copied = False
            if legacy is not None:
                for key in field_def.legacy_keys or (field_def.name,):
                    if key in legacy and legacy[key] not in (None, ""):
                        section[field_def.name] = legacy[key]
                        logger.debug(
                            "Plugin migrator: copied %s.%s -> %s.%s",
                            legacy_map.legacy_section,
                            key,
                            dest,
                            field_def.name,
                        )
                        copied_here.append(key)
                        mutated = True
                        copied = True
                        break
            if not copied and field_def.name not in section:
                if field_def.type == "bool":
                    section[field_def.name] = False
                elif field_def.type == "int":
                    section[field_def.name] = 0
                else:
                    section[field_def.name] = ""

        if legacy is not None and legacy_map.delete_section:
            destinations, keys = sections_to_delete.setdefault(legacy_map.legacy_section, (set(), []))
            destinations.add(dest)
            keys.extend(copied_here)
        elif legacy is not None and not legacy_map.delete_section:
            mapped = {key for field_def in legacy_map.fields for key in (field_def.legacy_keys or (field_def.name,))}
            destinations, keys, mapped_keys = sections_to_strip.setdefault(legacy_map.legacy_section, (set(), [], set()))
            destinations.add(dest)
            keys.extend(copied_here)
            mapped_keys.update(mapped)
            for field_def in legacy_map.fields:
                for key in field_def.legacy_keys or (field_def.name,):
                    if key in legacy:
                        del legacy[key]
                        mutated = True

    for section_name, (destinations, keys, _mapped) in sections_to_strip.items():
        if keys:
            _log_migrated(section_name, sorted(destinations), keys)

    for section_name, (destinations, keys) in sections_to_delete.items():
        if section_name not in cfg:
            continue
        had_values = bool(keys) or _legacy_has_values(cfg[section_name])
        if keys:
            _log_migrated(section_name, sorted(destinations), keys)
        leftover = _section_keys(cfg[section_name])
        mapped = set()
        for legacy_map in maps:
            if legacy_map.legacy_section == section_name:
                mapped.update(key for field_def in legacy_map.fields for key in (field_def.legacy_keys or (field_def.name,)))
        unmapped = [k for k in leftover if k not in mapped]
        _log_removed_legacy(section_name, moved=bool(keys), unmapped=unmapped)
        del cfg[section_name]
        # check_section / check_setting_str recreate empty legacy sections every boot;
        # scrubbing them in-memory must not force a config save or log spam.
        if had_values:
            mutated = True

    return mutated


def _coerce_settings_value(field_type: str, raw: Any) -> Any:
    """Coerce ConfigObj/settings values; ConfigObj often stores bools as 'True'/'False' strings."""
    if field_type == "bool":
        return _as_bool(raw, False)
    if field_type == "int":
        if raw in (None, ""):
            return 0
        if isinstance(raw, bool):
            return int(raw)
        # Checkbox leftovers written as strings before typing was corrected
        if str(raw).lower() in {"true", "yes", "on"}:
            return 1
        if str(raw).lower() in {"false", "no", "off"}:
            return 0
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0
    if raw is None:
        return ""
    # If a bool leaked into a str field, normalize for save_config int() callers
    if isinstance(raw, bool):
        return raw
    return raw


def sync_legacy_maps_to_settings(cfg: ConfigObj, maps) -> None:
    """Fill settings.* globals from [extensions] using declared maps (for Mako / legacy code)."""
    from sickchill import settings as sc_settings

    for legacy_map in maps:
        kind = PluginKind(legacy_map.kind)
        section = read_plugin_section(cfg, kind, legacy_map.plugin_id)
        if not section:
            continue
        for field_def in legacy_map.fields:
            if not hasattr(sc_settings, field_def.settings_attr):
                continue
            value = _coerce_settings_value(field_def.type, section.get(field_def.name))
            setattr(sc_settings, field_def.settings_attr, value)


def write_legacy_maps_from_settings(cfg: ConfigObj, maps) -> None:
    """Persist settings.* into [extensions] and drop legacy sections when allowed."""
    from sickchill import settings as sc_settings

    for legacy_map in maps:
        kind = PluginKind(legacy_map.kind)
        data = {}
        for field_def in legacy_map.fields:
            raw = getattr(sc_settings, field_def.settings_attr, None)
            value = _coerce_settings_value(field_def.type, raw)
            # Persist bools as real bools so later sync does not see 'True' strings.
            data[field_def.name] = value
        write_plugin_section(cfg, kind, legacy_map.plugin_id, data)
        if legacy_map.delete_section and legacy_map.legacy_section in cfg:
            del cfg[legacy_map.legacy_section]


def migrate_client_maps(cfg: ConfigObj, maps) -> bool:
    """
    One-shot migrate legacy client INI sections into top-level [CLIENTS][[id]].
    Defer section delete/strip until all maps for a legacy section have been applied
    so shared sources like [TORRENT] can seed every torrent client.
    """
    from sickchill.plugins.legacy_maps import LegacyMap

    mutated = False
    sections_to_delete: set[str] = set()
    sections_to_strip: dict[str, set[str]] = {}
    # legacy_section -> (CLIENTS destinations, copied legacy keys)
    moved: dict[str, tuple[set[str], list[str]]] = {}

    for legacy_map in maps:
        assert isinstance(legacy_map, LegacyMap)
        section = ensure_client_section(cfg, legacy_map.plugin_id)
        legacy = cfg.get(legacy_map.legacy_section) if legacy_map.legacy_section in cfg else None
        dest = f"CLIENTS[[{legacy_map.plugin_id}]]"

        for field_def in legacy_map.fields:
            if field_def.name in section and section[field_def.name] not in (None, ""):
                continue
            copied = False
            if legacy is not None:
                for key in field_def.legacy_keys or (field_def.name,):
                    if key in legacy and legacy[key] not in (None, ""):
                        section[field_def.name] = legacy[key]
                        logger.debug(
                            "Plugin migrator: copied %s.%s -> %s.%s",
                            legacy_map.legacy_section,
                            key,
                            dest,
                            field_def.name,
                        )
                        destinations, copied_keys = moved.setdefault(legacy_map.legacy_section, (set(), []))
                        destinations.add(dest)
                        copied_keys.append(key)
                        mutated = True
                        copied = True
                        break
            if not copied and field_def.name not in section:
                if field_def.type == "bool":
                    section[field_def.name] = False
                elif field_def.type == "int":
                    section[field_def.name] = 0
                else:
                    section[field_def.name] = ""

        if legacy is not None:
            mapped = {key for field_def in legacy_map.fields for key in (field_def.legacy_keys or (field_def.name,))}
            if legacy_map.delete_section:
                sections_to_delete.add(legacy_map.legacy_section)
            else:
                sections_to_strip.setdefault(legacy_map.legacy_section, set()).update(mapped)

    for section_name, keys in sections_to_strip.items():
        if section_name in sections_to_delete or section_name not in cfg:
            continue
        destinations, copied_keys = moved.get(section_name, (set(), []))
        if copied_keys:
            _log_migrated(section_name, sorted(destinations), copied_keys)
        legacy = cfg[section_name]
        for key in keys:
            if key in legacy:
                del legacy[key]
                mutated = True

    for section_name in sections_to_delete:
        if section_name not in cfg:
            continue
        destinations, copied_keys = moved.get(section_name, (set(), []))
        had_values = bool(copied_keys) or _legacy_has_values(cfg[section_name])
        if copied_keys:
            _log_migrated(section_name, sorted(destinations), copied_keys)
        leftover = _section_keys(cfg[section_name])
        mapped = set()
        for legacy_map in maps:
            if legacy_map.legacy_section == section_name:
                mapped.update(key for field_def in legacy_map.fields for key in (field_def.legacy_keys or (field_def.name,)))
        unmapped = [k for k in leftover if k not in mapped]
        _log_removed_legacy(section_name, moved=bool(copied_keys), unmapped=unmapped)
        del cfg[section_name]
        if had_values:
            mutated = True

    return mutated
