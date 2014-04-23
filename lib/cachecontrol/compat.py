try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


try:
    import email.utils
    parsedate_tz = email.utils.parsedate_tz
except ImportError:
    import email.Utils
    parsedate_tz = email.Utils.parsedate_tz


try:
    import cPickle as pickle
except ImportError:
    import pickle


# Handle the case where the requests has been patched to not have urllib3
# bundled as part of it's source.
try:
    from requests.packages.urllib3.response import HTTPResponse
except ImportError:
    from urllib3.response import HTTPResponse
