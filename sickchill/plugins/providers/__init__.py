"""First-party search provider plugins.

Dynamic registration: import each ``oldbeard.providers.<mod>``, build a
``ProviderPlugin`` subclass with ``id`` from ``Provider().get_id()``.
"""

from __future__ import annotations

import importlib
import logging
import sys

logger = logging.getLogger("sickchill.plugins.providers")

# Populated from oldbeard.providers.__all__ at load time (excluding broken).
FIRST_PARTY_PROVIDER_MODULES: tuple[str, ...] = ()


def _provider_modules() -> tuple[str, ...]:
    from sickchill.oldbeard.providers import __all__ as provider_all, broken_providers

    broken = set(broken_providers or [])
    return tuple(name for name in provider_all if name not in broken)


def load_first_party_providers() -> None:
    """Import oldbeard provider modules and @register thin ProviderPlugin wrappers."""
    global FIRST_PARTY_PROVIDER_MODULES

    from sickchill.plugins.api import register
    from sickchill.plugins.kinds.provider import ProviderPlugin

    FIRST_PARTY_PROVIDER_MODULES = _provider_modules()
    registered_ids: set[str] = set()

    for module_name in FIRST_PARTY_PROVIDER_MODULES:
        full = f"sickchill.oldbeard.providers.{module_name}"
        try:
            if full in sys.modules:
                mod = importlib.reload(sys.modules[full])
            else:
                mod = importlib.import_module(full)
            provider_cls = getattr(mod, "Provider", None)
            if provider_cls is None:
                logger.warning("Provider module %s has no Provider class", module_name)
                continue
            sample = provider_cls()
            provider_id = sample.get_id()
            if not provider_id or provider_id in registered_ids:
                continue
            registered_ids.add(provider_id)

            plugin_cls = type(
                f"{provider_id.title().replace('_', '')}ProviderPlugin",
                (ProviderPlugin,),
                {
                    "id": provider_id,
                    "name": sample.name,
                    "provider_module": module_name,
                    "version": "1.0.0",
                },
            )
            register(plugin_cls)
        except Exception as error:
            logger.exception("Failed to load provider plugin %s: %s", module_name, error)
