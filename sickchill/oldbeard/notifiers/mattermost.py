import json

import requests
from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):
    MATTERMOST_WEBHOOK_URL = ""
    MATTERMOST_ICON_URL = "https://github.com/SickChill/SickChill/raw/master/sickchill/gui/slick/images/sickchill-sc.png"

    def notify_snatch(self, ep_name):
        if settings.MATTERMOST_NOTIFY_SNATCH:
            self._notify_mattermost(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name):
        if settings.MATTERMOST_NOTIFY_DOWNLOAD:
            self._notify_mattermost(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.MATTERMOST_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify_mattermost(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_update(self, new_version="??"):
        if settings.USE_MATTERMOST:
            update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_UPDATE]
            self._notify_mattermost(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_MATTERMOST:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_mattermost(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_mattermost("This is a test notification from SickChill", force=True)

    def _send_mattermost(self, message=None):
        mattermost_webhook = self.MATTERMOST_WEBHOOK_URL + settings.MATTERMOST_WEBHOOK.replace(self.MATTERMOST_WEBHOOK_URL, "")
        mattermost_icon_emoji = settings.MATTERMOST_ICON_EMOJI
        mattermost_user = settings.MATTERMOST_USERNAME

        logger.info("Sending mattermost webhook message: " + message)
        logger.info("Sending mattermost webhook message to url: " + mattermost_webhook)

        headers = CaseInsensitiveDict({"Content-Type": "application/json"})

        try:
            r = requests.post(
                mattermost_webhook,
                data=json.dumps(dict(text=message, username=mattermost_user, icon_emoji=mattermost_icon_emoji, icon_url=self.MATTERMOST_ICON_URL)),
                headers=headers,
            )
            r.raise_for_status()
        except Exception as error:
            logger.exception(f"Error Sending Mattermost webhook message: {error}")
            return False

        return True

    def _notify_mattermost(self, message="", force=False):
        if not settings.USE_MATTERMOST and not force:
            logger.debug("Notification for Mattermost webhook not enabled, skipping this notification")
            return False

        return self._send_mattermost(message)
