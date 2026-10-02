"""Non-destructive settings sync helpers for ClientPlugins that read settings.*."""

from __future__ import annotations

from typing import Any

from sickchill.plugins.settings import _as_bool, read_client_section


def reload_client_ctx(plugin) -> None:
    """Refresh plugin.ctx from [CLIENTS][[id]] (or leave unchanged on failure)."""
    try:
        from sickchill import settings
        from sickchill.plugins.manager import plugin_manager

        cfg = plugin_manager._cfg or settings.CFG
        if cfg is None:
            return
        data = read_client_section(cfg, plugin.id)
        if not data:
            return
        plugin.ctx._data.clear()
        plugin.ctx._data.update(data)
    except Exception:
        pass


def set_if_present(module: Any, attr: str, value: Any, *, as_bool: bool = False, as_int: bool = False, default_int: int = 0) -> None:
    """Set settings attr only when value is non-empty (unless bool/int explicitly provided)."""
    if value is None or value == "":
        return
    if as_bool:
        setattr(module, attr, _as_bool(value, False))
    elif as_int:
        try:
            setattr(module, attr, int(value))
        except (TypeError, ValueError):
            setattr(module, attr, default_int)
    else:
        setattr(module, attr, value)
