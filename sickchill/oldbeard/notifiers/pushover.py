# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
import time

import requests

from sickchill import logger, settings
from sickchill.oldbeard.common import (
    NOTIFY_DOWNLOAD,
    NOTIFY_GIT_UPDATE,
    NOTIFY_GIT_UPDATE_TEXT,
    NOTIFY_LOGIN,
    NOTIFY_LOGIN_TEXT,
    NOTIFY_SNATCH,
    NOTIFY_SUBTITLE_DOWNLOAD,
    notifyStrings,
)
from sickchill.oldbeard.helpers import make_session

API_URL = "https://api.pushover.net/1/messages.json"


class Notifier(object):
    def __init__(self):
        self.api_url = "https://api.pushover.net/1/messages.json"
        self.session = make_session()

    def test_notify(self, userKey=None, apiKey=None):
        return self._notify_pushover("This is a test notification from SickChill", "Test", userKey=userKey, apiKey=apiKey, force=True)

    def _send_pushover(self, msg, title, sound=None, userKey=None, apiKey=None, priority=None):
        """
        Sends a pushover notification to the address provided

        msg: The message to send (str)
        title: The title of the message
        sound: The notification sound to use
        userKey: The pushover user id to send the message to (or to subscribe with)
        apiKey: The pushover api key to use
        returns: True if the message succeeded, False otherwise
        """

        userKey = userKey or settings.PUSHOVER_USERKEY
        apiKey = apiKey or settings.PUSHOVER_APIKEY
        sound = sound or settings.PUSHOVER_SOUND
        priority = priority or settings.PUSHOVER_PRIORITY

        if not (userKey and apiKey):
            logger.warning("You must set a user key and api key to use pushover")
            return False

        logger.debug("Pushover API KEY in use: " + apiKey)

        try:
            data = {
                "token": apiKey,
                "user": userKey,
                "title": title,
                "message": msg.strip(),
                "timestamp": int(time.time()),
                "retry": 60,
                "expire": 3600,
                "priority": priority,
            }

            if sound and sound != "default":
                data["sound"] = sound

            if settings.PUSHOVER_DEVICE:
                data["device"] = settings.PUSHOVER_DEVICE

            response = self.session.post(self.api_url, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            if error.response:
                print(error.response)

                # HTTP status 404 if the provided email address isn't a Pushover user.
                if error.response.status_code == 404:
                    logger.warning("Username is wrong/not a pushover email. Pushover will send an email to it")
                # For HTTP status code 401's, it is because you are passing in either an invalid token, or the user has not added your service.
                elif error.response.status_code == 401:
                    # HTTP status 401 if the user doesn't have the service added
                    subscribe_note = self._send_pushover(msg, title, sound=sound, userKey=userKey, apiKey=apiKey)
                    if subscribe_note:
                        logger.debug("Subscription sent")
                        return True
                    else:
                        logger.warning("Subscription could not be sent")
                # If you receive an HTTP status code of 400, it is because you failed to send the proper parameters
                elif error.response.status_code == 400:
                    logger.warning("Wrong data sent to pushover")

                # If you receive a HTTP status code of 429, it is because the message limit has been reached (free limit is 7,500)
                elif error.response.status_code == 429:
                    logger.warning("Pushover API message limit reached - try a different API key")

                return False

            logger.warning(f"Pushover notification failed. {error}")
            return False

        logger.info("Pushover notification successful.")
        return True

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if settings.PUSHOVER_NOTIFY_ONSNATCH:
            self._notify_pushover(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if settings.PUSHOVER_NOTIFY_ONDOWNLOAD:
            self._notify_pushover(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if settings.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_pushover(title, ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if settings.USE_PUSHOVER:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notify_pushover(title, update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_PUSHOVER:
            update_text = notifyStrings[NOTIFY_LOGIN_TEXT]
            title = notifyStrings[NOTIFY_LOGIN]
            self._notify_pushover(title, update_text.format(ipaddress))

    def _notify_pushover(self, title, message, sound=None, userKey=None, apiKey=None, force=False):
        """
        Sends a pushover notification based on the provided info or SR config

        title: The title of the notification to send
        message: The message string to send
        sound: The notification sound to use
        userKey: The userKey to send the notification to
        apiKey: The apiKey to use to send the notification
        force: Enforce sending, for instance for testing
        """

        if not settings.USE_PUSHOVER and not force:
            logger.debug("Notification for Pushover not enabled, skipping this notification")
            return False

        logger.debug("Sending notification for " + message)

        return self._send_pushover(message, title, sound=sound, userKey=userKey, apiKey=apiKey)
