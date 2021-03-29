# Author: Rafael Silva <rpluto@gmail.com>
# Author: Marvin Pinto <me@marvinp.ca>
from sickchill import logger, settings
from sickchill.oldbeard import common, helpers


class Notifier(object):
    def __init__(self):
        self.session = helpers.make_session()
        self.url = "https://new.boxcar.io/api/notifications"

    def test_notify(self, accesstoken, title="SickChill : Test"):
        return self._sendBoxcar2("This is a test notification from SickChill", title, accesstoken)

    def _sendBoxcar2(self, msg, title, accesstoken):
        """
        Sends a boxcar2 notification to the address provided

        msg: The message to send
        title: The title of the message
        accesstoken: to send to this device

        returns: True if the message succeeded, False otherwise
        """
        # http://blog.boxcar.io/post/93211745502/boxcar-api-update-boxcar-api-update-icon-and

        post_data = {
            "user_credentials": accesstoken,
            "notification[title]": "SickChill : {0}: {1}".format(title, msg),
            "notification[long_message]": msg,
            "notification[sound]": "notifier-2",
            "notification[source_name]": "SickChill",
            "notification[icon_url]": settings.LOGO_URL,
        }

        response = helpers.getURL(self.url, post_data=post_data, session=self.session, timeout=60, returns="json")
        if not response:
            logger.exception("Boxcar2 notification failed.")
            return False

        logger.debug("Boxcar2 notification successful.")
        return True

    def notify_snatch(self, ep_name, title=common.notifyStrings[common.NOTIFY_SNATCH]):
        if settings.BOXCAR2_NOTIFY_ONSNATCH:
            self._notifyBoxcar2(title, ep_name)

    def notify_download(self, ep_name, title=common.notifyStrings[common.NOTIFY_DOWNLOAD]):
        if settings.BOXCAR2_NOTIFY_ONDOWNLOAD:
            self._notifyBoxcar2(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD]):
        if settings.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyBoxcar2(title, ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
        self._notifyBoxcar2(title, update_text + new_version)

    def notify_login(self, ipaddress=""):
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._notifyBoxcar2(title, update_text.format(ipaddress))

    def _notifyBoxcar2(self, title, message, accesstoken=None):
        """
        Sends a boxcar2 notification based on the provided info or SB config

        title: The title of the notification to send
        message: The message string to send
        accesstoken: to send to this device
        """

        if not settings.USE_BOXCAR2:
            logger.debug("Notification for Boxcar2 not enabled, skipping this notification")
            return False

        accesstoken = accesstoken or settings.BOXCAR2_ACCESSTOKEN

        logger.debug("Sending notification for {0}".format(message))

        return self._sendBoxcar2(message, title, accesstoken)
