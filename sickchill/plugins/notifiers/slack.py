from __future__ import annotations

import json
from typing import ClassVar

import requests
from requests.structures import CaseInsensitiveDict

from sickchill.oldbeard import common
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import NotifierPlugin


@register
class SlackNotifier(NotifierPlugin):
    id = "slack"
    name = "Slack"
    version = "1.0.0"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Slack",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_slack",)),
        Field(name="webhook", type="url", default="", required=True, legacy_keys=("slack_webhook",)),
        Field(name="icon_emoji", type="str", default="", legacy_keys=("slack_icon_emoji",)),
        Field(name="notify_snatch", type="bool", default=False, legacy_keys=("slack_notify_snatch",)),
        Field(name="notify_download", type="bool", default=False, legacy_keys=("slack_notify_download",)),
        Field(name="notify_subtitledownload", type="bool", default=False, legacy_keys=("slack_notify_subtitledownload",)),
    )

    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/"
    SLACK_ICON_URL = "https://github.com/SickChill/SickChill/raw/master/sickchill/gui/slick/images/sickchill-sc.png"

    def notify_snatch(self, ep_name: str) -> None:
        if self.ctx.get("notify_snatch"):
            self._notify(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name: str) -> None:
        if self.ctx.get("notify_download"):
            self._notify(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_postprocess(self, ep_name: str) -> None:
        if self.ctx.get("notify_download"):
            self._notify(common.notifyStrings[common.NOTIFY_POSTPROCESS] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name: str, lang: str = "") -> None:
        if self.ctx.get("notify_subtitledownload"):
            self._notify(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_update(self, new_version: str = "??") -> None:
        update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_UPDATE]
        self._notify(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress: str = "") -> None:
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._notify(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify("This is a test notification from SickChill", force=True)

    def test(self) -> tuple[bool, str]:
        ok = bool(self.test_notify())
        return ok, "ok" if ok else "failed"

    def _notify(self, message: str = "", force: bool = False) -> bool:
        if not self.ctx.get("enabled") and not force:
            self.ctx.logger.debug("Notification for Slack not enabled, skipping this notification")
            return False
        return self._send(message)

    def _send(self, message: str | None = None) -> bool:
        webhook = self.ctx.get("webhook") or ""
        slack_webhook = self.SLACK_WEBHOOK_URL + str(webhook).replace(self.SLACK_WEBHOOK_URL, "")
        icon_emoji = self.ctx.get("icon_emoji") or ""
        self.ctx.logger.info("Sending slack message: %s", message)
        headers = CaseInsensitiveDict({"Content-Type": "application/json"})
        try:
            response = requests.post(
                slack_webhook,
                data=json.dumps(dict(text=message, username="SickChillBot", icon_emoji=icon_emoji, icon_url=self.SLACK_ICON_URL)),
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
        except Exception as error:
            self.ctx.logger.exception("Error Sending Slack message: %s", error)
            return False
        return True
