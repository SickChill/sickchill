# coding=utf-8
# Author: Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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

from sickrage.helper import HTTP_STATUS_CODES


class Notifier(object):
    """
    Use Join to send notifications

    http://joaoapps.com/join/
    """
    def test_notify(self, id=None):
        """
        Send a test notification
        :param id: The Device ID
        :returns: the notification
        """
        return self._notify_join('Test', 'This is a test notification from SickRage', id, force=True)

    def _send_join_msg(self, title, msg, id=None):
        """
        Sends a Join notification

        :param title: The title of the notification to send
        :param msg: The message string to send
        :param id: The Device ID

        :returns: True if the message succeeded, False otherwise
        """
        id = sickbeard.JOIN_ID if id is None else id

        logger.log('Join in use with device ID: {0}'.format(id), logger.DEBUG)

        message = '{0} : {1}'.format(title.encode(), msg.encode())
        params = {   
            "deviceId": id,
            "title": title,
            "text": message,
            "icon": "https://raw.githubusercontent.com/SickRage/SickRage/master/gui/slick/images/sickrage.png"
        }
        payload = urllib.urlencode(params)
        req = 'https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?' + payload

        logger.log('Join iurl : {0}'.format(join_api), logger.DEBUG)
        success = False
        try:
            urllib2.urlopen(req)
            message = 'Join message sent successfully.'
            logger.log('Join message returned : {0}'.format(message), logger.DEBUG) 
            success = True
        except IOError as e:
            message = 'Unknown IO error: {0}'.format(e)
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
                    HTTP_STATUS_CODES.get(e.code, message)
        except Exception as e:
            message = 'Error while sending Join message: {0} '.format(e)
        finally:
            logger.log(message, logger.INFO)
            return success, message

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        """
        Sends a Join notification when an episode is snatched

        :param ep_name: The name of the episode snatched
        :param title: The title of the notification to send
        """
        if sickbeard.JOIN_NOTIFY_ONSNATCH:
            self._notify_join(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        """
        Sends a Join notification when an episode is downloaded

        :param ep_name: The name of the episode downloaded
        :param title: The title of the notification to send
        """
        if sickbeard.JOIN_NOTIFY_ONDOWNLOAD:
            self._notify_join(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        """
        Sends a Join notification when subtitles for an episode are downloaded

        :param ep_name: The name of the episode subtitles were downloaded for
        :param lang: The language of the downloaded subtitles
        :param title: The title of the notification to send
        """
        if sickbeard.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_join(title, '{0}: {1}'.format(ep_name, lang))

    def notify_git_update(self, new_version='??'):
        """
        Sends a Join notification for git updates

        :param new_version: The new version available from git
        """
        if sickbeard.USE_JOIN:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notify_join(title, update_text + new_version)

    def notify_login(self, ipaddress=''):
        """
        Sends a Join notification on login

        :param ipaddress: The IP address the login is originating from
        """
        if sickbeard.USE_JOIN:
            update_text = notifyStrings[NOTIFY_LOGIN_TEXT]
            title = notifyStrings[NOTIFY_LOGIN]
            self._notify_join(title, update_text.format(ipaddress))

    def _notify_join(self, title, message, id=None, force=False):
        """
        Sends a Join notification

        :param title: The title of the notification to send
        :param message: The message string to send
        :param id: The Device ID
        :param force: Enforce sending, for instance for testing

        :returns: the message to send
        """

        if not (force or sickbeard.USE_JOIN):
            logger.log('Notification for Join not enabled, skipping this notification', logger.DEBUG)
            return False, 'Disabled'

        logger.log('Sending a Join message for {0}'.format(message), logger.DEBUG)

        return self._send_join_msg(title, message, id)
