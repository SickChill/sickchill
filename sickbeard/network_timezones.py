# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import re
import datetime
import requests
from dateutil import tz

from sickbeard import db
from sickbeard import helpers
from sickbeard import logger
from sickrage.helper.common import try_int

# regex to parse time (12/24 hour format)
time_regex = re.compile(r'(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2})?)? ?(?P<meridiem>[PA]\.? ?M?)?\b', re.I)

network_dict = None
sb_timezone = tz.tzwinlocal() if tz.tzwinlocal else tz.tzlocal()


# update the network timezone table
def update_network_dict():
    """Update timezone information from SR repositories"""

    url = 'http://sickrage.github.io/sb_network_timezones/network_timezones.txt'
    url_data = helpers.getURL(url, session=requests.Session())
    if not url_data:
        logger.log(u'Updating network timezones failed, this can happen from time to time. URL: %s' % url, logger.WARNING)
        load_network_dict()
        return

    d = {}
    try:
        for line in url_data.splitlines():
            (key, val) = line.strip().rsplit(u':', 1)
            if key is None or val is None:
                continue
            d[key] = val
    except (IOError, OSError):
        pass

    cache_db_con = db.DBConnection('cache.db')

    network_list = dict(cache_db_con.select('SELECT * FROM network_timezones;'))

    queries = []
    for network, timezone in d.iteritems():
        existing = network in network_list
        if not existing:
            queries.append(['INSERT OR IGNORE INTO network_timezones VALUES (?,?);', [network, timezone]])
        elif network_list[network] != timezone:
            queries.append(['UPDATE OR IGNORE network_timezones SET timezone = ? WHERE network_name = ?;', [timezone, network]])

        if existing:
            del network_list[network]

    if network_list:
        purged = [x for x in network_list]
        queries.append(['DELETE FROM network_timezones WHERE network_name IN (%s);' % ','.join(['?'] * len(purged)), purged])

    if queries:
        cache_db_con.mass_action(queries)
        load_network_dict()


# load network timezones from db into dict
def load_network_dict():
    """
    Load network timezones from db into dict network_dict (global dict)
    """
    try:
        cache_db_con = db.DBConnection('cache.db')
        cur_network_list = cache_db_con.select('SELECT * FROM network_timezones;')
        if not cur_network_list:
            update_network_dict()
            cur_network_list = cache_db_con.select('SELECT * FROM network_timezones;')
        d = dict(cur_network_list)
    except Exception:
        d = {}
    # pylint: disable=global-statement
    global network_dict
    network_dict = d


# get timezone of a network or return default timezone
def get_network_timezone(network, _network_dict):
    """
    Get a timezone of a network from a given network dict

    :param network: network to look up (needle)
    :param _network_dict: dict to look up in (haystack)
    :return:
    """

    # Get the name of the networks timezone from _network_dict
    network_tz_name = _network_dict[network] if network in _network_dict else None

    if network_tz_name is None:
        logger.log(u'Network was not found in the network time zones: %s' % network)

    return tz.gettz(network_tz_name) if network_tz_name else sb_timezone


# parse date and time string into local time
def parse_date_time(d, t, network):
    """
    Parse date and time string into local time

    :param d: date string
    :param t: time string
    :param network: network to use as base
    :return: datetime object containing local time
    """

    if not network_dict:
        load_network_dict()

    parsed_time = time_regex.search(t)
    network_tz = get_network_timezone(network, network_dict)

    hr = 0
    m = 0

    if parsed_time:
        hr = try_int(parsed_time.group('hour'))
        m = try_int(parsed_time.group('minute'))

        ap = parsed_time.group('meridiem')
        ap = ap[0].lower() if ap else ''

        if ap == 'a' and hr == 12:
            hr -= 12
        elif ap == 'p' and hr != 12:
            hr += 12

        hr = hr if 0 <= hr <= 23 else 0
        m = m if 0 <= m <= 59 else 0

    result = datetime.datetime.fromordinal(max(try_int(d), 1))

    return result.replace(hour=hr, minute=m, tzinfo=network_tz)


def test_timeformat(time_string):
    return time_regex.search(time_string) is not None
