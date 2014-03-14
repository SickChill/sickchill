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
