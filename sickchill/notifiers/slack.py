from __future__ import annotations

import json

import requests
from requests.structures import CaseInsensitiveDict

from sickchill import common, logger, settings


class Notifier(object):
    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/"
    SLACK_ICON_URL = "https://github.com/SickChill/SickChill/raw/master/sickchill/gui/slick/images/sickchill-sc.png"

    def notify_snatch(self, ep_name):
        if settings.SLACK_NOTIFY_SNATCH:
            self._notify(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name):
        if settings.SLACK_NOTIFY_DOWNLOAD:
            self._notify(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_postprocess(self, ep_name):
        if settings.SLACK_NOTIFY_DOWNLOAD:
            self._notify(common.notifyStrings[common.NOTIFY_POSTPROCESS] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.SLACK_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_update(self, new_version="??"):
        update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_UPDATE]
        self._notify(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._notify(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify("This is a test notification from SickChill", force=True)

    def _notify(self, message="", force=False):
        if not settings.USE_SLACK and not force:
            logger.debug("Notification for Slack not enabled, skipping this notification")
            return False
        return self._send(message)

    def _send(self, message=None):
        webhook = settings.SLACK_WEBHOOK or ""
        slack_webhook = self.SLACK_WEBHOOK_URL + str(webhook).replace(self.SLACK_WEBHOOK_URL, "")
        icon_emoji = settings.SLACK_ICON_EMOJI or ""
        logger.info("Sending slack message: %s", message)
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
            logger.exception("Error Sending Slack message: %s", error)
            return False
        return True
