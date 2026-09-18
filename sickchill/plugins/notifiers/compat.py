from __future__ import annotations

from typing import Any

from sickchill import settings
from sickchill.plugins.api import PluginKind
from sickchill.plugins.settings import read_plugin_section, write_plugin_section


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def discord_config_from_settings() -> dict[str, Any]:
    return {
        "enabled": bool(settings.USE_DISCORD),
        "webhook": settings.DISCORD_WEBHOOK or "",
        "bot_name": settings.DISCORD_NAME or "SickChill",
        "avatar_url": settings.DISCORD_AVATAR_URL or "",
        "tts": bool(settings.DISCORD_TTS),
        "notify_snatch": bool(settings.DISCORD_NOTIFY_SNATCH),
        "notify_download": bool(settings.DISCORD_NOTIFY_DOWNLOAD),
        "notify_subtitle_download": bool(getattr(settings, "DISCORD_NOTIFY_SUBTITLEDOWNLOAD", False)),
    }


def sync_discord_settings_from_cfg(cfg=None) -> None:
    """Overlay Discord runtime settings from [extensions][[notifiers]][[[discord]]]."""
    cfg = cfg if cfg is not None else settings.CFG
    if cfg is None:
        return
    section = read_plugin_section(cfg, PluginKind.NOTIFIER, "discord")
    if not section:
        return
    settings.USE_DISCORD = _as_bool(section.get("enabled"), False)
    settings.DISCORD_WEBHOOK = section.get("webhook") or ""
    settings.DISCORD_NAME = section.get("bot_name") or "SickChill"
    settings.DISCORD_AVATAR_URL = section.get("avatar_url") or settings.DISCORD_AVATAR_URL
    settings.DISCORD_TTS = _as_bool(section.get("tts"), False)
    settings.DISCORD_NOTIFY_SNATCH = _as_bool(section.get("notify_snatch"), False)
    settings.DISCORD_NOTIFY_DOWNLOAD = _as_bool(section.get("notify_download"), False)
    if hasattr(settings, "DISCORD_NOTIFY_SUBTITLEDOWNLOAD"):
        settings.DISCORD_NOTIFY_SUBTITLEDOWNLOAD = _as_bool(section.get("notify_subtitle_download"), False)


def write_discord_settings_to_cfg(cfg) -> None:
    """Persist Discord settings into extensions and drop legacy [Discord]."""
    write_plugin_section(cfg, PluginKind.NOTIFIER, "discord", discord_config_from_settings())
    if "Discord" in cfg:
        del cfg["Discord"]


def get_discord_runtime_config() -> dict[str, Any]:
    """Prefer live plugin context; fall back to settings globals."""
    try:
        from sickchill.plugins.manager import plugin_manager

        plugin = plugin_manager.instance(PluginKind.NOTIFIER, "discord")
        if plugin is not None:
            return {
                "enabled": True,
                "webhook": plugin.ctx.get("webhook") or "",
                "bot_name": plugin.ctx.get("bot_name") or "SickChill",
                "avatar_url": plugin.ctx.get("avatar_url") or "",
                "tts": bool(plugin.ctx.get("tts")),
                "notify_snatch": bool(plugin.ctx.get("notify_snatch")),
                "notify_download": bool(plugin.ctx.get("notify_download")),
                "notify_subtitle_download": bool(plugin.ctx.get("notify_subtitle_download")),
            }
    except Exception:
        pass
    return discord_config_from_settings()
