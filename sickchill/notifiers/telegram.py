from __future__ import annotations

from sickchill import logger, settings
from sickchill.common import (
    NOTIFY_DOWNLOAD,
    NOTIFY_LOGIN,
    NOTIFY_LOGIN_TEXT,
    NOTIFY_SNATCH,
    NOTIFY_SUBTITLE_DOWNLOAD,
    NOTIFY_UPDATE,
    NOTIFY_UPDATE_TEXT,
    notifyStrings,
)
from sickchill.helper.helpers import make_session


def _redact_telegram_secret(text, token) -> str:
    message = str(text)
    if token:
        message = message.replace(str(token), "***")
    return message


class Notifier(object):
    def __init__(self):
        self.session = make_session()

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if settings.TELEGRAM_NOTIFY_ONSNATCH:
            self._notify(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if settings.TELEGRAM_NOTIFY_ONDOWNLOAD:
            self._notify(title, ep_name)

    def notify_postprocess(self, ep_name):
        if settings.TELEGRAM_NOTIFY_ONDOWNLOAD:
            self._notify(notifyStrings[NOTIFY_DOWNLOAD], ep_name)

    def notify_subtitle_download(self, ep_name, lang="", title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if settings.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify(title, f"{ep_name}: {lang}")

    def notify_update(self, new_version="??"):
        self._notify(notifyStrings[NOTIFY_UPDATE], notifyStrings[NOTIFY_UPDATE_TEXT] + new_version)

    def notify_login(self, ipaddress=""):
        self._notify(notifyStrings[NOTIFY_LOGIN], notifyStrings[NOTIFY_LOGIN_TEXT].format(ipaddress))

    def test_notify(self, id=None, api_key=None):
        return self._notify("Test", "This is a test notification from SickChill", id=id, api_key=api_key, force=True)

    def _notify(self, title, message, id=None, api_key=None, force=False):
        if not (force or settings.USE_TELEGRAM):
            logger.debug("Notification for Telegram not enabled, skipping this notification")
            return False, "Disabled"
        chat_id = id or settings.TELEGRAM_ID
        token = api_key or settings.TELEGRAM_APIKEY
        logger.debug("Sending a Telegram message for %s", message)
        params = {"chat_id": chat_id, "text": f"{title} : {message}"}
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            http = self.session.get(url, params=params, timeout=30)
            http.raise_for_status()
            response = http.json()
        except Exception as error:
            logger.warning("Telegram request failed: %s", _redact_telegram_secret(error, token))
            return False, "Sending Telegram message failed, check the log"
        result_message = ("Sending Telegram message failed, check the log", "Telegram message sent successfully.")[bool(response)]
        logger.info(result_message)
        return bool(response), result_message
