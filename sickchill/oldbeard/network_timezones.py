import datetime
import re

from dateutil import tz

from sickchill.helper.common import try_int

from .. import logger
from . import db, helpers

# regex to parse time (12/24 hour format)
time_regex = re.compile(r"(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2})?)? ?(?P<meridiem>[PA]\.? ?M?)?\b", re.I)

network_dict = {}

sb_timezone = tz.gettz()

missing_network_timezones = set()


def update_network_dict():
    """Update timezone information from SR repositories"""

    url = "https://sickchill.github.io/sb_network_timezones/network_timezones.txt"
    data = helpers.getURL(url, session=helpers.make_session(), returns="text")
    if not data:
        logger.warning("Updating network timezones failed, this can happen from time to time. URL: {0}".format(url))
        load_network_dict()
        return

    d = {}
    try:
        for line in data.splitlines():
            (key, val) = line.strip().rsplit(":", 1)
            if not val:  # n Lets set a default
                val = "US/Eastern"
            if key and val:
                d[key.lower()] = val
    except (IOError, OSError):
        pass

    if not d:
        logger.warning("Parsing network timezones failed, not going to touch the db")
        load_network_dict()
        return

    cache_db_con = db.DBConnection("cache.db")

    network_list = dict(cache_db_con.select("SELECT * FROM network_timezones;"))

    queries = []
    for network, timezone in d.items():
        existing = network in network_list
        if not existing:
            queries.append(["INSERT OR IGNORE INTO network_timezones VALUES (?,?);", [network, timezone]])
        elif network_list[network] != timezone:
            queries.append(["UPDATE OR IGNORE network_timezones SET timezone = ? WHERE network_name = ?;", [timezone, network]])

        if existing:
            del network_list[network]

    for network in network_list:
        queries.append(["DELETE FROM network_timezones WHERE network_name = ?;", [network]])

    if queries:
        cache_db_con.mass_action(queries)
        load_network_dict()


def load_network_dict():
    """
    Load network timezones from db into dict network_dict (global dict)
    """
    try:
        cache_db_con = db.DBConnection("cache.db")
        cur_network_list = cache_db_con.select("SELECT * FROM network_timezones;")
        if not cur_network_list:
            update_network_dict()
            cur_network_list = cache_db_con.select("SELECT * FROM network_timezones;")

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
        severity = (logger.ERROR, logger.INFO)[network.endswith("none")]
        logger.log(
            severity,
            _(
                "Missing time zone for network: {orig_network}. Check valid network is set in indexer (theTVDB) before filing issue.".format(
                    orig_network=orig_network
                )
            ),
        )

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
        hr = try_int(parsed_time.group("hour"))
        m = try_int(parsed_time.group("minute"))

        ap = parsed_time.group("meridiem")
        ap = ap[0].lower() if ap else ""

        if ap == "a" and hr == 12:
            hr -= 12
        elif ap == "p" and hr != 12:
            hr += 12

        hr = hr if 0 <= hr <= 23 else 0
        m = m if 0 <= m <= 59 else 0

    result = datetime.datetime.fromordinal(max(try_int(d), 1))

    return result.replace(hour=hr, minute=m, tzinfo=network_tz)


def test_timeformat(time_string):
    return time_regex.search(time_string) is not None
