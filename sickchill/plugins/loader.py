from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import logging
import sys
from pathlib import Path

from sickchill.plugins.api import Plugin, PluginKind, registered_classes

logger = logging.getLogger("sickchill.plugins.loader")


def _iter_entry_point_classes(kind: PluginKind) -> list[type[Plugin]]:
    found: list[type[Plugin]] = []
    group = f"sickchill.{kind.value}"
    try:
        eps = importlib.metadata.entry_points()
        # Python 3.10+: select(); older returns dict-like
        selected = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])
    except Exception as error:
        logger.debug("entry_points lookup failed for %s: %s", group, error)
        return found

    for ep in selected:
        try:
            obj = ep.load()
        except Exception as error:
            logger.warning("Failed to load entry point %s: %s", ep.name, error)
            continue
        if _accept_plugin_class(obj):
            found.append(obj)
    return found


def _accept_plugin_class(obj: object) -> bool:
    return isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin


def _load_dropin_module(path: Path):
    module_name = f"sickchill_dropin_{path.stem}_{abs(hash(str(path)))}"
    if path.is_dir():
        init_py = path / "__init__.py"
        plugin_py = path / "plugin.py"
        target = plugin_py if plugin_py.is_file() else init_py
        if not target.is_file():
            return None
        spec = importlib.util.spec_from_file_location(module_name, target, submodule_search_locations=[str(path)])
    elif path.is_file() and path.suffix == ".py":
        spec = importlib.util.spec_from_file_location(module_name, path)
    else:
        return None

    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _classes_from_module(module) -> list[type[Plugin]]:
    found: list[type[Plugin]] = []
    for value in vars(module).values():
        if not _accept_plugin_class(value):
            continue
        # Skip imported bases (NotifierPlugin etc.); only concrete plugins defined here.
        if getattr(value, "__module__", None) != module.__name__:
            continue
        if not getattr(value, "id", None):
            continue
        found.append(value)
    return found


def discover_dropins(plugins_dir: str | Path | None) -> list[type[Plugin]]:
    found: list[type[Plugin]] = []
    if not plugins_dir:
        return found
    root = Path(plugins_dir)
    if not root.is_dir():
        return found

    for child in sorted(root.iterdir()):
        if child.name.startswith(("_", ".")):
            continue
        try:
            module = _load_dropin_module(child)
        except Exception as error:
            logger.warning("Skipping broken drop-in plugin %s: %s", child, error)
            continue
        if module is None:
            continue
        found.extend(_classes_from_module(module))
    return found


def discover_classes(data_dir: str | None = None, plugins_dir: str | None = None) -> list[type[Plugin]]:
    """
    Discovery order: in-tree @register → entry points → DATA_DIR/plugins (or plugins_dir).
    """
    classes: list[type[Plugin]] = []
    seen: set[tuple[str, str]] = set()

    def add(cls: type[Plugin]) -> None:
        if not _accept_plugin_class(cls):
            logger.warning("Rejected non-Plugin object during discovery: %r", cls)
            return
        key = (cls.kind.value, cls.id)
        if key in seen:
            return
        seen.add(key)
        classes.append(cls)

    for cls in registered_classes():
        add(cls)

    for kind in PluginKind:
        for cls in _iter_entry_point_classes(kind):
            add(cls)

    dropin_root = plugins_dir
    if not dropin_root and data_dir:
        dropin_root = str(Path(data_dir) / "plugins")
    for cls in discover_dropins(dropin_root):
        add(cls)

    return classes
