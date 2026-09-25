from __future__ import annotations

import json
from typing import ClassVar

import requests
from requests.structures import CaseInsensitiveDict

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
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import NotifierPlugin


@register
class GotifyNotifier(NotifierPlugin):
    id = "gotify"
    name = "Gotify"
    version = "1.0.0"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Gotify",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_gotify",)),
        Field(name="host", type="url", default="", required=True, legacy_keys=("gotify_host",)),
        Field(name="authorizationtoken", type="password", default="", required=True, secret=True, legacy_keys=("gotify_authorizationtoken",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("gotify_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("gotify_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("gotify_notify_onsubtitledownload",)),
    )

    def notify_snatch(self, ep_name: str, title=notifyStrings[NOTIFY_SNATCH]) -> None:
        if self.ctx.get("notify_onsnatch"):
            self._notify(title, ep_name)

    def notify_download(self, ep_name: str, title=notifyStrings[NOTIFY_DOWNLOAD]) -> None:
        if self.ctx.get("notify_ondownload"):
            self._notify(title, ep_name)

    def notify_postprocess(self, ep_name: str) -> None:
        if self.ctx.get("notify_ondownload"):
            self._notify(notifyStrings[NOTIFY_DOWNLOAD], ep_name)

    def notify_subtitle_download(self, ep_name: str, lang: str = "", title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]) -> None:
        if self.ctx.get("notify_onsubtitledownload"):
            self._notify(title, f"{ep_name}: {lang}")

    def notify_update(self, new_version: str = "??") -> None:
        self._notify(notifyStrings[NOTIFY_UPDATE], notifyStrings[NOTIFY_UPDATE_TEXT] + new_version)

    def notify_login(self, ipaddress: str = "") -> None:
        self._notify(notifyStrings[NOTIFY_LOGIN], notifyStrings[NOTIFY_LOGIN_TEXT].format(ipaddress))

    def test_notify(self, host=None, token=None):
        return self._notify("Test", "This is a test notification from SickChill", host=host, token=token, force=True)

    def test(self) -> tuple[bool, str]:
        ok, error = self.test_notify()
        return bool(ok), "ok" if ok else str(error)

    def _notify(self, title, message, host=None, token=None, force=False):
        if not (force or self.ctx.get("enabled")):
            self.ctx.logger.debug("Notification for Gotify not enabled, skipping this notification")
            return False, "Disabled"
        host = host or self.ctx.get("host") or ""
        token = token or self.ctx.get("authorizationtoken") or ""
        if host and not str(host).endswith("/"):
            host = f"{host}/"
        self.ctx.logger.debug("Sending a Gotify message %s", message)
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
            self.ctx.logger.exception("Error Sending Gotify message: %s", error)
            return False, error
        return True, None
