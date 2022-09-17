# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
import urllib.parse
import urllib.request

from sickchill import logger, settings
from sickchill.oldbeard.common import (
    NOTIFY_DOWNLOAD,
    NOTIFY_LOGIN,
    NOTIFY_LOGIN_TEXT,
    NOTIFY_SNATCH,
    NOTIFY_SUBTITLE_DOWNLOAD,
    NOTIFY_UPDATE,
    NOTIFY_UPDATE_TEXT,
    notifyStrings,
)


class Notifier(object):
    def test_notify(self, cust_id=None, apiKey=None):
        return self._notifyFreeMobile("Test", "This is a test notification from SickChill", cust_id, apiKey, force=True)

    @staticmethod
    def _sendFreeMobileSMS(title, msg, cust_id=None, apiKey=None):
        """
        Sends a SMS notification

        msg: The message to send (str)
        title: The title of the message
        userKey: The pushover user id to send the message to (or to subscribe with)

        returns: True if the message succeeded, False otherwise
        """

        if cust_id is None:
            cust_id = settings.FREEMOBILE_ID
        if apiKey is None:
            apiKey = settings.FREEMOBILE_APIKEY

        logger.debug("Free Mobile in use with API KEY: " + apiKey)

        # build up the URL and parameters
        msg = msg.strip()
        msg_quoted = urllib.parse.quote(title + ": " + msg)
        URL = "https://smsapi.free-mobile.fr/sendmsg?user=" + cust_id + "&pass=" + apiKey + "&msg=" + msg_quoted

        req = urllib.request.Request(URL)
        # send the request to Free Mobile
        try:
            urllib.request.urlopen(req)
        except IOError as error:
            if hasattr(error, "code"):
                if error.code == 400:
                    message = "Missing parameter(s)."
                    logger.exception(message)
                    return False, message
                if error.code == 402:
                    message = "Too much SMS sent in a short time."
                    logger.exception(message)
                    return False, message
                if error.code == 403:
                    message = "API service isn't enabled in your account or ID / API key is incorrect."
                    logger.exception(message)
                    return False, message
                if error.code == 500:
                    message = "Server error. Please retry in few moment."
                    logger.exception(message)
                    return False, message
        except Exception as error:
            message = f"Error while sending SMS: {error}"
            logger.exception(message)
            return False, message

        message = "Free Mobile SMS successful."
        logger.info(message)
        return True, message

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if settings.FREEMOBILE_NOTIFY_ONSNATCH:
            self._notifyFreeMobile(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if settings.FREEMOBILE_NOTIFY_ONDOWNLOAD:
            self._notifyFreeMobile(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if settings.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyFreeMobile(title, ep_name + ": " + lang)

    def notify_update(self, new_version="??"):
        if settings.USE_FREEMOBILE:
            update_text = notifyStrings[NOTIFY_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_UPDATE]
            self._notifyFreeMobile(title, update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_FREEMOBILE:
            update_text = notifyStrings[NOTIFY_LOGIN_TEXT]
            title = notifyStrings[NOTIFY_LOGIN]
            self._notifyFreeMobile(title, update_text.format(ipaddress))

    def _notifyFreeMobile(self, title, message, cust_id=None, apiKey=None, force=False):
        """
        Sends a SMS notification

        title: The title of the notification to send
        message: The message string to send
        cust_id: Your Free Mobile customer ID
        apikey: Your Free Mobile API key
        force: Enforce sending, for instance for testing
        """

        if not settings.USE_FREEMOBILE and not force:
            logger.debug("Notification for Free Mobile not enabled, skipping this notification")
            return False, "Disabled"

        logger.debug("Sending a SMS for " + message)

        return self._sendFreeMobileSMS(title, message, cust_id, apiKey)
