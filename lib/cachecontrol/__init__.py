"""CacheControl import Interface.

Make it easy to import from cachecontrol without long namespaces.
"""
from .wrapper import CacheControl
from .adapter import CacheControlAdapter
from .controller import CacheController

from lib.requests.packages import urllib3
urllib3.disable_warnings()
