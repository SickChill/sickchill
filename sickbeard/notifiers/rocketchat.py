# coding=utf-8

# Author: Patrick Begley<forge33@gmail.com>, Chris Burton <cyberhiker@gmail.com>
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
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import json

# Third Party Imports
import requests
import six

# First Party Imports
import sickbeard
from sickbeard import common, logger
from sickchill.helper.exceptions import ex


class Notifier(object):

    ROCKETCHAT_ICON_URL = 'https://github.com/SickChill/SickChill/raw/master/gui/slick/images/sickchill-sc.png'

    def notify_snatch(self, ep_name):
        if sickbeard.ROCKETCHAT_NOTIFY_SNATCH:
            self._notify_rocketchat(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickbeard.ROCKETCHAT_NOTIFY_DOWNLOAD:
            self._notify_rocketchat(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify_rocketchat(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_ROCKETCHAT:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_rocketchat(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_ROCKETCHAT:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_rocketchat(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_rocketchat("This is a test notification from SickChill", force=True)

    def _send_rocketchat(self, message=None):
        rocketchat_webhook = sickbeard.ROCKETCHAT_WEBHOOK
        rocketchat_icon_emoji = sickbeard.ROCKETCHAT_ICON_EMOJI

        logger.log("Sending rocketchat message: " + message, logger.INFO)
        logger.log("Sending rocketchat message to url: " + rocketchat_webhook, logger.INFO)

        if isinstance(message, six.text_type):
            message = message.encode('utf-8')

        headers = {b"Content-Type": b"application/json"}
        try:
            r = requests.post(rocketchat_webhook, data=json.dumps(dict(text=message, attachments=(dict(icon_emoji=rocketchat_icon_emoji, author_icon=self.ROCKETCHAT_ICON_URL)))), headers=headers)
            r.raise_for_status()
        except Exception as e:
            logger.log("Error Sending RocketChat message: " + ex(e), logger.ERROR)
            return False

        return True

    def _notify_rocketchat(self, message='', force=False):
        if not sickbeard.USE_ROCKETCHAT and not force:
            return False

        return self._send_rocketchat(message)
