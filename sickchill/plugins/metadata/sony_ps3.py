from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import register
from sickchill.plugins.metadata._base import MetadataGeneratorPlugin


@register
class SonyPs3Metadata(MetadataGeneratorPlugin):
    id = "sony_ps3"
    name = "Sony PS3"
    provider_module: ClassVar[str] = "ps3"
