"""Shared schema and wrapper for metadata generator plugins."""

from __future__ import annotations

from typing import Any, ClassVar

from sickchill.plugins.api import Field
from sickchill.plugins.kinds.metadata import MetadataPlugin
from sickchill.plugins.metadata.config import METADATA_FLAG_NAMES, pack_flags

METADATA_FLAG_SCHEMA: tuple[Field, ...] = tuple(Field(name=name, type="bool", default=False) for name in METADATA_FLAG_NAMES)


class MetadataGeneratorPlugin(MetadataPlugin):
    """Wraps sickchill.providers.metadata.<module>.metadata_class."""

    version = "1.0.0"
    schema: ClassVar[tuple[Field, ...]] = METADATA_FLAG_SCHEMA
    # Provider module basename under sickchill.providers.metadata (ps3 for sony_ps3).
    provider_module: ClassVar[str] = ""

    def as_packed_config(self) -> str:
        return pack_flags({name: self.ctx.get(name) for name in METADATA_FLAG_NAMES})

    def apply_to_generator(self, generator: Any) -> None:
        generator.set_config(self.as_packed_config())

    def generator(self):
        import importlib

        module_name = self.provider_module or self.id
        mod = importlib.import_module(f"sickchill.providers.metadata.{module_name}")
        instance = mod.metadata_class()
        self.apply_to_generator(instance)
        return instance
