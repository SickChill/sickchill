#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2016-5-27

@author: hustcc
'''

from datetime import datetime
from datetime import date
from datetime import time

__ALL__ = ['parse']


def parse(input):
    '''
    parse input to datetime
    '''
    if isinstance(input, datetime):
        return input
    if isinstance(input, date):
        return date_to_datetime(input)
    if isinstance(input, time):
        return time_to_datetime(input)
    if isinstance(input, (int, float)):
        return timestamp_to_datetime(input)
    if isinstance(input, (str)):
        return string_to_data_time(input)
    return None


def date_to_datetime(d):
    return _combine_date_time(d, time(0, 0, 0))


def time_to_datetime(t):
    return _combine_date_time(date.today(), t)


def timestamp_to_datetime(ts):
    '''
    parse timestamp to datetime
    '''
    return datetime.fromtimestamp(ts)


def _combine_date_time(d, t):
    if (d is not None) and (t is not None):
        return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second)
    return None


def _string_to_date(date_string):
    if not date_string:
        return None
    try:
        d_array = date_string.split('-')
        return date(int(d_array[0]), int(d_array[1]), int(d_array[2]))
    except:
        return None


def _string_to_time(time_string):
    if not time_string:
        return None
    try:
        t_array = time_string.split(':')
        return time(int(t_array[0]), int(t_array[1]), int(t_array[2]))
    except:
        return None


def string_to_data_time(d):
    '''
    simple parse date string, such as:
    2016-5-27 21:22:20
    2016-05-27 21:22:2
    2016/05/27 21:22:2

    2016-05-27
    2016/5/27

    21:22:2
    '''
    if d:
        d = d.replace('/', '-')
        if ' ' in d:
            _datetime = d.split(' ')
            if len(_datetime) == 2:
                _d = _string_to_date(_datetime[0])
                _t = _string_to_time(_datetime[1])
                return _combine_date_time(_d, _t)
        else:
            # no space
            if '-' in d:
                return date_to_datetime(_string_to_date(d))
            elif ':' in d:
                return time_to_datetime(_string_to_time(d))
    return None
