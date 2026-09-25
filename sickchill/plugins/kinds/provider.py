from __future__ import annotations

from typing import Any, ClassVar

from sickchill.plugins.api import Plugin, PluginKind
from sickchill.plugins.settings import _as_bool, _coerce_settings_value


class ProviderPlugin(Plugin):
    kind: ClassVar[PluginKind] = PluginKind.PROVIDER
    # Module basename under sickchill.oldbeard.providers (may differ from id, e.g. jackett → jackett_sc).
    provider_module: ClassVar[str] = ""

    def apply_to_provider(self, provider: Any) -> None:
        """Copy ctx settings onto a live GenericProvider instance (hasattr-gated)."""
        data = dict(self.ctx.settings)
        if not data:
            return

        if "enabled" in data and hasattr(provider, "enabled"):
            can = bool(getattr(provider, "can_daily", True) or getattr(provider, "can_backlog", True))
            provider.enabled = can and _as_bool(data.get("enabled"), False)

        for key, raw in data.items():
            if key in {"enabled", "type", "name"}:
                continue
            if key == "categories" and not getattr(provider, "uses_configurable_categories", False):
                continue
            if not hasattr(provider, key):
                continue
            if key in _BOOL_KEYS:
                value = _coerce_settings_value("bool", raw)
                if key == "enable_daily":
                    value = bool(getattr(provider, "can_daily", True)) and value
                elif key == "enable_backlog":
                    value = bool(getattr(provider, "can_backlog", True)) and value
                setattr(provider, key, value)
            elif key in _INT_KEYS:
                setattr(provider, key, _coerce_settings_value("int", raw))
            else:
                setattr(provider, key, "" if raw is None else raw)

    def provider(self) -> Any:
        """Instantiate the wrapped oldbeard provider and apply ctx settings."""
        import importlib

        module_name = self.provider_module or self.id
        mod = importlib.import_module(f"sickchill.oldbeard.providers.{module_name}")
        instance = mod.Provider()
        self.apply_to_provider(instance)
        return instance


_BOOL_KEYS = frozenset(
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
_INT_KEYS = frozenset({"minseed", "minleech", "cat"})
