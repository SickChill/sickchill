from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, ClassVar

_REGISTERED: list[type[Plugin]] = []


class PluginKind(str, Enum):
    NOTIFIER = "notifiers"
    CLIENT = "clients"
    PROVIDER = "providers"
    METADATA = "metadata"


@dataclass(frozen=True)
class Field:
    name: str
    type: str = "str"  # str|password|int|float|bool|url|host|list|select
    default: Any = ""
    required: bool = False
    secret: bool = False
    help: str = ""
    choices: tuple[str, ...] | None = None
    legacy_keys: tuple[str, ...] = ()


ENABLED_FIELD = Field(name="enabled", type="bool", default=False, help="Enable this plugin")


@dataclass
class PluginContext:
    """Host facade exposing only this plugin's settings section."""

    kind: PluginKind
    plugin_id: str
    _data: dict[str, Any] = field(default_factory=dict)
    _writer: Any = None  # callable(kind, plugin_id, data) | None
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("sickchill.plugins"))

    def __post_init__(self) -> None:
        self.logger = logging.LoggerAdapter(
            logging.getLogger(f"sickchill.plugins.{self.kind.value}.{self.plugin_id}"),
            {"plugin": f"{self.kind.value}.{self.plugin_id}"},
        )

    @property
    def settings(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self._data))

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def update(self, **kwargs: Any) -> None:
        self._data.update(kwargs)
        if self._writer is not None:
            self._writer(self.kind, self.plugin_id, dict(self._data))


class Plugin(ABC):
    id: str
    name: str
    kind: ClassVar[PluginKind]
    version: str = "1.0.0"
    schema: ClassVar[tuple[Field, ...]] = ()
    legacy_sections: ClassVar[tuple[str, ...]] = ()

    def __init__(self, ctx: PluginContext):
        self.ctx = ctx

    @classmethod
    def all_fields(cls) -> tuple[Field, ...]:
        names = {f.name for f in cls.schema}
        if "enabled" in names:
            return cls.schema
        return (ENABLED_FIELD,) + cls.schema

    def validate(self) -> list[str]:
        errors: list[str] = []
        for field_def in self.all_fields():
            if field_def.name == "enabled":
                continue
            value = self.ctx.get(field_def.name, field_def.default)
            if field_def.required and (value is None or value == ""):
                errors.append(f"{field_def.name} is required")
                continue
            if value is None or value == "":
                continue
            err = _validate_type(field_def, value)
            if err:
                errors.append(err)
        return errors

    def test(self) -> tuple[bool, str]:
        return True, "ok"


def _validate_type(field_def: Field, value: Any) -> str | None:
    t = field_def.type
    if t == "bool":
        if not isinstance(value, bool) and str(value).lower() not in {"0", "1", "true", "false", "yes", "no"}:
            return f"{field_def.name} must be a boolean"
    elif t == "int":
        try:
            int(value)
        except (TypeError, ValueError):
            return f"{field_def.name} must be an integer"
    elif t == "float":
        try:
            float(value)
        except (TypeError, ValueError):
            return f"{field_def.name} must be a float"
    elif t == "select":
        if field_def.choices is not None and str(value) not in field_def.choices:
            return f"{field_def.name} must be one of {field_def.choices}"
    elif t == "list" and not isinstance(value, (list, tuple, str)):
        return f"{field_def.name} must be a list"
    return None


def register(cls: type[Plugin]) -> type[Plugin]:
    if not issubclass(cls, Plugin):
        raise TypeError(f"{cls!r} is not a Plugin subclass")
    if cls not in _REGISTERED:
        _REGISTERED.append(cls)
    return cls


def registered_classes() -> list[type[Plugin]]:
    return list(_REGISTERED)


def clear_registry() -> None:
    """Test helper: reset in-tree registrations."""
    _REGISTERED.clear()
