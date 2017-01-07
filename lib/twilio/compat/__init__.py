
# Those are not supported by the six library and needs to be done manually
from six import binary_type

try:
    # python 3
    from urllib.parse import urlencode, urlparse, urljoin, urlunparse
except ImportError:
    # python 2 backward compatibility
    # noinspection PyUnresolvedReferences
    from urllib import urlencode
    # noinspection PyUnresolvedReferences
    from urlparse import urlparse, urljoin, urlunparse

try:
    # python 2
    from itertools import izip
except ImportError:
    # python 3
    izip = zip
