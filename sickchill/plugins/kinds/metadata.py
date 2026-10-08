from __future__ import annotations

from typing import Any, ClassVar

from sickchill.plugins.api import Field, Plugin, PluginKind


class MetadataPlugin(Plugin):
    kind: ClassVar[PluginKind] = PluginKind.METADATA
    # Generators are always available for UI / metadata_provider_dict — no enabled gate.
    legacy_sections: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def all_fields(cls) -> tuple[Field, ...]:
        return cls.schema

    def as_packed_config(self) -> str:
        from sickchill.plugins.metadata.config import METADATA_FLAG_NAMES, pack_flags

        return pack_flags({name: self.ctx.get(name) for name in METADATA_FLAG_NAMES})

    def apply_to_generator(self, generator: Any) -> None:
        generator.set_config(self.as_packed_config())

    def generator(self) -> Any:
        """Optional factory; runtime consumers still use settings.metadata_provider_dict."""
        return None
