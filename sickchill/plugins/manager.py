from __future__ import annotations

import logging
from typing import Any

from configobj import ConfigObj

from sickchill.plugins.api import Plugin, PluginKind
from sickchill.plugins.loader import discover_classes
from sickchill.plugins.settings import (
    migrate_legacy_sections,
    read_client_section,
    read_metadata_section,
    read_plugin_section,
    write_client_section,
    write_metadata_section,
    write_plugin_section,
)

logger = logging.getLogger("sickchill.plugins.manager")


class PluginManager:
    def __init__(self) -> None:
        self._classes: list[type[Plugin]] = []
        self._instances: dict[tuple[str, str], Plugin] = {}
        self._cfg: ConfigObj | None = None
        self._data_dir: str | None = None
        self._plugins_dir: str | None = None

    def discover(self, data_dir: str | None = None, plugins_dir: str | None = None) -> None:
        self._data_dir = data_dir
        self._plugins_dir = plugins_dir
        self._classes = discover_classes(data_dir=data_dir, plugins_dir=plugins_dir)
        # Drop cached instances for classes that disappeared
        valid = {(cls.kind.value, cls.id) for cls in self._classes}
        for key in list(self._instances):
            if key not in valid:
                self._instances.pop(key, None)
        logger.debug("Discovered %s plugin class(es)", len(self._classes))

    def classes(self, kind: PluginKind | None = None) -> list[type[Plugin]]:
        if kind is None:
            return list(self._classes)
        return [cls for cls in self._classes if cls.kind == kind]

    def migrate_settings(self, cfg: ConfigObj) -> bool:
        self._cfg = cfg
        return migrate_legacy_sections(cfg, self._classes)

    def _read_section(self, kind: PluginKind, plugin_id: str) -> dict[str, Any]:
        if self._cfg is None:
            return {}
        if kind == PluginKind.CLIENT:
            return read_client_section(self._cfg, plugin_id)
        if kind == PluginKind.METADATA:
            return read_metadata_section(self._cfg, plugin_id)
        return read_plugin_section(self._cfg, kind, plugin_id)

    def _writer(self, kind: PluginKind, plugin_id: str, data: dict[str, Any]) -> None:
        if self._cfg is None:
            return
        if kind == PluginKind.CLIENT:
            write_client_section(self._cfg, plugin_id, data)
        elif kind == PluginKind.METADATA:
            write_metadata_section(self._cfg, plugin_id, data)
        else:
            write_plugin_section(self._cfg, kind, plugin_id, data)

    def _is_enabled(self, cls: type[Plugin]) -> bool:
        if self._cfg is None:
            return False
        section = self._read_section(cls.kind, cls.id)
        value = section.get("enabled", False)
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}

    def instance(self, kind: PluginKind, plugin_id: str, *, require_enabled: bool | None = None) -> Plugin | None:
        cls = next((c for c in self._classes if c.kind == kind and c.id == plugin_id), None)
        if cls is None:
            return None
        # Clients are selected via TORRENT_METHOD / NZB_METHOD; metadata generators are always available.
        if require_enabled is None:
            require_enabled = kind not in (PluginKind.CLIENT, PluginKind.METADATA)
        if require_enabled and not self._is_enabled(cls):
            return None

        key = (kind.value, plugin_id)
        existing = self._instances.get(key)
        if existing is not None:
            return existing

        data = self._read_section(kind, plugin_id)
        from sickchill.plugins.api import PluginContext

        ctx = PluginContext(kind=kind, plugin_id=plugin_id, _data=dict(data), _writer=self._writer)
        plugin = cls(ctx)
        self._instances[key] = plugin
        return plugin

    def get(self, kind: PluginKind, plugin_id: str) -> Plugin | None:
        """Always build if the class exists (no enabled gate)."""
        return self.instance(kind, plugin_id, require_enabled=False)

    def enabled(self, kind: PluginKind) -> list[Plugin]:
        result: list[Plugin] = []
        for cls in self.classes(kind):
            plugin = self.instance(kind, cls.id)
            if plugin is not None:
                result.append(plugin)
        return result


plugin_manager = PluginManager()
