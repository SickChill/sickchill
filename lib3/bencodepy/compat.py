"""bencode.py - compatibility helpers."""

import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


def is_binary(s):
    if PY3:
        return isinstance(s, bytes)

    return isinstance(s, str)


def is_text(s):
    if PY3:
        return isinstance(s, str)

    return isinstance(s, unicode)  # noqa: F821


def to_binary(s):
    if is_binary(s):
        return s

    if is_text(s):
        return s.encode('utf-8', 'strict')

    raise TypeError("expected binary or text (found %s)" % type(s))
