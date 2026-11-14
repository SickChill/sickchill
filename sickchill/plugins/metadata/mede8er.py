from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import register
from sickchill.plugins.metadata._base import MetadataGeneratorPlugin


@register
class Mede8erMetadata(MetadataGeneratorPlugin):
    id = "mede8er"
    name = "Mede8er"
    provider_module: ClassVar[str] = "mede8er"
