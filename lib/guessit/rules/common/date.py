#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Date
"""
from dateutil import parser

from rebulk.remodule import re

_dsep = r'[-/ \.]'
_dsep_bis = r'[-/ \.x]'

date_regexps = [
    re.compile(r'{0!s}((\d{{8}})){1!s}'.format(_dsep, _dsep), re.IGNORECASE),
    re.compile(r'{0!s}((\d{{6}})){1!s}'.format(_dsep, _dsep), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{{2}}){0!s}(\d{{1,2}}){1!s}(\d{{1,2}}))(?:$|[^\d])'.format(_dsep, _dsep), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{{1,2}}){0!s}(\d{{1,2}}){1!s}(\d{{2}}))(?:$|[^\d])'.format(_dsep, _dsep), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{{4}}){0!s}(\d{{1,2}}){1!s}(\d{{1,2}}))(?:$|[^\d])'.format(_dsep_bis, _dsep), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{{1,2}}){0!s}(\d{{1,2}}){1!s}(\d{{4}}))(?:$|[^\d])'.format(_dsep, _dsep_bis), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{{1,2}}(?:st|nd|rd|th)?{0!s}(?:[a-z]{{3,10}}){1!s}\d{{4}}))(?:$|[^\d])'.format(_dsep, _dsep),
               re.IGNORECASE)]


def valid_year(year):
    """Check if number is a valid year"""
    return 1920 <= year < 2030


def search_date(string, year_first=None, day_first=True):
    """Looks for date patterns, and if found return the date and group span.

    Assumes there are sentinels at the beginning and end of the string that
    always allow matching a non-digit delimiting the date.

    Year can be defined on two digit only. It will return the nearest possible
    date from today.

    >>> search_date(' This happened on 2002-04-22. ')
    (18, 28, datetime.date(2002, 4, 22))

    >>> search_date(' And this on 17-06-1998. ')
    (13, 23, datetime.date(1998, 6, 17))

    >>> search_date(' no date in here ')
    """
    start, end = None, None
    match = None
    for date_re in date_regexps:
        search_match = date_re.search(string)
        if search_match and (match is None or search_match.end() - search_match.start() > len(match)):
            start, end = search_match.start(1), search_match.end(1)
            match = '-'.join(search_match.groups()[1:])

    if match is None:
        return

    # If day_first/year_first is undefined, parse is made using both possible values.
    yearfirst_opts = [False, True]
    if year_first is not None:
        yearfirst_opts = [year_first]

    dayfirst_opts = [True, False]
    if day_first is not None:
        dayfirst_opts = [day_first]

    kwargs_list = ({'dayfirst': d, 'yearfirst': y} for d in dayfirst_opts for y in yearfirst_opts)
    for kwargs in kwargs_list:
        try:
            date = parser.parse(match, **kwargs)
        except (ValueError, TypeError):  # pragma: no cover
            # see https://bugs.launchpad.net/dateutil/+bug/1247643
            date = None

        # check date plausibility
        if date and valid_year(date.year):  # pylint:disable=no-member
            return start, end, date.date()  # pylint:disable=no-member
