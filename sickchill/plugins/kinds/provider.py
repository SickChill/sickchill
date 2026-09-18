from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import Plugin, PluginKind


class ProviderPlugin(Plugin):
    kind: ClassVar[PluginKind] = PluginKind.PROVIDER
