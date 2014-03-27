"""CacheControl import Interface.

Make it easy to import from cachecontrol without long namespaces.
"""

# patch our requests.models.Response to make them pickleable in older
# versions of requests.

import cachecontrol.patch_requests

from cachecontrol.wrapper import CacheControl
from cachecontrol.adapter import CacheControlAdapter
from cachecontrol.controller import CacheController
