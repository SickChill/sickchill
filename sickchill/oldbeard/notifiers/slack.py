import json

import requests

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):

    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/"
    SLACK_ICON_URL = "https://github.com/SickChill/SickChill/raw/master/sickchill/gui/slick/images/sickchill-sc.png"

    def notify_snatch(self, ep_name):
        if settings.SLACK_NOTIFY_SNATCH:
            self._notify_slack(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name):
        if settings.SLACK_NOTIFY_DOWNLOAD:
            self._notify_slack(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.SLACK_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify_slack(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if settings.USE_SLACK:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_slack(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_SLACK:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_slack(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_slack("This is a test notification from SickChill", force=True)

    def _send_slack(self, message=None):
        slack_webhook = self.SLACK_WEBHOOK_URL + settings.SLACK_WEBHOOK.replace(self.SLACK_WEBHOOK_URL, "")
        slack_icon_emoji = settings.SLACK_ICON_EMOJI

        logger.info("Sending slack message: " + message)
        logger.info("Sending slack message  to url: " + slack_webhook)

        headers = {"Content-Type": "application/json"}
        try:
            r = requests.post(
                slack_webhook,
                data=json.dumps(dict(text=message, username="SickChillBot", icon_emoji=slack_icon_emoji, icon_url=self.SLACK_ICON_URL)),
                headers=headers,
            )
            r.raise_for_status()
        except Exception as e:
            logger.exception("Error Sending Slack message: " + str(e))
            return False

        return True

    def _notify_slack(self, message="", force=False):
        if not settings.USE_SLACK and not force:
            return False

        return self._send_slack(message)
