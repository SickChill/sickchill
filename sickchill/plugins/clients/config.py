"""CLIENTS section sync between config.ini and settings.* globals."""

from __future__ import annotations

from typing import Any

from configobj import ConfigObj

from sickchill.plugins.legacy_maps import TORRENT_CLIENT_IDS
from sickchill.plugins.settings import (
    _coerce_settings_value,
    read_client_section,
    write_client_section,
)

_TORRENT_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("host", "TORRENT_HOST", "str"),
    ("username", "TORRENT_USERNAME", "str"),
    ("password", "TORRENT_PASSWORD", "str"),
    ("path", "TORRENT_PATH", "str"),
    ("path_incomplete", "TORRENT_PATH_INCOMPLETE", "str"),
    ("label", "TORRENT_LABEL", "str"),
    ("label_anime", "TORRENT_LABEL_ANIME", "str"),
    ("paused", "TORRENT_PAUSED", "bool"),
    ("seed_time", "TORRENT_SEED_TIME", "int"),
    ("verify_cert", "TORRENT_VERIFY_CERT", "bool"),
    ("rpcurl", "TORRENT_RPCURL", "str"),
    ("high_bandwidth", "TORRENT_HIGH_BANDWIDTH", "bool"),
    ("auth_type", "TORRENT_AUTH_TYPE", "str"),
)

_SAB_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("username", "SAB_USERNAME", "str"),
    ("password", "SAB_PASSWORD", "str"),
    ("apikey", "SAB_APIKEY", "str"),
    ("category", "SAB_CATEGORY", "str"),
    ("category_backlog", "SAB_CATEGORY_BACKLOG", "str"),
    ("category_anime", "SAB_CATEGORY_ANIME", "str"),
    ("category_anime_backlog", "SAB_CATEGORY_ANIME_BACKLOG", "str"),
    ("host", "SAB_HOST", "str"),
    ("forced", "SAB_FORCED", "bool"),
)

_NZBGET_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("username", "NZBGET_USERNAME", "str"),
    ("password", "NZBGET_PASSWORD", "str"),
    ("category", "NZBGET_CATEGORY", "str"),
    ("category_backlog", "NZBGET_CATEGORY_BACKLOG", "str"),
    ("category_anime", "NZBGET_CATEGORY_ANIME", "str"),
    ("category_anime_backlog", "NZBGET_CATEGORY_ANIME_BACKLOG", "str"),
    ("host", "NZBGET_HOST", "str"),
    ("use_https", "NZBGET_USE_HTTPS", "bool"),
    ("priority", "NZBGET_PRIORITY", "int"),
)

_DSM_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("host", "SYNOLOGY_DSM_HOST", "str"),
    ("username", "SYNOLOGY_DSM_USERNAME", "str"),
    ("password", "SYNOLOGY_DSM_PASSWORD", "str"),
    ("path", "SYNOLOGY_DSM_PATH", "str"),
)

_LEGACY_CLIENT_SECTIONS = ("TORRENT", "SABnzbd", "NZBget", "Blackhole")
# DSM keys plus use_synoindex (owned by [NOTIFIERS][[synoindex]]).
_DSM_KEYS = ("host", "username", "password", "path", "use_synoindex")


def _apply_section_to_settings(section: dict[str, Any], fields: tuple[tuple[str, str, str], ...]) -> None:
    from sickchill import settings as sc_settings

    if not section:
        return
    for name, attr, field_type in fields:
        if name not in section:
            continue
        if not hasattr(sc_settings, attr):
            continue
        setattr(sc_settings, attr, _coerce_settings_value(field_type, section.get(name)))


def _settings_to_section(fields: tuple[tuple[str, str, str], ...], *, include: set[str] | None = None) -> dict[str, Any]:
    from sickchill import settings as sc_settings

    data: dict[str, Any] = {}
    for name, attr, field_type in fields:
        if include is not None and name not in include:
            continue
        raw = getattr(sc_settings, attr, None)
        data[name] = _coerce_settings_value(field_type, raw)
    return data


def _merge_client_section(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Prefer incoming values, but do not blank existing CLIENTS keys with empty settings.*."""
    merged = dict(existing or {})
    for key, value in incoming.items():
        if value in (None, "") and merged.get(key) not in (None, ""):
            continue
        merged[key] = value
    return merged


def sync_clients_from_settings(cfg: ConfigObj) -> None:
    """Push [CLIENTS] into settings.* for Mako / snatch / legacy client classes."""
    from sickchill import settings as sc_settings

    # Blackhole serves both NZB and torrent methods with independent dirs.
    blackhole = read_client_section(cfg, "blackhole")
    if blackhole:
        if blackhole.get("nzb_dir") not in (None, ""):
            sc_settings.NZB_DIR = _coerce_settings_value("str", blackhole.get("nzb_dir"))
        if blackhole.get("torrent_dir") not in (None, ""):
            sc_settings.TORRENT_DIR = _coerce_settings_value("str", blackhole.get("torrent_dir"))

    _apply_section_to_settings(read_client_section(cfg, "sabnzbd"), _SAB_FIELDS)
    _apply_section_to_settings(read_client_section(cfg, "nzbget"), _NZBGET_FIELDS)

    download_station = read_client_section(cfg, "download_station")
    _apply_section_to_settings(download_station, _DSM_FIELDS)

    method = getattr(sc_settings, "TORRENT_METHOD", None) or ""
    if method == "download_station":
        # Torrent Search tab binds torrent_host etc. — mirror DSM keys only (not qbit leftovers).
        if download_station:
            if download_station.get("host") not in (None, ""):
                sc_settings.TORRENT_HOST = _coerce_settings_value("str", download_station.get("host"))
            if download_station.get("username") not in (None, ""):
                sc_settings.TORRENT_USERNAME = _coerce_settings_value("str", download_station.get("username"))
            if download_station.get("password") not in (None, ""):
                sc_settings.TORRENT_PASSWORD = _coerce_settings_value("str", download_station.get("password"))
            if download_station.get("path") not in (None, ""):
                sc_settings.TORRENT_PATH = _coerce_settings_value("str", download_station.get("path"))
    elif method and method != "blackhole" and method in TORRENT_CLIENT_IDS:
        _apply_section_to_settings(read_client_section(cfg, method), _TORRENT_FIELDS)

    nzb_method = getattr(sc_settings, "NZB_METHOD", None) or ""
    # Do not overwrite TORRENT_* when an actual torrent client (qbit/transmission/…) is active.
    torrent_client_active = bool(method) and method not in ("blackhole", "download_station") and method in TORRENT_CLIENT_IDS
    if nzb_method == "download_station" and not torrent_client_active and download_station:
        # NZB DS with no competing torrent client: expose host on TORRENT_* for shared paths.
        if download_station.get("host") not in (None, ""):
            sc_settings.TORRENT_HOST = _coerce_settings_value("str", download_station.get("host"))
        if download_station.get("username") not in (None, ""):
            sc_settings.TORRENT_USERNAME = _coerce_settings_value("str", download_station.get("username"))
        if download_station.get("password") not in (None, ""):
            sc_settings.TORRENT_PASSWORD = _coerce_settings_value("str", download_station.get("password"))
        if download_station.get("path") not in (None, ""):
            sc_settings.TORRENT_PATH = _coerce_settings_value("str", download_station.get("path"))


def write_clients_to_cfg(cfg: ConfigObj) -> None:
    """Persist settings.* into [CLIENTS] and drop migratable legacy client sections."""
    from sickchill import settings as sc_settings

    write_client_section(
        cfg,
        "blackhole",
        _merge_client_section(
            read_client_section(cfg, "blackhole"),
            {
                "nzb_dir": getattr(sc_settings, "NZB_DIR", None) or "",
                "torrent_dir": getattr(sc_settings, "TORRENT_DIR", None) or "",
            },
        ),
    )
    write_client_section(cfg, "sabnzbd", _merge_client_section(read_client_section(cfg, "sabnzbd"), _settings_to_section(_SAB_FIELDS)))
    write_client_section(cfg, "nzbget", _merge_client_section(read_client_section(cfg, "nzbget"), _settings_to_section(_NZBGET_FIELDS)))

    method = getattr(sc_settings, "TORRENT_METHOD", None) or ""
    nzb_method = getattr(sc_settings, "NZB_METHOD", None) or ""
    # download_station stores only DSM keys (host/user/pass/path). Do not copy
    # unrelated TORRENT_* leftovers (labels, seed_time, incomplete path, …).
    ds_data = _settings_to_section(_DSM_FIELDS)
    if method == "download_station":
        # Torrent tab is authoritative while DS is the torrent method.
        torrent_dsm = _settings_to_section(_TORRENT_FIELDS, include={"host", "username", "password", "path"})
        for name, value in torrent_dsm.items():
            if value not in (None, ""):
                ds_data[name] = value
    elif nzb_method == "download_station":
        # Fill empty DSM keys from TORRENT_* only when NZB tab owns DS.
        torrent_dsm = _settings_to_section(_TORRENT_FIELDS, include={"host", "username", "password", "path"})
        for name, value in torrent_dsm.items():
            if ds_data.get(name) in (None, "") and value not in (None, ""):
                ds_data[name] = value
    # Replace section with DSM-only keys (drop polluted qbit fields if present).
    existing_ds = {k: v for k, v in read_client_section(cfg, "download_station").items() if k in {"host", "username", "password", "path"}}
    write_client_section(cfg, "download_station", _merge_client_section(existing_ds, ds_data))

    if method and method not in ("blackhole", "download_station") and method in TORRENT_CLIENT_IDS:
        include = {name for name, _, _ in _TORRENT_FIELDS[:10]}
        if method == "transmission":
            include.update({"rpcurl", "high_bandwidth"})
        elif method == "rtorrent":
            include.add("auth_type")
        write_client_section(
            cfg,
            method,
            _merge_client_section(read_client_section(cfg, method), _settings_to_section(_TORRENT_FIELDS, include=include)),
        )

    for section_name in _LEGACY_CLIENT_SECTIONS:
        if section_name in cfg:
            del cfg[section_name]

    if "Synology" in cfg:
        synology = cfg["Synology"]
        for key in _DSM_KEYS:
            if key in synology:
                del synology[key]
        # Drop empty leftover [Synology] so save does not keep recreating a shell section.
        if not [k for k in synology if not str(k).startswith("#")]:
            del cfg["Synology"]
