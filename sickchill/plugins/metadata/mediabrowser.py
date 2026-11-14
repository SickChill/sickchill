from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import register
from sickchill.plugins.metadata._base import MetadataGeneratorPlugin


@register
class MediabrowserMetadata(MetadataGeneratorPlugin):
    id = "mediabrowser"
    name = "MediaBrowser"
    provider_module: ClassVar[str] = "mediabrowser"
