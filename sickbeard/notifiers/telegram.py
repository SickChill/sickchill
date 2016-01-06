# coding=utf-8

# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Aaron Bieber <deftly@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.
import urllib
import urllib2

import sickbeard
from sickbeard import logger
from sickbeard.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT, NOTIFY_GIT_UPDATE_TEXT


class TelegramNotifier(object):

    def test_notify(self, id=None, apiKey=None):
        return self._notifyTelegram('Test', "This is a test notification from SickRage", id, apiKey, force=True)

    def _sendTelegramMsg(self, title, msg, id=None, apiKey=None):
        """
        Sends a Telegram notification

        title: The title of the notification to send
        msg: The message string to send
        id: The Telegram user/group id to send the message to
        apikey: Your Telegram bot API token

        returns: True if the message succeeded, False otherwise
        """

        if id is None:
            id = sickbeard.TELEGRAM_ID
        if apiKey is None:
            apiKey = sickbeard.TELEGRAM_APIKEY

        logger.log(u"Telegram in use with API KEY: " + apiKey, logger.DEBUG)

        message = title.encode('utf-8') + ": " + msg.encode('utf-8')
        payload = urllib.urlencode({'chat_id': id, 'text': message})
        TELEGRAM_API = "https://api.telegram.org/bot%s/%s"

        req = urllib2.Request(TELEGRAM_API % (apiKey, "sendMessage"), payload)

        try:
            urllib2.urlopen(req)
        except IOError as e:
            if hasattr(e, 'code'):
                if e.code == 400:
                    message = "Missing parameter(s)."
                    logger.log(message, logger.ERROR)
                    return False, message
                if e.code == 401:
                    message = "Authentication failed."
                    logger.log(message, logger.ERROR)
                    return False, message
                if e.code == 420:
                    message = "Too many messages."
                    logger.log(message, logger.ERROR)
                    return False, message
                if e.code == 500:
                    message = "Server error. Please retry in few moment."
                    logger.log(message, logger.ERROR)
                    return False, message
        except Exception as e:
            message = u"Error while sending Telegram message: {0}".format(e)
            logger.log(message, logger.ERROR)
            return False, message

        message = "Telegram message sent successfully."
        logger.log(message, logger.INFO)
        return True, message

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickbeard.TELEGRAM_NOTIFY_ONSNATCH:
            self._notifyTelegram(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickbeard.TELEGRAM_NOTIFY_ONDOWNLOAD:
            self._notifyTelegram(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyTelegram(title, ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_TELEGRAM:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyTelegram(title, update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_TELEGRAM:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notifyTelegram(title, update_text.format(ipaddress))

    def _notifyTelegram(self, title, message, id=None, apiKey=None, force=False):
        """
        Sends a Telegram notification

        title: The title of the notification to send
        message: The message string to send
        id: The Telegram user/group id to send the message to
        apikey: Your Telegram bot API token
        force: Enforce sending, for instance for testing
        """

        if not sickbeard.USE_TELEGRAM and not force:
            logger.log("Notification for Telegram not enabled, skipping this notification", logger.DEBUG)
            return False, "Disabled"

        logger.log("Sending a Telegram message for " + message, logger.DEBUG)

        return self._sendTelegramMsg(title, message, id, apiKey)


notifier = TelegramNotifier
