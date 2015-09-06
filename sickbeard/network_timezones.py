# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from dateutil import tz
from dateutil import zoneinfo

from sickbeard import db
from sickbeard import helpers
from sickbeard import logger
from sickbeard import encodingKludge as ek
from os.path import basename, join, isfile
import os
import re
import datetime
import requests

# regex to parse time (12/24 hour format)
time_regex = re.compile(r'(\d{1,2})(([:.](\d{2,2}))? ?([PA][. ]? ?M)|[:.](\d{2,2}))\b', flags=re.IGNORECASE)
am_regex = re.compile(r'(A[. ]? ?M)', flags=re.IGNORECASE)
pm_regex = re.compile(r'(P[. ]? ?M)', flags=re.IGNORECASE)

network_dict = None

sb_timezone = tz.tzlocal()


# helper to remove failed temp download
def _remove_zoneinfo_failed(filename):
    try:
        ek.ek(os.remove, filename)
    except:
        pass


# helper to remove old unneeded zoneinfo files
def _remove_old_zoneinfo():
    if zoneinfo.ZONEINFOFILE is not None:
        cur_zoneinfo = ek.ek(basename, zoneinfo.ZONEINFOFILE)
    else:
        return

    cur_file = helpers.real_path(ek.ek(join, ek.ek(os.path.dirname, zoneinfo.__file__), cur_zoneinfo))
    for (path, dirs, files) in ek.ek(os.walk, helpers.real_path(ek.ek(os.path.dirname, zoneinfo.__file__))):
        for filename in files:
            if filename.endswith('.tar.gz'):
                file_w_path = ek.ek(join, path, filename)
                if file_w_path != cur_file and ek.ek(isfile, file_w_path):
                    try:
                        ek.ek(os.remove, file_w_path)
                        logger.log(u'Delete unneeded old zoneinfo File: %s' % file_w_path)
                    except:
                        logger.log(u'Unable to delete: %s' % file_w_path, logger.WARNING)


# update the dateutil zoneinfo
def _update_zoneinfo():
    global sb_timezone
    sb_timezone = tz.tzlocal()
    url_zv = 'http://sickragetv.github.io/sb_network_timezones/zoneinfo.txt'
    try:
        url_data = helpers.getURL(url_zv, session=requests.Session())
        if not url_data:
            raise

        # Filename of existing zoneinfo
        if zoneinfo.ZONEINFOFILE is not None:
            cur_zoneinfo = ek.ek(basename, zoneinfo.ZONEINFOFILE)
        else:
            cur_zoneinfo = None

        # Filename and hash of new zoneinfo
        (new_zoneinfo, zoneinfo_md5) = url_data.strip().rsplit(u' ')
    except Exception as e:
        logger.log(u'Loading zoneinfo.txt failed, this can happen from time to time. Unable to get URL: %s' %
                url_zv, logger.WARNING)
        return

    if (cur_zoneinfo is not None) and (new_zoneinfo == cur_zoneinfo):
        return

    # now load the new zoneinfo
    url_tar = u'http://sickragetv.github.io/sb_network_timezones/%s' % new_zoneinfo

    zonefile = helpers.real_path(ek.ek(join, ek.ek(os.path.dirname, zoneinfo.__file__), new_zoneinfo))
    zonefile_tmp = re.sub(r'\.tar\.gz$', '.tmp', zonefile)

    if ek.ek(os.path.exists, zonefile_tmp):
        try:
            ek.ek(os.remove, zonefile_tmp)
        except:
            logger.log(u'Unable to delete: %s' % zonefile_tmp, logger.WARNING)
            return

    if not helpers.download_file(url_tar, zonefile_tmp, session=requests.Session()):
        return

    if not ek.ek(os.path.exists, zonefile_tmp):
        logger.log(u'Download of %s failed.' % zonefile_tmp, logger.WARNING)
        return

    new_hash = str(helpers.md5_for_file(zonefile_tmp))

    if zoneinfo_md5.upper() == new_hash.upper():
        logger.log(u'Updating timezone info with new one: %s' % new_zoneinfo, logger.INFO)
        try:
            # remove the old zoneinfo file
            if cur_zoneinfo is not None:
                old_file = helpers.real_path(
                    ek.ek(join, ek.ek(os.path.dirname, zoneinfo.__file__), cur_zoneinfo))
                if ek.ek(os.path.exists, old_file):
                    ek.ek(os.remove, old_file)
            # rename downloaded file
            ek.ek(os.rename, zonefile_tmp, zonefile)
            # load the new zoneinfo
            reload(zoneinfo)
            sb_timezone = tz.tzlocal()
        except:
            _remove_zoneinfo_failed(zonefile_tmp)
            return
    else:
        _remove_zoneinfo_failed(zonefile_tmp)
        logger.log(u'MD5 hash does not match: %s File: %s' % (zoneinfo_md5.upper(), new_hash.upper()), logger.WARNING)
        return


# update the network timezone table
def update_network_dict():
    _remove_old_zoneinfo()
    _update_zoneinfo()

    url = 'http://sickragetv.github.io/sb_network_timezones/network_timezones.txt'
    url_data = helpers.getURL(url, session=requests.Session())
    if url_data is None:
        logger.log(u'Updating network timezones failed, this can happen from time to time. URL: %s' % url, logger.WARNING)
        load_network_dict()
        return

    d = {}
    try:
        for line in url_data.splitlines():
            (key, val) = line.decode('utf-8').strip().rsplit(u':', 1)
            if key is None or val is None:
                continue
            d[key] = val
    except (IOError, OSError):
        pass

    my_db = db.DBConnection('cache.db')

    network_list = dict(my_db.select('SELECT * FROM network_timezones;'))

    queries = []
    for network, timezone in d.iteritems():
        existing = network_list.has_key(network)
        if not existing:
            queries.append(['INSERT OR IGNORE INTO network_timezones VALUES (?,?);', [network, timezone]])
        elif network_list[network] is not timezone:
            queries.append(['UPDATE OR IGNORE network_timezones SET timezone = ? WHERE network_name = ?;', [timezone, network]])

        if existing:
            del network_list[network]

    if network_list:
        purged = list(x for x in network_list)
        queries.append(['DELETE FROM network_timezones WHERE network_name IN (%s);' % ','.join(['?'] * len(purged)), purged])

    if queries:
        my_db.mass_action(queries)
        load_network_dict()


# load network timezones from db into dict
def load_network_dict():
    try:
        my_db = db.DBConnection('cache.db')
        cur_network_list = my_db.select('SELECT * FROM network_timezones;')
        if cur_network_list is None or len(cur_network_list) < 1:
            update_network_dict()
            cur_network_list = my_db.select('SELECT * FROM network_timezones;')
        d = dict(cur_network_list)
    except:
        d = {}
    global network_dict
    network_dict = d


# get timezone of a network or return default timezone
def get_network_timezone(network, network_dict):
    if network is None:
        return sb_timezone

    try:
        if zoneinfo.ZONEINFOFILE is not None:
            try:
                n_t = tz.gettz(network_dict[network])
            except:
                return sb_timezone

            if n_t is not None:
                return n_t
            else:
                return sb_timezone
        else:
            return sb_timezone
    except:
        return sb_timezone


# parse date and time string into local time
def parse_date_time(d, t, network):
    if network_dict is None:
        load_network_dict()
    mo = time_regex.search(t)
    if mo is not None and len(mo.groups()) >= 5:
        if mo.group(5) is not None:
            try:
                hr = helpers.tryInt(mo.group(1))
                m = helpers.tryInt(mo.group(4))
                ap = mo.group(5)
                # convert am/pm to 24 hour clock
                if ap is not None:
                    if pm_regex.search(ap) is not None and hr != 12:
                        hr += 12
                    elif am_regex.search(ap) is not None and hr == 12:
                        hr -= 12
            except:
                hr = 0
                m = 0
        else:
            try:
                hr = helpers.tryInt(mo.group(1))
                m = helpers.tryInt(mo.group(6))
            except:
                hr = 0
                m = 0
    else:
        hr = 0
        m = 0
    if hr < 0 or hr > 23 or m < 0 or m > 59:
        hr = 0
        m = 0

    te = datetime.datetime.fromordinal(helpers.tryInt(d))
    try:
        foreign_timezone = get_network_timezone(network, network_dict)
        foreign_naive = datetime.datetime(te.year, te.month, te.day, hr, m, tzinfo=foreign_timezone)
        return foreign_naive
    except:
        return datetime.datetime(te.year, te.month, te.day, hr, m, tzinfo=sb_timezone)


def test_timeformat(t):
    mo = time_regex.search(t)
    if mo is None or len(mo.groups()) < 2:
        return False
    else:
        return True
