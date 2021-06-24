#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2016-5-26

@author: hustcc
'''

from datetime import datetime, timedelta
from timeago.locales import timeago_template
from timeago.excepts import ParameterUnvalid
from timeago import parser
from timeago.setting import DEFAULT_LOCALE

__version__ = '1.0.14'
__license__ = 'MIT'
__ALL__ = ['format']


# Original fix #2 for Py2.6
def total_seconds(dt):
    # Keep backward compatibility with Python 2.6 which doesn't have
    # this method
    if hasattr(datetime, 'total_seconds'):
        return dt.total_seconds()
    else:
        return (dt.microseconds +
                (dt.seconds + dt.days * 24 * 3600) * 10**6) / 10**6


# second, minute, hour, day, week, month, year(365 days)
SEC_ARRAY = [60.0, 60.0, 24.0, 7.0, 365.0 / 7.0 / 12.0, 12.0]
SEC_ARRAY_LEN = 6


def format(date, now=None, locale='en'):
    '''
    the entry method
    '''
    if not isinstance(date, timedelta):
        if now is None:
            now = datetime.now()
        date = parser.parse(date)
        now = parser.parse(now)

        if date is None:
            raise ParameterUnvalid('the parameter `date` should be datetime '
                                   '/ timedelta, or datetime formatted string.')
        if now is None:
            raise ParameterUnvalid('the parameter `now` should be datetime, '
                                   'or datetime formatted string.')
        date = now - date
    # the gap sec
    diff_seconds = int(total_seconds(date))

    # is ago or in
    ago_in = 0
    if diff_seconds < 0:
        ago_in = 1  # date is later then now, is the time in future
        diff_seconds *= -1  # change to positive

    tmp = 0
    i = 0
    while i < SEC_ARRAY_LEN:
        tmp = SEC_ARRAY[i]
        if diff_seconds >= tmp:
            i += 1
            diff_seconds /= tmp
        else:
            break
    diff_seconds = int(diff_seconds)
    i *= 2

    if diff_seconds > (i == 0 and 9 or 1):
        i += 1

    if locale is None:
        locale = DEFAULT_LOCALE

    tmp = timeago_template(locale, i, ago_in)
    if hasattr(tmp, '__call__'):
        tmp = tmp(diff_seconds)
    return '%s' in tmp and tmp % diff_seconds or tmp
