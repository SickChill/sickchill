# coding=utf-8

# Author: Mhynlo<mhynlo@mhynlo.io>
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import json

import requests
import six

import sickbeard
from sickbeard import common, logger
from sickchill.helper.exceptions import ex


class Notifier(object):

    def notify_snatch(self, ep_name):
        if sickbeard.DISCORD_NOTIFY_SNATCH:
            self._notify_discord(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickbeard.DISCORD_NOTIFY_DOWNLOAD:
            self._notify_discord(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.DISCORD_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify_discord(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_DISCORD:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_discord(title + " - " + update_text + new_version)

    def notify_login(self, ip_address=""):
        if sickbeard.USE_DISCORD:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_discord(title + " - " + update_text.format(ip_address))

    def test_notify(self):
        return self._notify_discord("This is a test notification from SickChill", force=True)

    def _send_discord(self, message=None):
        discord_webhook = sickbeard.DISCORD_WEBHOOK
        discord_name = sickbeard.DISCORD_NAME
        avatar_icon = sickbeard.DISCORD_AVATAR_URL
        discord_tts = bool(sickbeard.DISCORD_TTS)

        logger.log("Sending discord message: " + message, logger.INFO)
        logger.log("Sending discord message  to url: " + discord_webhook, logger.INFO)

        if isinstance(message, six.text_type):
            message = message.encode('utf-8')

        headers = {b"Content-Type": b"application/json"}
        try:
            r = requests.post(discord_webhook, data=json.dumps(dict(content=message, username=discord_name, avatar_url=avatar_icon, tts=discord_tts)), headers=headers)
            r.raise_for_status()
        except Exception as e:
            logger.log("Error Sending Discord message: " + ex(e), logger.ERROR)
            return False

        return True

    def _notify_discord(self, message='', force=False):
        if not sickbeard.USE_DISCORD and not force:
            return False

        return self._send_discord(message)
