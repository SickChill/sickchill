# -*- coding: utf-8 -*-
"""
utils.py
~~~~~~~~

Utility functions for use with httpcache.
"""
from datetime import datetime, timedelta

try:  # Python 2
    from urlparse import urlparse
except ImportError:  # Python 3
    from urllib.parse import urlparse

RFC_1123_DT_STR = "%a, %d %b %Y %H:%M:%S GMT"
RFC_850_DT_STR = "%A, %d-%b-%y %H:%M:%S GMT"


def parse_date_header(header):
    """
    Given a date header in the form specified by RFC 2616, return a Python
    datetime object.

    RFC 2616 specifies three possible formats for date/time headers, and
    makes it clear that all dates/times should be in UTC/GMT. That is assumed
    by this library, which simply does everything in UTC. This currently does
    not parse the C asctime() string, because that's effort.

    This function does _not_ follow Postel's Law. If a format does not strictly
    match the defined strings, this function returns None. This is considered
    'safe' behaviour.
    """
    try:
        dt = datetime.strptime(header, RFC_1123_DT_STR)
    except ValueError:
        try:
            dt = datetime.strptime(header, RFC_850_DT_STR)
        except ValueError:
            dt = None
    except TypeError:
        dt = None

    return dt


def build_date_header(dt):
    """
    Given a Python datetime object, build a Date header value according to
    RFC 2616.

    RFC 2616 specifies that the RFC 1123 form is to be preferred, so that is
    what we use.
    """
    return dt.strftime(RFC_1123_DT_STR)


def expires_from_cache_control(header, current_time):
    """
    Given a Cache-Control header, builds a Python datetime object corresponding
    to the expiry time (in UTC). This function should respect all relevant
    Cache-Control directives.

    Takes current_time as an argument to ensure that 'max-age=0' generates the
    correct behaviour without being special-cased.

    Returns None to indicate that a request must not be cached.
    """
    # Cache control header values are made of multiple comma separated fields.
    # Splitting them like this is probably a bad idea, but I'm going to roll with
    # it for now. We'll come back to it.
    fields = header.split(', ')
    duration = None

    for field in fields:
        # Right now we don't handle no-cache applied to specific fields. To be
        # as 'nice' as possible, treat any no-cache as applying to the whole
        # request. Bail early, because there's no reason to stick around.
        if field.startswith('no-cache') or field == 'no-store':
            return None

        if field.startswith('max-age'):
            _, duration = field.split('=')
            duration = int(duration)

    if duration:
        interval = timedelta(seconds=int(duration))
        return current_time + interval

def url_contains_query(url):
    """
    A very stupid function for determining if a URL contains a query string
    or not.
    """
    if urlparse(url).query:
        return True
    else:
        return False
