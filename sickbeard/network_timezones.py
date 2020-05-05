# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import datetime
import re

# Third Party Imports
import six
from dateutil import tz

# First Party Imports
from sickchill.helper.common import try_int

# Local Folder Imports
from . import db, helpers, logger

# regex to parse time (12/24 hour format)
time_regex = re.compile(r'(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2})?)? ?(?P<meridiem>[PA]\.? ?M?)?\b', re.I)

network_dict = {}

try:
    sb_timezone = tz.tzwinlocal() if tz.tzwinlocal else tz.tzlocal()
except Exception:
    sb_timezone = tz.tzlocal()

missing_network_timezones = set()


def update_network_dict():
    """Update timezone information from SR repositories"""

    url = 'http://sickchill.github.io/sb_network_timezones/network_timezones.txt'
    data = helpers.getURL(url, session=helpers.make_session(), returns='text')
    if not data:
        logger.log('Updating network timezones failed, this can happen from time to time. URL: {0}'.format(url), logger.WARNING)
        load_network_dict()
        return

    d = {}
    try:
        for line in data.splitlines():
            (key, val) = line.strip().rsplit(':', 1)
            if not val:  # n Lets set a default
                val = 'US/Eastern'
            if key and val:
                d[key.lower()] = val
    except (IOError, OSError):
        pass

    if not d:
        logger.log('Parsing network timezones failed, not going to touch the db', logger.WARNING)
        load_network_dict()
        return

    cache_db_con = db.DBConnection('cache.db')

    network_list = dict(cache_db_con.select('SELECT * FROM network_timezones;'))

    queries = []
    for network, timezone in six.iteritems(d):
        existing = network in network_list
        if not existing:
            queries.append(['INSERT OR IGNORE INTO network_timezones VALUES (?,?);', [network, timezone]])
        elif network_list[network] != timezone:
            queries.append(['UPDATE OR IGNORE network_timezones SET timezone = ? WHERE network_name = ?;', [timezone, network]])

        if existing:
            del network_list[network]

    for network in network_list:
        queries.append(['DELETE FROM network_timezones WHERE network_name = ?;', [network]])

    if queries:
        cache_db_con.mass_action(queries)
        load_network_dict()


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

        network_dict.clear()
        network_dict.update(dict(cur_network_list))
    except Exception:
        pass


def get_network_timezone(network):
    """
    Get the timezone of a network, or return sb_timezone

    :param network: network to look up
    :return: network timezone if found, or sb_timezone
    """

    orig_network = network
    if network:
        network = network.lower()

    network_tz_name = network_dict.get(network)
    if network and not (network_tz_name or network in missing_network_timezones):
        missing_network_timezones.add(network)
        logger.log(_('Missing time zone for network: {0}. Check valid network is set in indexer (theTVDB) before filing issue.').format(orig_network),
                   logger.ERROR)

    try:
        network_tz = (tz.gettz(network_tz_name) or sb_timezone) if network_tz_name else sb_timezone
    except Exception:
        return sb_timezone
    return network_tz


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
    network_tz = get_network_timezone(network)

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
