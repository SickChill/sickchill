class traktException(Exception):
    pass


class traktAuthException(traktException):
    pass


class traktServerBusy(traktException):
    pass


class traktForbiddenException(traktException):
    """Trakt returned 403 — invalid / blocked API key or unapproved app."""
