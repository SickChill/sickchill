from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import register
from sickchill.plugins.metadata._base import MetadataGeneratorPlugin


@register
class KodiMetadata(MetadataGeneratorPlugin):
    id = "kodi"
    name = "KODI"
    provider_module: ClassVar[str] = "kodi"
