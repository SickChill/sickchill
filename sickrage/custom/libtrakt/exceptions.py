# coding=utf-8
from __future__ import unicode_literals


class TraktException(Exception):
    pass


class TraktAuthException(TraktException):
    pass


class TraktServerBusy(TraktException):
    pass
