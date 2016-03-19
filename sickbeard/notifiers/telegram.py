# coding=utf-8
# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Aaron Bieber <deftly@gmail.com>
# URL: https://sickrage.github.io
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import urllib
import urllib2

import sickbeard
from sickbeard import logger
from sickbeard.common import notifyStrings, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT, NOTIFY_LOGIN, NOTIFY_LOGIN_TEXT, \
    NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD

from sickrage.helper.common import http_status_code


class Notifier(object):
    """
    Use Telegram to send notifications

    https://telegram.org/
    """
    def test_notify(self, id=None, api_key=None):
        """
        Send a test notification
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token
        :returns: the notification
        """
        return self._notify_telegram('Test', 'This is a test notification from SickRage', id, api_key, force=True)

    def _send_telegram_msg(self, title, msg, id=None, api_key=None):
        """
        Sends a Telegram notification

        :param title: The title of the notification to send
        :param msg: The message string to send
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token

        :returns: True if the message succeeded, False otherwise
        """
        id = sickbeard.TELEGRAM_ID if id is None else id
        api_key = sickbeard.TELEGRAM_APIKEY if api_key is None else api_key

        logger.log('Telegram in use with API KEY: {0!s}'.format(api_key), logger.DEBUG)

        message = '{0!s} : {1!s}'.format(title.encode(), msg.encode())
        payload = urllib.urlencode({'chat_id': id, 'text': message})
        telegram_api = 'https://api.telegram.org/bot%s/%s'

        req = urllib2.Request(telegram_api % (api_key, 'sendMessage'), payload)

        success = False
        try:
            urllib2.urlopen(req)
            message = 'Telegram message sent successfully.'
            success = True
        except IOError as e:
            message = 'Unknown IO error: {0!s}'.format(e)
            if hasattr(e, b'code'):
                error_message = {
                    400: 'Missing parameter(s). Double check your settings or if the channel/user exists.',
                    401: 'Authentication failed.',
                    420: 'Too many messages.',
                    500: 'Server error. Please retry in a few moments.',
                }
                if e.code in error_message:
                    message = error_message.get(e.code)
                else:
                    http_status_code.get(e.code, message)
        except Exception as e:
            message = 'Error while sending Telegram message: {0!s} '.format(e)
        finally:
            logger.log(message, logger.INFO)
            return success, message

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        """
        Sends a Telegram notification when an episode is snatched

        :param ep_name: The name of the episode snatched
        :param title: The title of the notification to send
        """
        if sickbeard.TELEGRAM_NOTIFY_ONSNATCH:
            self._notify_telegram(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        """
        Sends a Telegram notification when an episode is downloaded

        :param ep_name: The name of the episode downloaded
        :param title: The title of the notification to send
        """
        if sickbeard.TELEGRAM_NOTIFY_ONDOWNLOAD:
            self._notify_telegram(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        """
        Sends a Telegram notification when subtitles for an episode are downloaded

        :param ep_name: The name of the episode subtitles were downloaded for
        :param lang: The language of the downloaded subtitles
        :param title: The title of the notification to send
        """
        if sickbeard.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_telegram(title, '{0!s}: {1!s}'.format(ep_name, lang))

    def notify_git_update(self, new_version='??'):
        """
        Sends a Telegram notification for git updates

        :param new_version: The new version available from git
        """
        if sickbeard.USE_TELEGRAM:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notify_telegram(title, update_text + new_version)

    def notify_login(self, ipaddress=''):
        """
        Sends a Telegram notification on login

        :param ipaddress: The ip address the login is originating from
        """
        if sickbeard.USE_TELEGRAM:
            update_text = notifyStrings[NOTIFY_LOGIN_TEXT]
            title = notifyStrings[NOTIFY_LOGIN]
            self._notify_telegram(title, update_text.format(ipaddress))

    def _notify_telegram(self, title, message, id=None, api_key=None, force=False):
        """
        Sends a Telegram notification

        :param title: The title of the notification to send
        :param message: The message string to send
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token
        :param force: Enforce sending, for instance for testing

        :returns: the message to send
        """

        if not (force or sickbeard.USE_TELEGRAM):
            logger.log('Notification for Telegram not enabled, skipping this notification', logger.DEBUG)
            return False, 'Disabled'

        logger.log('Sending a Telegram message for {0!s}'.format(message), logger.DEBUG)

        return self._send_telegram_msg(title, message, id, api_key)
