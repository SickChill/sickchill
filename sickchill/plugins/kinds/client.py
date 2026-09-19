from __future__ import annotations

from typing import Any, ClassVar

from sickchill.plugins.api import Field, Plugin, PluginKind


class ClientPlugin(Plugin):
    kind: ClassVar[PluginKind] = PluginKind.CLIENT
    # Selection is via TORRENT_METHOD / NZB_METHOD — no enabled field.
    legacy_sections: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def all_fields(cls) -> tuple[Field, ...]:
        return cls.schema

    def send(self, result: Any) -> bool:
        return False

    def test_client_connection(self, *args: Any, **kwargs: Any) -> tuple[bool, str]:
        return False, "not implemented"

    def test(self) -> tuple[bool, str]:
        return self.test_client_connection()
