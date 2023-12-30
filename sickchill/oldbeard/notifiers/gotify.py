import json

import requests
from requests.structures import CaseInsensitiveDict

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
from sickchill.oldbeard.helpers import make_session


class Notifier(object):
    """
    Use Gotify to send notifications

    https://gotify.net/
    """

    def __init__(self):
        self.session = make_session()

    def test_notify(self, host=None, token=None):
        """
        Send a test notification

        :param host: The host where Gotify is running (incl port)
        :param token: Gotify authorization token
        :returns: the notification
        """
        return self._notify_gotify("Test", "This is a test notification from SickChill", host, token, force=True)

    def _send_gotify_msg(self, title, msg, host=None, token=None):
        """
        Send a Gotify notification

        :param title: The title of the notification to send
        :param msg: The message string to send
        :param host: The host where Gotify is running (incl port)
        :param token: Gotify authorization token
        :return: True if the message succeeded, False otherwise and error
        """
        logger.debug("Gotify in use with authorization token.")
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {token or settings.GOTIFY_AUTHORIZATIONTOKEN}"
        try:
            r = requests.post(
                f"{host}message",
                data=json.dumps(dict(title=title, message=f"{title} : {msg}")),
                headers=headers,
            )
            r.raise_for_status()
        except Exception as error:
            logger.exception(f"Error Sending Gotify message: {error}")
            return False, error
        return True, None

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        """
        Sends a Gotify notification when an episode is snatched

        :param ep_name: The name of the episode snatched
        :param title: The title of the notification to send
        """
        if settings.GOTIFY_NOTIFY_ONSNATCH:
            self._notify_gotify(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        """
        Sends a Gotify notification when an episode is downloaded

        :param ep_name: The name of the episode downloaded
        :param title: The title of the notification to send
        """
        if settings.GOTIFY_NOTIFY_ONDOWNLOAD:
            self._notify_gotify(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        """
        Sends a Gotify notification when subtitles for an episode are downloaded

        :param ep_name: The name of the episode subtitles were downloaded for
        :param lang: The language of the downloaded subtitles
        :param title: The title of the notification to send
        """
        if settings.GOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_gotify(title, "{0}: {1}".format(ep_name, lang))

    def notify_update(self, new_version="??"):
        """
        Sends a Gotify notification for git updates

        :param new_version: The new version available from git
        """
        if settings.USE_GOTIFY:
            update_text = notifyStrings[NOTIFY_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_UPDATE]
            self._notify_gotify(title, update_text + new_version)

    def notify_login(self, ipaddress=""):
        """
        Sends a Gotify notification on login

        :param ipaddress: The ip address the login is originating from
        """
        if settings.USE_GOTIFY:
            update_text = notifyStrings[NOTIFY_LOGIN_TEXT]
            title = notifyStrings[NOTIFY_LOGIN]
            self._notify_gotify(title, update_text.format(ipaddress))

    def _notify_gotify(self, title, message, host, token=None, force=False):
        """
        Sends a Gotify notification

        :param title: The title of the notification to send
        :param message: The message string to send
        :param host: The host where Gotify is running (incl port)
        :param token: Gotify authorization token
        :param force: Enforce sending, for instance for testing

        :returns: the message to send
        """

        if not (force or settings.USE_GOTIFY):
            logger.debug("Notification for Gotify not enabled, skipping this notification")
            return False, "Disabled"

        logger.debug("Sending a Gotify message {0}".format(message))

        return self._send_gotify_msg(title, message, host, token)
