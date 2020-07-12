class traktException(Exception):
    pass


class traktAuthException(traktException):
    pass


class traktServerBusy(traktException):
    pass
