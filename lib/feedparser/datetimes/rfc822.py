from __future__ import absolute_import, unicode_literals

import datetime

timezone_names = {
    'ut': 0, 'gmt': 0, 'z': 0,
    'adt': -3, 'ast': -4, 'at': -4,
    'edt': -4, 'est': -5, 'et': -5,
    'cdt': -5, 'cst': -6, 'ct': -6,
    'mdt': -6, 'mst': -7, 'mt': -7,
    'pdt': -7, 'pst': -8, 'pt': -8,
    'a': -1, 'n': 1,
    'm': -12, 'y': 12,
    'met': 1, 'mest': 2,
}
day_names = {'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}
months = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def _parse_date_rfc822(date):
    """Parse RFC 822 dates and times
    http://tools.ietf.org/html/rfc822#section-5

    There are some formatting differences that are accounted for:
    1. Years may be two or four digits.
    2. The month and day can be swapped.
    3. Additional timezone names are supported.
    4. A default time and timezone are assumed if only a date is present.

    :param str date: a date/time string that will be converted to a time tuple
    :returns: a UTC time tuple, or None
    :rtype: time.struct_time | None
    """

    parts = date.lower().split()
    if len(parts) < 5:
        # Assume that the time and timezone are missing
        parts.extend(('00:00:00', '0000'))
    # Remove the day name
    if parts[0][:3] in day_names:
        parts = parts[1:]
    if len(parts) < 5:
        # If there are still fewer than five parts, there's not enough
        # information to interpret this.
        return None

    # Handle the day and month name.
    month = months.get(parts[1][:3])
    try:
        day = int(parts[0])
    except ValueError:
        # Check if the day and month are swapped.
        if months.get(parts[0][:3]):
            try:
                day = int(parts[1])
            except ValueError:
                return None
            month = months.get(parts[0][:3])
        else:
            return None
    if not month:
        return None

    # Handle the year.
    try:
        year = int(parts[2])
    except ValueError:
        return None
    # Normalize two-digit years:
    # Anything in the 90's is interpreted as 1990 and on.
    # Anything 89 or less is interpreted as 2089 or before.
    if len(parts[2]) <= 2:
        year += (1900, 2000)[year < 90]

    # Handle the time (default to 00:00:00).
    time_parts = parts[3].split(':')
    time_parts.extend(('0',) * (3 - len(time_parts)))
    try:
        (hour, minute, second) = [int(i) for i in time_parts]
    except ValueError:
        return None

    # Handle the timezone information, if any (default to +0000).
    # Strip 'Etc/' from the timezone.
    if parts[4].startswith('etc/'):
        parts[4] = parts[4][4:]
    # Normalize timezones that start with 'gmt':
    # GMT-05:00 => -0500
    # GMT => GMT
    if parts[4].startswith('gmt'):
        parts[4] = ''.join(parts[4][3:].split(':')) or 'gmt'
    # Handle timezones like '-0500', '+0500', and 'EST'
    if parts[4] and parts[4][0] in ('-', '+'):
        try:
            timezone_hours = int(parts[4][1:3])
            timezone_minutes = int(parts[4][3:])
        except ValueError:
            return None
        if parts[4].startswith('-'):
            timezone_hours *= -1
            timezone_minutes *= -1
    else:
        timezone_hours = timezone_names.get(parts[4], 0)
        timezone_minutes = 0

    # Create the datetime object and timezone delta objects
    try:
        stamp = datetime.datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None
    delta = datetime.timedelta(0, 0, 0, 0, timezone_minutes, timezone_hours)

    # Return the date and timestamp in a UTC 9-tuple
    try:
        return (stamp - delta).utctimetuple()
    except (OverflowError, ValueError):
        # IronPython throws ValueErrors instead of OverflowErrors
        return None
