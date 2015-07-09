#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
#
# GuessIt is free software; you can redistribute it and/or modify it under
# the terms of the Lesser GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# GuessIt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import re

from dateutil import parser


_dsep = r'[-/ \.]'
_dsep_bis = r'[-/ \.x]'

date_regexps = [
    re.compile('%s(\d{8})%s' % (_dsep, _dsep), re.IGNORECASE),
    re.compile('%s(\d{6})%s' % (_dsep, _dsep), re.IGNORECASE),
    re.compile('[^\d](\d{2})%s(\d{1,2})%s(\d{1,2})[^\d]' % (_dsep, _dsep), re.IGNORECASE),
    re.compile('[^\d](\d{1,2})%s(\d{1,2})%s(\d{2})[^\d]' % (_dsep, _dsep), re.IGNORECASE),
    re.compile('[^\d](\d{4})%s(\d{1,2})%s(\d{1,2})[^\d]' % (_dsep_bis, _dsep), re.IGNORECASE),
    re.compile('[^\d](\d{1,2})%s(\d{1,2})%s(\d{4})[^\d]' % (_dsep, _dsep_bis), re.IGNORECASE),
    re.compile('[^\d](\d{1,2}(?:st|nd|rd|th)?%s(?:[a-z]{3,10})%s\d{4})[^\d]' % (_dsep, _dsep), re.IGNORECASE)]


def valid_year(year, today=None):
    """Check if number is a valid year"""
    if not today:
        today = datetime.date.today()
    return 1920 < year < today.year + 5


def search_year(string):
    """Looks for year patterns, and if found return the year and group span.

    Assumes there are sentinels at the beginning and end of the string that
    always allow matching a non-digit delimiting the date.

    Note this only looks for valid production years, that is between 1920
    and now + 5 years, so for instance 2000 would be returned as a valid
    year but 1492 would not.

    >>> search_year(' in the year 2000... ')
    (2000, (13, 17))

    >>> search_year(' they arrived in 1492. ')
    (None, None)
    """
    match = re.search(r'[^0-9]([0-9]{4})[^0-9]', string)
    if match:
        year = int(match.group(1))
        if valid_year(year):
            return year, match.span(1)

    return None, None


def search_date(string, year_first=None, day_first=True):
    """Looks for date patterns, and if found return the date and group span.

    Assumes there are sentinels at the beginning and end of the string that
    always allow matching a non-digit delimiting the date.

    Year can be defined on two digit only. It will return the nearest possible
    date from today.

    >>> search_date(' This happened on 2002-04-22. ')
    (datetime.date(2002, 4, 22), (18, 28))

    >>> search_date(' And this on 17-06-1998. ')
    (datetime.date(1998, 6, 17), (13, 23))

    >>> search_date(' no date in here ')
    (None, None)
    """
    start, end = None, None
    match = None
    for date_re in date_regexps:
        s = date_re.search(string)
        if s and (match is None or s.end() - s.start() > len(match)):
            start, end = s.start(), s.end()
            if date_re.groups:
                match = '-'.join(s.groups())
            else:
                match = s.group()

    if match is None:
        return None, None

    today = datetime.date.today()

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
        except (ValueError, TypeError) as e: #see https://bugs.launchpad.net/dateutil/+bug/1247643
            date = None
            pass
        # check date plausibility
        if date and valid_year(date.year, today=today):
            return date.date(), (start+1, end-1) #compensate for sentinels

    return None, None
