# -*- coding: utf-8 -*-
"""
__init__.py
~~~~~~~~~~~

Defines the public API to the httpcache module.
"""

__version__ = '0.1.3'

from .cache import HTTPCache
from .adapter import CachingHTTPAdapter

__all__ = [HTTPCache, CachingHTTPAdapter]
