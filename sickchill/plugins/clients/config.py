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
# DSM keys plus use_synoindex (owned by extensions[[notifiers]][[[synoindex]]]).
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


def sync_clients_from_settings(cfg: ConfigObj) -> None:
    """Push [CLIENTS] into settings.* for Mako / snatch / legacy client classes."""
    from sickchill import settings as sc_settings

    blackhole = read_client_section(cfg, "blackhole")
    if blackhole:
        if "nzb_dir" in blackhole:
            sc_settings.NZB_DIR = blackhole.get("nzb_dir") or ""
        if "torrent_dir" in blackhole:
            sc_settings.TORRENT_DIR = blackhole.get("torrent_dir") or ""

    _apply_section_to_settings(read_client_section(cfg, "sabnzbd"), _SAB_FIELDS)
    _apply_section_to_settings(read_client_section(cfg, "nzbget"), _NZBGET_FIELDS)

    download_station = read_client_section(cfg, "download_station")
    _apply_section_to_settings(download_station, _DSM_FIELDS)

    method = getattr(sc_settings, "TORRENT_METHOD", None) or ""
    if method == "download_station":
        _apply_section_to_settings(download_station, _TORRENT_FIELDS)
    elif method and method != "blackhole" and method in TORRENT_CLIENT_IDS:
        _apply_section_to_settings(read_client_section(cfg, method), _TORRENT_FIELDS)

    nzb_method = getattr(sc_settings, "NZB_METHOD", None) or ""
    if nzb_method == "download_station" and download_station:
        # Keep TORRENT_* mirrors available when NZB uses Download Station.
        _apply_section_to_settings(download_station, _TORRENT_FIELDS)


def write_clients_to_cfg(cfg: ConfigObj) -> None:
    """Persist settings.* into [CLIENTS] and drop migratable legacy client sections."""
    from sickchill import settings as sc_settings

    write_client_section(
        cfg,
        "blackhole",
        {
            "nzb_dir": getattr(sc_settings, "NZB_DIR", None) or "",
            "torrent_dir": getattr(sc_settings, "TORRENT_DIR", None) or "",
        },
    )
    write_client_section(cfg, "sabnzbd", _settings_to_section(_SAB_FIELDS))
    write_client_section(cfg, "nzbget", _settings_to_section(_NZBGET_FIELDS))

    method = getattr(sc_settings, "TORRENT_METHOD", None) or ""
    nzb_method = getattr(sc_settings, "NZB_METHOD", None) or ""
    ds_data = _settings_to_section(_DSM_FIELDS)
    # Prefer DSM values; fill gaps from TORRENT_* when Download Station is active.
    if method == "download_station" or nzb_method == "download_station":
        torrent_shared = _settings_to_section(_TORRENT_FIELDS, include={name for name, _, _ in _TORRENT_FIELDS[:10]})
        for name, value in torrent_shared.items():
            if name in ds_data and ds_data[name] not in (None, ""):
                continue
            if value not in (None, ""):
                ds_data[name] = value
    write_client_section(cfg, "download_station", ds_data)

    if method and method not in ("blackhole", "download_station") and method in TORRENT_CLIENT_IDS:
        include = {name for name, _, _ in _TORRENT_FIELDS[:10]}
        if method == "transmission":
            include.update({"rpcurl", "high_bandwidth"})
        elif method == "rtorrent":
            include.add("auth_type")
        write_client_section(cfg, method, _settings_to_section(_TORRENT_FIELDS, include=include))

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
