from __future__ import with_statement
import os
import pytz
import subprocess
import sys

_cache_tz = None

if sys.version_info[0] == 2:

    class Popen(subprocess.Popen):

        def __enter__(self):
            return self

        def __exit__(self, type, value, traceback):
            if self.stdout:
                self.stdout.close()
            if self.stderr:
                self.stderr.close()
            if self.stdin:
                self.stdin.close()
            # Wait for the process to terminate, to avoid zombies.
            self.wait()

else:
    from subprocess import Popen


def _get_localzone(_root='/'):
    with Popen(
        "systemsetup -gettimezone",
        shell=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    ) as pipe:
        tzname = pipe.stdout.read().replace(b'Time Zone: ', b'').strip()

    if not tzname or tzname not in pytz.all_timezones_set:
        # link will be something like /usr/share/zoneinfo/America/Los_Angeles.
        link = os.readlink(os.path.join(_root, "etc/localtime"))
        tzname = link[link.rfind("zoneinfo/") + 9:]

    return pytz.timezone(tzname)


def get_localzone():
    """Get the computers configured local timezone, if any."""
    global _cache_tz
    if _cache_tz is None:
        _cache_tz = _get_localzone()
    return _cache_tz


def reload_localzone():
    """Reload the cached localzone. You need to call this if the timezone has changed."""
    global _cache_tz
    _cache_tz = _get_localzone()
    return _cache_tz
