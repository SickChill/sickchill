import json
import time

import requests
from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):
    def notify_snatch(self, ep_name):
        if settings.MATRIX_NOTIFY_SNATCH:
            show = self._parseEp(ep_name)
            message = f"""<body>
                        <h3>SickChill Notification - Snatched</h3>
                        <p>Show: <b>{show[0]}</b></p><p>Episode Number: <b>{show[1]}</b></p><p>Episode: <b>{show[2]}</b></p><p>Quality: <b>{show[3]}</b></p>
                        <h5>Powered by SickChill.</h5></body>"""
            self._notify_matrix(message)

    def notify_download(self, ep_name):
        if settings.MATRIX_NOTIFY_DOWNLOAD:
            show = self._parseEp(ep_name)
            message = f"""<body>
                        <h3>SickChill Notification - Downloaded</h3>
                        <p>Show: <b>{show[0]}</b></p><p>Episode Number: <b>{show[1]}</b></p><p>Episode: <b>{show[2]}</b></p><p>Quality: <b>{show[3]}</b></p>
                        <h5 style="margin-top: 2.5em; padding: .7em 0;
                        color: #777; border-top: #BBB solid 1px;">
                        Powered by SickChill.</h5></body>"""
            self._notify_matrix(message)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.MATRIX_NOTIFY_SUBTITLEDOWNLOAD:
            show = self._parseEp(ep_name)
            message = f"""<body>
                        <h3>SickChill Notification - Subtitle Downloaded</h3>
                        <p>Show: <b>{show[0]}</b></p><p>Episode Number: <b>{show[1]}</b></p><p>Episode: <b>{show[2]}</b></p></p>
                        <p>Language: <b>{lang}</b></p>
                        <h5>Powered by SickChill.</h5></body>"""
            self._notify_matrix(message)

    def notify_git_update(self, new_version="??"):
        if settings.USE_MATRIX:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_matrix(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_MATRIX:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_matrix(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_matrix("This is a test notification from SickChill", force=True)

    @staticmethod
    def _send_matrix(message=None):
        url = f"https://{settings.MATRIX_SERVER}/_matrix/client/r0/rooms/{settings.MATRIX_ROOM}/send/m.room.message/{time.time()}?access_token={settings.MATRIX_API_TOKEN}"

        logger.info("Sending matrix message: " + message)
        logger.info("Sending matrix message to url: " + url)

        jsonMessage = {
            "msgtype": "m.text",
            "format": "org.matrix.custom.html",
            "body": message,
            "formatted_body": message,
        }

        headers = CaseInsensitiveDict({"Content-Type": "application/json"})
        try:
            r = requests.put(url, data=json.dumps(jsonMessage), headers=headers)
            r.raise_for_status()

        except Exception as e:
            logger.exception(f"Error Sending Matrix message: {e}")
            return False

        return True

    def _notify_matrix(self, message="", force=False):
        if not settings.USE_MATRIX and not force:
            return False

        return self._send_matrix(message)

    @staticmethod
    def _parseEp(ep_name):
        sep = " - "
        titles = ep_name.split(sep)
        logger.debug(f"TITLES: {titles}")
        return titles
