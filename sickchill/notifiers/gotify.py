from __future__ import annotations

import json

import requests
from requests.structures import CaseInsensitiveDict

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


class Notifier(object):
    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if settings.GOTIFY_NOTIFY_ONSNATCH:
            self._notify(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if settings.GOTIFY_NOTIFY_ONDOWNLOAD:
            self._notify(title, ep_name)

    def notify_postprocess(self, ep_name):
        if settings.GOTIFY_NOTIFY_ONDOWNLOAD:
            self._notify(notifyStrings[NOTIFY_DOWNLOAD], ep_name)

    def notify_subtitle_download(self, ep_name, lang="", title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if settings.GOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify(title, f"{ep_name}: {lang}")

    def notify_update(self, new_version="??"):
        self._notify(notifyStrings[NOTIFY_UPDATE], notifyStrings[NOTIFY_UPDATE_TEXT] + new_version)

    def notify_login(self, ipaddress=""):
        self._notify(notifyStrings[NOTIFY_LOGIN], notifyStrings[NOTIFY_LOGIN_TEXT].format(ipaddress))

    def test_notify(self, host=None, token=None):
        return self._notify("Test", "This is a test notification from SickChill", host=host, token=token, force=True)

    def _notify(self, title, message, host=None, token=None, force=False):
        if not (force or settings.USE_GOTIFY):
            logger.debug("Notification for Gotify not enabled, skipping this notification")
            return False, "Disabled"
        host = host or settings.GOTIFY_HOST or ""
        token = token or settings.GOTIFY_AUTHORIZATIONTOKEN or ""
        if host and not str(host).endswith("/"):
            host = f"{host}/"
        logger.debug("Sending a Gotify message %s", message)
        headers = CaseInsensitiveDict({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
        try:
            response = requests.post(
                f"{host}message",
                data=json.dumps(dict(title=title, message=f"{title} : {message}")),
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
        except Exception as error:
            logger.exception("Error Sending Gotify message: %s", error)
            return False, error
        return True, None
