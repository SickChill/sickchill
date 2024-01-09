import json

import requests
from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):
    MATTERMOSTBOT_POST_URI = "/api/v4/posts"
    MATTERMOSTBOT_ICON_URL = "https://github.com/SickChill/SickChill/raw/master/sickchill/gui/slick/images/sickchill-sc.png"

    def notify_snatch(self, ep_name):
        if settings.MATTERMOSTBOT_NOTIFY_SNATCH:
            self._notify_mattermostbot(common.notifyStrings[common.NOTIFY_SNATCH], ep_name, "s")

    def notify_download(self, ep_name):
        if settings.MATTERMOSTBOT_NOTIFY_DOWNLOAD:
            self._notify_mattermostbot(common.notifyStrings[common.NOTIFY_DOWNLOAD], ep_name, "d")

    def notify_subtitle_download(self, ep_name, lang):
        if settings.MATTERMOSTBOT_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify_mattermostbot(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD], ep_name + " - " + lang, "sd")

    def notify_update(self, new_version="??"):
        if settings.USE_MATTERMOSTBOT:
            update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_UPDATE]
            self._notify_mattermostbot("Update", title + " - " + update_text + new_version, "u")

    def notify_login(self, ipaddress=""):
        if settings.USE_MATTERMOSTBOT:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_mattermostbot("Login", title + " - " + update_text.format(ipaddress), "l")

    def test_notify(self):
        action = "Testing"
        message = "Serie name - S0E0 - Episode Name - Quality specs"
        tmsg = "t"
        return self._notify_mattermostbot(action, message, tmsg, force=True)

    def _send_mattermostbot(self, action="", message="", tmsg="t"):
        logger.info("Action: " + action + " | Message: " + message + " | tmsg: " + tmsg)
        mattermostbot_post_url = settings.MATTERMOSTBOT_URL + self.MATTERMOSTBOT_POST_URI
        mattermostbot_author = settings.MATTERMOSTBOT_AUTHOR
        mattermostbot_post_url.replace("//api", "/api")
        mattermostbot_icon_emoji = settings.MATTERMOSTBOT_ICON_EMOJI
        logger.info("Sending mattermost bot message: " + message + " towards " + mattermostbot_post_url)
        logger.info("Sending mattermost bot action: " + action)

        headers = CaseInsensitiveDict({"Content-Type": "application/json", "Authorization": "Bearer " + settings.MATTERMOSTBOT_TOKEN})
        contents = message.split(" - ")

        if tmsg == "s":
            color = "#ffff50"
            pretext = "Snatch/Start"
        elif tmsg == "d":
            color = "#009900"
            pretext = "Finish"
        elif tmsg == "t":
            color = "#0000ff"
            pretext = "Testing"
        else:
            color = "#ff0000"
            pretext = "Type: " + tmsg

        payload = {"channel_id": settings.MATTERMOSTBOT_CHANNEL, "message": "SickChill Work", "props": {"attachments": []}}
        payload["channel_id"] = settings.MATTERMOSTBOT_CHANNEL
        payload["props"]["attachments"] = []
        payload["props"]["attachments"].append({"pretext": pretext, "author_name": mattermostbot_author, "color": color, "fields": {}})
        payload["props"]["attachments"][0]["fields"] = []
        payload["props"]["attachments"][0]["fields"].append({"title": "Series", "value": contents[0], "short": "true"})
        payload["props"]["attachments"][0]["fields"].append({"title": "EP", "value": contents[1], "short": "true"})
        payload["props"]["attachments"][0]["fields"].append({"title": "Title", "value": contents[2], "short": "true"})
        payload["props"]["attachments"][0]["fields"].append({"title": "Quality", "value": contents[3], "short": "true"})

        try:
            r = requests.post(
                mattermostbot_post_url,
                data=json.dumps(payload),
                headers=headers,
            )
            r.raise_for_status()
        except Exception as error:
            logger.exception(f"Error Sending Mattermost Bot message: {error}")
            return False

        return True

    def _notify_mattermostbot(self, act="", message="", tmsg="", force=False):
        if not settings.USE_MATTERMOSTBOT and not force:
            logger.debug("Notification for Mattermost Bot not enabled, skipping this notification")
            return False

        return self._send_mattermostbot(act, message, tmsg)
