import json

import requests
from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):

    ROCKETCHAT_ICON_URL = "https://github.com/SickChill/SickChill/raw/master/sickchill/gui/slick/images/sickchill-sc.png"

    def notify_snatch(self, ep_name):
        if settings.ROCKETCHAT_NOTIFY_SNATCH:
            self._notify_rocketchat(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name):
        if settings.ROCKETCHAT_NOTIFY_DOWNLOAD:
            self._notify_rocketchat(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify_rocketchat(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if settings.USE_ROCKETCHAT:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_rocketchat(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_ROCKETCHAT:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_rocketchat(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_rocketchat("This is a test notification from SickChill", force=True)

    def _send_rocketchat(self, message=None):
        rocketchat_webhook = settings.ROCKETCHAT_WEBHOOK
        rocketchat_icon_emoji = settings.ROCKETCHAT_ICON_EMOJI

        logger.info("Sending rocketchat message: " + message)
        logger.info("Sending rocketchat message to url: " + rocketchat_webhook)

        headers = CaseInsensitiveDict({"Content-Type": "application/json"})
        try:
            r = requests.post(
                rocketchat_webhook,
                data=json.dumps(dict(text=message, attachments=(dict(icon_emoji=rocketchat_icon_emoji, author_icon=self.ROCKETCHAT_ICON_URL)))),
                headers=headers,
            )
            r.raise_for_status()
        except Exception as e:
            logger.exception("Error Sending RocketChat message: " + str(e))
            return False

        return True

    def _notify_rocketchat(self, message="", force=False):
        if not settings.USE_ROCKETCHAT and not force:
            return False

        return self._send_rocketchat(message)
