import html
import os
import warnings

from sickchill import settings
from sickchill.oldbeard import common

# noinspection PyUnresolvedReferences
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        # noinspection PyUnresolvedReferences
        from pgi.repository import Notify
    except (ImportError, Exception):
        try:
            # noinspection PyUnresolvedReferences
            from gi.repository import Notify
        except (ImportError, Exception):
            Notify = None


# noinspection PyUnresolvedReferences
class Notifier(object):
    def __init__(self):
        self.notify_initialized = None
        if Notify:
            self.notify_initialized = Notify.init("SickChill")

    @staticmethod
    def diagnose():
        """
        Check the environment for reasons libnotify isn't working.  Return a
        user-readable message indicating possible issues.
        """
        if not Notify:
            return (
                "<p>Error: gir-notify isn't installed. On Ubuntu/Debian, install the "
                '<a href="apt:gir1.2-notify-0.7">gir1.2-notify-0.7</a> or '
                '<a href="apt:gir1.0-notify-0.4">gir1.0-notify-0.4</a> package.'
            )

        if "DISPLAY" not in os.environ and "DBUS_SESSION_BUS_ADDRESS" not in os.environ:
            return (
                "<p>Error: Environment variables DISPLAY and DBUS_SESSION_BUS_ADDRESS "
                "aren't set.  libnotify will only work when you run SickChill "
                "from a desktop login."
            )

        try:
            import dbus
        except (ImportError, Exception):
            dbus = None

        if dbus:
            try:
                bus = dbus.SessionBus()
            except dbus.DBusException as error:
                return ("<p>Error: unable to connect to D-Bus session bus: <code>{}</code>." "<p>Are you running SickChill in a desktop session?").format(
                    html.escape(error)
                )
            try:
                bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
            except dbus.DBusException as error:
                return (
                    "<p>Error: there doesn't seem to be a notification daemon available: <code>{}</code> "
                    "<p>Try installing notification-daemon or notify-osd."
                ).format(html.escape(error))

        return "<p>Error: Unable to send notification."

    def notify_snatch(self, ep_name):
        if settings.LIBNOTIFY_NOTIFY_ONSNATCH:
            self._notify(common.notifyStrings[common.NOTIFY_SNATCH], ep_name)

    def notify_download(self, ep_name):
        if settings.LIBNOTIFY_NOTIFY_ONDOWNLOAD:
            self._notify(common.notifyStrings[common.NOTIFY_DOWNLOAD], ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD], ep_name + ": " + lang)

    def notify_update(self, new_version="??"):
        if settings.USE_LIBNOTIFY:
            update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_UPDATE]
            self._notify(title, update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_LIBNOTIFY:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify(title, update_text.format(ipaddress))

    def test_notify(self):
        return self._notify("Test notification", "This is a test notification from SickChill", force=True)

    def _notify(self, title, message, force=False):
        if self.notify_initialized and settings.USE_LIBNOTIFY | force:
            icon = os.path.join(settings.PROG_DIR, "gui", settings.GUI_NAME, "images", "ico", "favicon-120.png")
            # noinspection PyBroadException
            try:
                n = Notify.Notification.new(title, message, icon)
                return n.show()
            except Exception:
                return False
