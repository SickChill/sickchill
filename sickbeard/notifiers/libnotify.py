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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import os
import cgi
import sickbeard

from sickbeard import logger, common


def diagnose():
    '''
    Check the environment for reasons libnotify isn't working.  Return a
    user-readable message indicating possible issues.
    '''
    try:
        from gi.repository import Notify  # @UnusedImport
    except ImportError:
        return (u"<p>Error: gir-notify isn't installed. On Ubuntu/Debian, install the "
                u"<a href=\"apt:gir1.2-notify-0.7\">gir1.2-notify-0.7</a> or "
                u"<a href=\"apt:gir1.0-notify-0.4\">gir1.0-notify-0.4</a> package.")
    if 'DISPLAY' not in os.environ and 'DBUS_SESSION_BUS_ADDRESS' not in os.environ:
        return (u"<p>Error: Environment variables DISPLAY and DBUS_SESSION_BUS_ADDRESS "
                u"aren't set.  libnotify will only work when you run SickRage "
                u"from a desktop login.")
    try:
        import dbus
    except ImportError:
        pass
    else:
        try:
            bus = dbus.SessionBus()
        except dbus.DBusException, e:
            return (u"<p>Error: unable to connect to D-Bus session bus: <code>%s</code>."
                    u"<p>Are you running SickRage in a desktop session?") % (cgi.escape(e),)
        try:
            bus.get_object('org.freedesktop.Notifications',
                           '/org/freedesktop/Notifications')
        except dbus.DBusException, e:
            return (u"<p>Error: there doesn't seem to be a notification daemon available: <code>%s</code> "
                    u"<p>Try installing notification-daemon or notify-osd.") % (cgi.escape(e),)
    return u"<p>Error: Unable to send notification."


class LibnotifyNotifier:
    def __init__(self):
        self.Notify = None
        self.gobject = None

    def init_notify(self):
        if self.Notify is not None:
            return True
        try:
            from gi.repository import Notify
        except ImportError:
            logger.log(u"Unable to import Notify from gi.repository. libnotify notifications won't work.", logger.ERROR)
            return False
        try:
            from gi.repository import GObject
        except ImportError:
            logger.log(u"Unable to import GObject from gi.repository. We can't catch a GError in display.", logger.ERROR)
            return False
        if not Notify.init('SickRage'):
            logger.log(u"Initialization of Notify failed. libnotify notifications won't work.", logger.ERROR)
            return False
        self.Notify = Notify
        self.gobject = GObject
        return True

    def notify_snatch(self, ep_name):
        if sickbeard.LIBNOTIFY_NOTIFY_ONSNATCH:
            self._notify(common.notifyStrings[common.NOTIFY_SNATCH], ep_name)

    def notify_download(self, ep_name):
        if sickbeard.LIBNOTIFY_NOTIFY_ONDOWNLOAD:
            self._notify(common.notifyStrings[common.NOTIFY_DOWNLOAD], ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD], ep_name + ": " + lang)
            
    def notify_git_update(self, new_version = "??"):
        if sickbeard.USE_LIBNOTIFY:
            update_text=common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title=common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify(title, update_text + new_version)

    def test_notify(self):
        return self._notify('Test notification', "This is a test notification from SickRage", force=True)

    def _notify(self, title, message, force=False):
        if not sickbeard.USE_LIBNOTIFY and not force:
            return False
        if not self.init_notify():
            return False

        # Can't make this a global constant because PROG_DIR isn't available
        # when the module is imported.
        icon_path = os.path.join(sickbeard.PROG_DIR, 'gui', 'slick', 'images', 'ico', 'favicon-120.png')

        # If the session bus can't be acquired here a bunch of warning messages
        # will be printed but the call to show() will still return True.
        # pynotify doesn't seem too keen on error handling.
        n = self.Notify.Notification.new(title, message, icon_path)
        try:
            return n.show()
        except self.gobject.GError:
            return False


notifier = LibnotifyNotifier
