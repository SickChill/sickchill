"""PROVIDERS section migrate / apply / write between config.ini and live providers."""

from __future__ import annotations

import logging
from typing import Any

from configobj import ConfigObj

from sickchill.plugins.legacy_maps import ALL_LEGACY_MAPS, CLIENT_SECTION_MAPS
from sickchill.plugins.settings import (
    RETIRED_NOTIFIER_LEGACY_SECTIONS,
    _as_bool,
    _coerce_settings_value,
    _legacy_has_values,
    _section_keys,
    ensure_provider_section,
    read_provider_section,
    write_provider_section,
)

logger = logging.getLogger("sickchill.plugins.providers")

# Same hasattr list as start.py provider load/save (short keys under PROVIDERS).
PROVIDER_OPTION_FIELDS: tuple[str, ...] = (
    "enabled",
    "custom_url",
    "api_key",
    "hash",
    "digest",
    "username",
    "password",
    "passkey",
    "pin",
    "confirmed",
    "ranked",
    "engrelease",
    "only_spanish_search",
    "sorting",
    "options",
    "ratio",
    "minseed",
    "minleech",
    "freeleech",
    "search_mode",
    "search_fallback",
    "enable_daily",
    "enable_backlog",
    "cat",
    "subtitle",
    "cookies",
    "indexer",
    "categories",
    "tv_categories",
)

# Custom Newznab / TorrentRss extras stored under PROVIDERS[[id]].
CUSTOM_EXTRA_FIELDS: tuple[str, ...] = ("type", "name", "url", "key", "titleTAG")

_BOOL_FIELDS = frozenset(
    {
        "enabled",
        "confirmed",
        "ranked",
        "engrelease",
        "only_spanish_search",
        "freeleech",
        "search_fallback",
        "enable_daily",
        "enable_backlog",
        "subtitle",
    }
)
_INT_FIELDS = frozenset({"minseed", "minleech", "cat"})

_DEFAULT_CATEGORIES = "5000,5030,5040,5045,5050,5060,5070"

# Top-level config sections that are never search-provider legacy sections.
# Leftover notifier/client INI names (KODI, NMJ, XBMC, …) are UPPER with id_* keys
# and would otherwise match _looks_like_provider_section during migrate/save.
_NON_PROVIDER_SECTIONS = (
    frozenset(
        {
            "General",
            "GUI",
            "Cloudflare",
            "Shares",
            "NZBs",
            "Newzbin",
            "Newznab",
            "TorrentRss",
            "Subtitles",
            "FailedDownloads",
            "ANIDB",
            "ANIME",
            "Localization",
            "Synology",
            "NOTIFIERS",
            "CLIENTS",
            "METADATA",
            "PROVIDERS",
            "extensions",
            "TORRENT",
            "SABnzbd",
            "NZBget",
            "Blackhole",
            "XBMC",  # pre-v6 Kodi; ConfigMigrator peeks but does not delete
        }
    )
    | frozenset(item.legacy_section for item in (*ALL_LEGACY_MAPS, *CLIENT_SECTION_MAPS))
    | frozenset(RETIRED_NOTIFIER_LEGACY_SECTIONS)
)


def _field_type(name: str) -> str:
    if name in _BOOL_FIELDS:
        return "bool"
    if name in _INT_FIELDS:
        return "int"
    return "str"


def _dest_nonempty(section: dict[str, Any], key: str) -> bool:
    return key in section and section[key] not in (None, "")


def _first_party_provider_ids() -> dict[str, str]:
    """Map provider_id → legacy section name (UPPER) without instantiating Provider()."""
    from sickchill.oldbeard.providers import __all__ as provider_all, broken_providers, provider_id_for_module

    broken = set(broken_providers or [])
    result: dict[str, str] = {}
    for module_name in provider_all:
        if module_name in broken:
            continue
        provider_id = provider_id_for_module(module_name)
        if provider_id:
            result[provider_id] = provider_id.upper()
    return result


def _looks_like_provider_section(section_name: str, section) -> bool:
    """True when section is named ID and has key ``id`` or ``id_*`` (legacy provider shape)."""
    if section_name in _NON_PROVIDER_SECTIONS or not hasattr(section, "keys"):
        return False
    provider_id = section_name.lower()
    if not provider_id or provider_id != section_name.lower():
        # Section names for providers are UPPER of id; accept exact case-fold match only.
        pass
    if section_name != section_name.upper():
        return False
    keys = _section_keys(section)
    if provider_id in keys:
        return True
    prefix = provider_id + "_"
    return any(str(k).startswith(prefix) for k in keys)


def _legacy_key_to_field(provider_id: str, key: str) -> str | None:
    if key == provider_id:
        return "enabled"
    prefix = f"{provider_id}_"
    if key.startswith(prefix):
        field = key[len(prefix) :]
        return field or None
    return None


def _migrate_one_legacy_section(cfg: ConfigObj, provider_id: str, section_name: str) -> bool:
    """Copy legacy [ID] keys into PROVIDERS[[id]]; delete section. Return True if real values moved."""
    if section_name not in cfg:
        return False
    legacy = cfg[section_name]
    if not hasattr(legacy, "keys"):
        return False

    dest = ensure_provider_section(cfg, provider_id)
    copied_keys: list[str] = []
    for key in list(_section_keys(legacy)):
        field = _legacy_key_to_field(provider_id, str(key))
        if field is None:
            continue
        if field == "categories":
            # Only migrate categories when dest already marks configurable, or always store —
            # apply path gates on uses_configurable_categories.
            pass
        value = legacy[key]
        if _dest_nonempty(dest, field):
            continue
        dest[field] = value
        if value not in (None, ""):
            copied_keys.append(str(key))

    had_values = bool(copied_keys) or _legacy_has_values(legacy)
    del cfg[section_name]

    if copied_keys:
        logger.info(
            "Plugin migrator: moved [%s] -> PROVIDERS[[%s]] (%s)",
            section_name,
            provider_id,
            ", ".join(sorted(set(copied_keys))),
        )
        return True
    # Empty-only delete: silent and not mutated. Non-empty leftover (dest already filled) still needs save.
    return had_values


def _ini_blob_as_str(raw) -> str:
    """Rejoin ConfigObj list_values splits so category commas survive round-trip."""
    if raw is None:
        return ""
    if isinstance(raw, (list, tuple)):
        return ",".join(str(part) for part in raw)
    return str(raw)


def _parsed_blob_provider_ids(blob: str, ptype: str) -> list[str] | None:
    """Ids from a Newznab/TorrentRss blob, or None if any non-empty entry is unparseable."""
    if ptype == "newznab":
        from sickchill.oldbeard.providers.newznab import NewznabProvider as provider_cls
    elif ptype == "torrentrss":
        from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider as provider_cls
    else:
        return None

    ids: list[str] = []
    for piece in blob.split("!!!"):
        piece = piece.strip()
        if not piece:
            continue
        try:
            providers = provider_cls.providers_list(piece)
        except Exception:
            return None
        if not providers:
            return None
        for provider in providers:
            provider_id = provider.get_id() if provider is not None else ""
            if not provider_id:
                return None
            ids.append(provider_id)
    return ids


def _drop_legacy_blob_section(cfg: ConfigObj, section_name: str, ptype: str, data_key: str) -> bool:
    """Delete [Newznab]/[TorrentRss] when empty or every blob entry is in PROVIDERS.

    Returns True when a non-empty blob was removed (caller should persist).
    Empty-only deletes are silent and do not count as mutated.
    A leftover type= match for a different provider does not authorize deleting the blob.
    Unparseable entries keep the whole section.
    """
    if section_name not in cfg:
        return False
    section = cfg[section_name]
    raw = section.get(data_key) if hasattr(section, "get") else None
    blob = _ini_blob_as_str(raw).strip()
    if not blob:
        del cfg[section_name]
        return False
    ids = _parsed_blob_provider_ids(blob, ptype)
    if not ids:
        return False
    for provider_id in ids:
        dest = read_provider_section(cfg, provider_id)
        if str(dest.get("type") or "").lower() != ptype:
            return False
    del cfg[section_name]
    return True


def _migrate_newznab_blob(cfg: ConfigObj) -> bool:
    if "Newznab" not in cfg:
        return False
    section = cfg["Newznab"]
    raw = section.get("newznab_data") if hasattr(section, "get") else None
    blob = _ini_blob_as_str(raw)
    moved = False

    if blob:
        from sickchill.oldbeard.providers.newznab import NewznabProvider

        try:
            providers = NewznabProvider.providers_list(blob)
        except Exception:
            logger.exception("Plugin migrator: could not parse [Newznab] newznab_data")
            providers = []
        for provider in providers:
            provider_id = provider.get_id()
            if not provider_id:
                continue
            dest = read_provider_section(cfg, provider_id)
            if dest.get("type") == "newznab" or (dest and dest.get("url")):
                # Already migrated / present — do not overwrite non-empty.
                data = dict(dest)
            else:
                data = {}
            payload = {
                "type": "newznab",
                "name": provider.name,
                "url": provider.url,
                "key": getattr(provider, "key", "") or "",
                "categories": getattr(provider, "categories", "") or "",
                "enabled": bool(provider.enabled),
                "search_mode": getattr(provider, "search_mode", "episode") or "episode",
                "search_fallback": bool(getattr(provider, "search_fallback", False)),
                "enable_daily": bool(getattr(provider, "enable_daily", True)),
                "enable_backlog": bool(getattr(provider, "enable_backlog", False)),
            }
            changed = False
            for key, value in payload.items():
                if _dest_nonempty(data, key):
                    continue
                data[key] = value
                if value not in (None, "", False):
                    changed = True
            write_provider_section(cfg, provider_id, data)
            if changed or not dest:
                moved = True
        if moved:
            logger.info("Plugin migrator: moved [Newznab] newznab_data -> PROVIDERS (type=newznab)")

    dropped = _drop_legacy_blob_section(cfg, "Newznab", "newznab", "newznab_data")
    return moved or dropped


def _migrate_torrentrss_blob(cfg: ConfigObj) -> bool:
    if "TorrentRss" not in cfg:
        return False
    section = cfg["TorrentRss"]
    raw = section.get("torrentrss_data") if hasattr(section, "get") else None
    blob = _ini_blob_as_str(raw)
    moved = False

    if blob:
        from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider

        try:
            providers = TorrentRssProvider.providers_list(blob)
        except Exception:
            logger.exception("Plugin migrator: could not parse [TorrentRss] torrentrss_data")
            providers = []
        for provider in providers:
            provider_id = provider.get_id()
            if not provider_id:
                continue
            dest = read_provider_section(cfg, provider_id)
            if dest.get("type") == "torrentrss" or (dest and dest.get("url")):
                data = dict(dest)
            else:
                data = {}
            payload = {
                "type": "torrentrss",
                "name": provider.name,
                "url": provider.url,
                "cookies": getattr(provider, "cookies", "") or "",
                "titleTAG": getattr(provider, "titleTAG", "title") or "title",
                "enabled": bool(provider.enabled),
                "search_mode": getattr(provider, "search_mode", "episode") or "episode",
                "search_fallback": bool(getattr(provider, "search_fallback", False)),
                "enable_daily": bool(getattr(provider, "enable_daily", False)),
                "enable_backlog": bool(getattr(provider, "enable_backlog", False)),
            }
            changed = False
            for key, value in payload.items():
                if _dest_nonempty(data, key):
                    continue
                data[key] = value
                if value not in (None, "", False):
                    changed = True
            write_provider_section(cfg, provider_id, data)
            if changed or not dest:
                moved = True
        if moved:
            logger.info("Plugin migrator: moved [TorrentRss] torrentrss_data -> PROVIDERS (type=torrentrss)")

    dropped = _drop_legacy_blob_section(cfg, "TorrentRss", "torrentrss", "torrentrss_data")
    return moved or dropped


def migrate_provider_sections(cfg: ConfigObj) -> bool:
    """
    One-shot: legacy [ID] provider sections + Newznab/TorrentRss blobs → [PROVIDERS][[id]].
    INFO only when real values moved; empty-only deletes are silent and do not set mutated.
    Does not touch [General] (provider_order / use_nzbs / use_torrents stay there).
    """
    if cfg is None:
        return False

    mutated = False
    known = _first_party_provider_ids()

    # 1) Known first-party legacy sections
    for provider_id, section_name in list(known.items()):
        if section_name in cfg and _migrate_one_legacy_section(cfg, provider_id, section_name):
            mutated = True
        elif section_name in cfg:
            # Empty scrub path inside _migrate_one_legacy_section already deleted; no mutate.
            pass

    # Re-scan: sections that look like providers (custom leftovers / missed ids)
    for section_name in list(cfg.keys()):
        if str(section_name).startswith("#") or section_name in _NON_PROVIDER_SECTIONS:
            continue
        if section_name not in cfg:
            continue
        section = cfg[section_name]
        if not _looks_like_provider_section(str(section_name), section):
            continue
        provider_id = str(section_name).lower()
        if provider_id in known and known[provider_id] not in cfg:
            # Already handled / deleted
            continue
        if _migrate_one_legacy_section(cfg, provider_id, str(section_name)):
            mutated = True

    # 2) Newznab / TorrentRss blobs
    if _migrate_newznab_blob(cfg):
        mutated = True
    if _migrate_torrentrss_blob(cfg):
        mutated = True

    return mutated


def _peek_legacy_field(cfg: ConfigObj, provider_id: str, field: str, default: Any, kind: str) -> Any:
    """Read one legacy [ID] field without creating the section."""
    from sickchill.oldbeard.config import peek_setting_bool, peek_setting_int, peek_setting_str

    section = provider_id.upper()
    item = provider_id if field == "enabled" else f"{provider_id}_{field}"
    if kind == "bool":
        return peek_setting_bool(cfg, section, item, default)
    if kind == "int":
        return peek_setting_int(cfg, section, item, default)
    censor = field in {"password", "api_key", "passkey", "pin", "hash", "digest", "cookies", "username"}
    return peek_setting_str(cfg, section, item, default if default is not None else "", censor_log=censor)


def _section_or_peek(cfg: ConfigObj, provider, field: str, default: Any, kind: str) -> Any:
    provider_id = provider.get_id()
    section = read_provider_section(cfg, provider_id)
    if field in section and section[field] not in (None, ""):
        return _coerce_settings_value(kind, section[field])
    if field in section and kind == "bool":
        return _coerce_settings_value("bool", section[field])
    # Prefer PROVIDERS even when value is explicitly False/0
    if field in section:
        return _coerce_settings_value(kind, section[field])
    return _peek_legacy_field(cfg, provider_id, field, default, kind)


# True after apply_providers_from_cfg(..., enabled_only=False). When False, write keeps
# existing PROVIDERS fields for disabled providers so startup-enabled-only load cannot wipe them.
_providers_full_settings_applied = False
# Provider ids whose credentials/options have been applied from cfg (or posted from the UI).
_providers_settings_loaded: set[str] = set()
# After saveProviders reconciles custom Newznab/TorrentRSS lists, prune orphans of those types only.
_prune_custom_providers_on_write = False
# Type-specific prune from saveProviders when only one custom tab was posted (e.g. USE_NZBS=0).
_prune_custom_provider_types: set[str] = set()


def mark_provider_settings_loaded(provider_id: str) -> None:
    if provider_id:
        _providers_settings_loaded.add(str(provider_id))


def loaded_provider_ids() -> set[str]:
    return set(_providers_settings_loaded)


def apply_one_provider_from_cfg(cfg: ConfigObj, provider) -> None:
    """Apply [PROVIDERS][[id]] onto one live provider and mark its settings loaded."""
    if cfg is None or provider is None:
        return
    _apply_provider_enabled(cfg, provider)
    _apply_provider_options(cfg, provider)
    mark_provider_settings_loaded(provider.get_id())


def provider_settings_for_ui(provider) -> dict[str, Any]:
    """JSON-friendly live settings for filling the Providers config form."""
    if provider is None:
        return {}
    from sickchill.oldbeard.filters import hide

    data = _provider_to_section(provider)
    if hasattr(provider, "password"):
        data["password"] = hide(getattr(provider, "password", "") or "")
    for field in ("api_key", "passkey", "pin"):
        value = data.get(field)
        if value:
            data[field] = hide(value)
    return data


def _apply_provider_enabled(cfg: ConfigObj, provider) -> None:
    """Always set ``provider.enabled`` from [PROVIDERS] (legacy peek fallback)."""
    if not hasattr(provider, "enabled"):
        return
    provider_id = provider.get_id()
    section = read_provider_section(cfg, provider_id)
    if section and "enabled" in section:
        enabled = _as_bool(section.get("enabled"), False)
    else:
        enabled = _peek_legacy_field(cfg, provider_id, "enabled", False, "bool")
    can = bool(getattr(provider, "can_daily", True) or getattr(provider, "can_backlog", True))
    provider.enabled = can and enabled


def _apply_provider_options(cfg: ConfigObj, provider) -> None:
    """Push credentials/options from [PROVIDERS] (legacy peek fallback) onto one provider."""
    provider_id = provider.get_id()
    section = read_provider_section(cfg, provider_id)

    if hasattr(provider, "custom_url"):
        default = getattr(provider, "custom_url", "") or ""
        provider.custom_url = _section_or_peek(cfg, provider, "custom_url", default, "str")

    if hasattr(provider, "api_key"):
        default = getattr(provider, "api_key", "") or ""
        provider.api_key = _section_or_peek(cfg, provider, "api_key", default, "str")

    for field in ("hash", "digest", "username", "passkey", "pin", "cookies"):
        if hasattr(provider, field):
            setattr(provider, field, _section_or_peek(cfg, provider, field, "", "str"))

    if hasattr(provider, "password"):
        section = read_provider_section(cfg, provider_id)
        if "password" in section and section.get("password") not in (None, ""):
            from sickchill import settings as sc_settings
            from sickchill.oldbeard import helpers

            provider.password = helpers.decrypt(section.get("password") or "", sc_settings.ENCRYPTION_VERSION)
        else:
            # Legacy [ID] peek still decrypts via peek_setting_str (*password* item name).
            provider.password = _section_or_peek(cfg, provider, "password", "", "str")

    if hasattr(provider, "confirmed"):
        provider.confirmed = _section_or_peek(cfg, provider, "confirmed", getattr(provider, "confirmed", True), "bool")
    if hasattr(provider, "ranked"):
        provider.ranked = _section_or_peek(cfg, provider, "ranked", getattr(provider, "ranked", True), "bool")
    if hasattr(provider, "engrelease"):
        provider.engrelease = _section_or_peek(cfg, provider, "engrelease", False, "bool")
    if hasattr(provider, "only_spanish_search"):
        provider.only_spanish_search = _section_or_peek(cfg, provider, "only_spanish_search", False, "bool")
    if hasattr(provider, "sorting"):
        provider.sorting = _section_or_peek(cfg, provider, "sorting", "seeders", "str")
    if hasattr(provider, "options"):
        provider.options = _section_or_peek(cfg, provider, "options", "", "str")
    if hasattr(provider, "ratio"):
        provider.ratio = _section_or_peek(cfg, provider, "ratio", "", "str")
    if hasattr(provider, "minseed"):
        provider.minseed = _section_or_peek(cfg, provider, "minseed", getattr(provider, "minseed", 10), "int")
    if hasattr(provider, "minleech"):
        provider.minleech = _section_or_peek(cfg, provider, "minleech", getattr(provider, "minleech", 0), "int")
    if hasattr(provider, "freeleech"):
        provider.freeleech = _section_or_peek(cfg, provider, "freeleech", False, "bool")
    if hasattr(provider, "search_mode"):
        provider.search_mode = _section_or_peek(cfg, provider, "search_mode", "episode", "str")
    if hasattr(provider, "search_fallback"):
        provider.search_fallback = _section_or_peek(cfg, provider, "search_fallback", False, "bool")

    if hasattr(provider, "enable_daily"):
        raw = _section_or_peek(cfg, provider, "enable_daily", True, "bool")
        provider.enable_daily = bool(getattr(provider, "can_daily", True)) and bool(raw)
    if hasattr(provider, "enable_backlog"):
        default_bl = bool(getattr(provider, "can_backlog", False))
        raw = _section_or_peek(cfg, provider, "enable_backlog", default_bl, "bool")
        provider.enable_backlog = bool(getattr(provider, "can_backlog", True)) and bool(raw)

    if hasattr(provider, "cat"):
        provider.cat = _section_or_peek(cfg, provider, "cat", 0, "int")
    if hasattr(provider, "subtitle"):
        provider.subtitle = _section_or_peek(cfg, provider, "subtitle", False, "bool")
    if hasattr(provider, "indexer"):
        provider.indexer = _section_or_peek(cfg, provider, "indexer", "all", "str")

    if getattr(provider, "uses_configurable_categories", False):
        default_cats = getattr(provider, "categories", "") or _DEFAULT_CATEGORIES
        provider.categories = _section_or_peek(cfg, provider, "categories", default_cats, "str")

    if hasattr(provider, "tv_categories") and callable(getattr(provider, "set_tv_categories", None)):
        default_tv = getattr(provider, "tv_categories", "") or ""
        provider.set_tv_categories(_section_or_peek(cfg, provider, "tv_categories", default_tv, "str"))

    # Custom-only fields when present on the object
    if getattr(provider, "provider_type", None) is not None:
        section_type = section.get("type") if section else None
        if section_type == "newznab":
            if hasattr(provider, "url") and "url" in section:
                provider.url = section.get("url") or provider.url
            if hasattr(provider, "key") and "key" in section:
                provider.key = section.get("key") or ""
                provider.needs_auth = bool(provider.key) and provider.key != "0"
            if hasattr(provider, "name") and section.get("name"):
                provider.name = section["name"]
        elif section_type == "torrentrss":
            if hasattr(provider, "url") and "url" in section:
                provider.url = (section.get("url") or provider.url or "").rstrip("/")
            if hasattr(provider, "titleTAG") and "titleTAG" in section:
                provider.titleTAG = section.get("titleTAG") or "title"
            if hasattr(provider, "name") and section.get("name"):
                provider.name = section["name"]


def _normalize_provider_order() -> None:
    """Keep PROVIDER_ORDER as enabled-only ids that still exist (strip stale / disabled / id:flag)."""
    from sickchill import settings as sc_settings

    provider_dict: dict[str, Any] = {x.get_id(): x for x in (sc_settings.providerList or [])}
    reserved_ids = set(provider_dict)
    for custom in (sc_settings.newznab_provider_list or []) + (sc_settings.torrent_rss_provider_list or []):
        custom_id = custom.get_id()
        if custom_id and custom_id not in reserved_ids:
            provider_dict[custom_id] = custom

    normalized: list[str] = []
    for entry in sc_settings.PROVIDER_ORDER or []:
        provider_id = entry.split(":", 1)[0] if entry else ""
        if not provider_id or provider_id in normalized:
            continue
        provider = provider_dict.get(provider_id)
        if provider is not None and getattr(provider, "enabled", False):
            normalized.append(provider_id)
    sc_settings.PROVIDER_ORDER = normalized


def enabled_provider_ids_from_cfg(cfg: ConfigObj | None) -> set[str]:
    """Ids that should be instantiated at startup (enabled in [PROVIDERS] and/or PROVIDER_ORDER)."""
    from sickchill import settings as sc_settings

    ids: set[str] = set()
    for entry in sc_settings.PROVIDER_ORDER or []:
        provider_id = str(entry).split(":")[0].strip()
        if provider_id:
            ids.add(provider_id)

    if cfg is None or "PROVIDERS" not in cfg:
        return ids

    for provider_id in cfg["PROVIDERS"]:
        if str(provider_id).startswith("#"):
            continue
        section = cfg["PROVIDERS"][provider_id]
        if not hasattr(section, "get"):
            continue
        if _as_bool(section.get("enabled"), False):
            ids.add(str(provider_id))
    return ids


def apply_providers_from_cfg(cfg: ConfigObj, *, enabled_only: bool = True) -> None:
    """Push [PROVIDERS][[id]] (peek legacy fallback) onto live provider objects.

    Always sets ``.enabled``. When ``enabled_only`` (startup default), credentials/options
    are applied only for enabled providers. Disabled providers are applied on demand via
    ``apply_one_provider_from_cfg`` when selected in the Providers UI.
    """
    global _providers_full_settings_applied

    if cfg is None:
        return

    from sickchill.oldbeard.providers import sorted_provider_list

    for provider in sorted_provider_list():
        _apply_provider_enabled(cfg, provider)
        if enabled_only and not getattr(provider, "enabled", False):
            continue
        _apply_provider_options(cfg, provider)
        mark_provider_settings_loaded(provider.get_id())

    _providers_full_settings_applied = not enabled_only
    _normalize_provider_order()


def _provider_to_section(provider) -> dict[str, Any]:
    from sickchill import settings as sc_settings
    from sickchill.oldbeard import helpers

    data: dict[str, Any] = {}
    if hasattr(provider, "enabled"):
        data["enabled"] = bool(provider.enabled)

    # Custom type markers
    from sickchill.oldbeard.providers.newznab import NewznabProvider
    from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider

    if isinstance(provider, NewznabProvider):
        data["type"] = "newznab"
        data["name"] = provider.name
        data["url"] = provider.url
        data["key"] = getattr(provider, "key", "") or ""
        if getattr(provider, "uses_configurable_categories", False):
            data["categories"] = getattr(provider, "categories", "") or ""
    elif isinstance(provider, TorrentRssProvider):
        data["type"] = "torrentrss"
        data["name"] = provider.name
        data["url"] = provider.url
        data["cookies"] = getattr(provider, "cookies", "") or ""
        data["titleTAG"] = getattr(provider, "titleTAG", "title") or "title"

    if hasattr(provider, "custom_url"):
        data["custom_url"] = provider.custom_url
    if hasattr(provider, "indexer"):
        data["indexer"] = provider.indexer
    if getattr(provider, "uses_configurable_categories", False) and "categories" not in data:
        data["categories"] = getattr(provider, "categories", "") or ""

    for field in ("digest", "hash", "api_key", "username", "passkey", "pin", "sorting", "options", "ratio", "search_mode", "cookies"):
        if field == "cookies" and "cookies" in data:
            continue
        if hasattr(provider, field):
            data[field] = getattr(provider, field)

    if hasattr(provider, "password"):
        data["password"] = helpers.encrypt(provider.password, sc_settings.ENCRYPTION_VERSION)

    for field in (
        "confirmed",
        "ranked",
        "engrelease",
        "only_spanish_search",
        "freeleech",
        "search_fallback",
        "subtitle",
    ):
        if hasattr(provider, field):
            data[field] = bool(getattr(provider, field))

    if hasattr(provider, "enable_daily"):
        data["enable_daily"] = bool(provider.enable_daily and getattr(provider, "can_daily", True))
    if hasattr(provider, "enable_backlog"):
        data["enable_backlog"] = bool(provider.enable_backlog and getattr(provider, "can_backlog", True))
    if hasattr(provider, "minseed"):
        data["minseed"] = int(provider.minseed)
    if hasattr(provider, "minleech"):
        data["minleech"] = int(provider.minleech)
    if hasattr(provider, "cat"):
        data["cat"] = int(provider.cat)
    if hasattr(provider, "tv_categories"):
        data["tv_categories"] = getattr(provider, "tv_categories", "") or ""

    return data


def write_providers_to_cfg(cfg: ConfigObj) -> None:
    """Persist live providers into [PROVIDERS]; drop leftover legacy [ID] sections.

    Built-in [PROVIDERS][[id]] sections are never deleted just because that provider
    is not in memory (startup loads enabled-only). Settings for providers that have
    not been loaded are merged (enabled flag only). Custom Newznab/TorrentRSS sections
    are pruned only after saveProviders reconciles the live custom lists, or after a
    full Providers-UI load. Legacy [Newznab]/[TorrentRss] blobs are dropped when empty
    or when every blob entry is already a matching PROVIDERS[[id]]; unparsed leftover
    blobs stay even if other customs of that type exist.
    """
    if cfg is None:
        return

    from sickchill import settings as sc_settings
    from sickchill.oldbeard.providers import sorted_provider_list

    builtin_ids = set(_first_party_provider_ids())
    seen_ids: set[str] = set()
    for provider in sorted_provider_list():
        provider_id = provider.get_id()
        if not provider_id:
            continue
        seen_ids.add(provider_id)
        loaded = provider_id in _providers_settings_loaded or _providers_full_settings_applied
        if not loaded:
            # Keep existing INI credentials; only persist the live enabled flag.
            existing = read_provider_section(cfg, provider_id)
            if existing:
                data = dict(existing)
                if hasattr(provider, "enabled"):
                    data["enabled"] = bool(provider.enabled)
                write_provider_section(cfg, provider_id, data)
                continue
        write_provider_section(cfg, provider_id, _provider_to_section(provider))

    # Never drop built-in config. Only prune custom type=newznab/torrentrss after a full UI load or
    # a saveProviders reconcile for that type (deleted customs are then absent from the live lists).
    live_custom_ids = {p.get_id() for p in (sc_settings.newznab_provider_list or []) + (sc_settings.torrent_rss_provider_list or []) if p}
    prune_all_custom = _providers_full_settings_applied or _prune_custom_providers_on_write
    if "PROVIDERS" in cfg and hasattr(cfg["PROVIDERS"], "keys"):
        for provider_id in list(cfg["PROVIDERS"].keys()):
            if str(provider_id).startswith("#"):
                continue
            if provider_id in builtin_ids:
                continue
            section = cfg["PROVIDERS"][provider_id]
            ptype = str(section.get("type") or "").lower() if hasattr(section, "get") else ""
            if ptype in {"newznab", "torrentrss"} and provider_id not in live_custom_ids and (prune_all_custom or ptype in _prune_custom_provider_types):
                del cfg["PROVIDERS"][provider_id]

    # Remove leftover legacy per-provider sections for known ids
    for provider_id in list(seen_ids) + list(_first_party_provider_ids()):
        section_name = provider_id.upper()
        if section_name in cfg and section_name not in _NON_PROVIDER_SECTIONS:
            del cfg[section_name]

    # Also scrub any remaining provider-shaped top-level sections
    for section_name in list(cfg.keys()):
        if str(section_name).startswith("#") or section_name in _NON_PROVIDER_SECTIONS:
            continue
        if _looks_like_provider_section(str(section_name), cfg[section_name]):
            del cfg[section_name]

    _drop_legacy_blob_section(cfg, "Newznab", "newznab", "newznab_data")
    _drop_legacy_blob_section(cfg, "TorrentRss", "torrentrss", "torrentrss_data")


def custom_providers_from_cfg(cfg: ConfigObj, enabled_ids: set[str] | None = None) -> tuple[list, list]:
    """Build newznab / torrentrss provider lists from PROVIDERS entries with type=…

    When ``enabled_ids`` is set, only those custom providers are constructed (startup).
    """
    from sickchill.oldbeard.providers.newznab import NewznabProvider
    from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider

    newznab: list = []
    torrentrss: list = []
    if cfg is None or "PROVIDERS" not in cfg:
        return newznab, torrentrss

    providers_root = cfg["PROVIDERS"]
    for provider_id in list(providers_root.keys()):
        if str(provider_id).startswith("#"):
            continue
        section = providers_root[provider_id]
        if not hasattr(section, "get"):
            continue
        ptype = str(section.get("type") or "").lower()
        if ptype not in {"newznab", "torrentrss"}:
            continue
        if enabled_ids is not None and str(provider_id) not in enabled_ids:
            continue
        name = section.get("name") or provider_id
        if ptype == "newznab":
            provider = NewznabProvider(
                name,
                section.get("url") or "",
                key=section.get("key") or "0",
                categories=section.get("categories") or "5030,5040",
                search_mode=section.get("search_mode") or "episode",
                search_fallback=_as_bool(section.get("search_fallback"), False),
                enable_daily=_as_bool(section.get("enable_daily"), True),
                enable_backlog=_as_bool(section.get("enable_backlog"), False),
            )
            provider.enabled = _as_bool(section.get("enabled"), False)
            newznab.append(provider)
        elif ptype == "torrentrss":
            provider = TorrentRssProvider(
                name,
                section.get("url") or "",
                cookies=section.get("cookies") or "",
                titleTAG=section.get("titleTAG") or "title",
                search_mode=section.get("search_mode") or "episode",
                search_fallback=_as_bool(section.get("search_fallback"), False),
                enable_daily=_as_bool(section.get("enable_daily"), False),
                enable_backlog=_as_bool(section.get("enable_backlog"), False),
            )
            provider.enabled = _as_bool(section.get("enabled"), False)
            torrentrss.append(provider)
    return newznab, torrentrss


def providers_section_has_customs(cfg: ConfigObj) -> bool:
    if cfg is None or "PROVIDERS" not in cfg:
        return False
    for provider_id in cfg["PROVIDERS"]:
        if str(provider_id).startswith("#"):
            continue
        section = cfg["PROVIDERS"][provider_id]
        if hasattr(section, "get") and str(section.get("type") or "").lower() in {"newznab", "torrentrss"}:
            return True
    return False
