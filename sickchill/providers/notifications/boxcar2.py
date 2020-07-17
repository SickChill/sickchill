# coding=utf-8
# Author: Rafael Silva <rpluto@gmail.com>
# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://sickchill.github.io
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
# First Party Imports
import sickbeard
from sickbeard import common, logger

# Local Folder Imports
from .base import AbstractNotifier


class Notifier(AbstractNotifier):
    def __init__(self):
        super().__init__('Boxcar2', extra_options=tuple(['access_token']))
        self.session = sickbeard.helpers.make_session()
        self.url = 'https://new.boxcar.io/api/notifications'

    def test_notify(self, accesstoken, title='SickChill : Test'):
        return self._sendBoxcar2('This is a test notification from SickChill', title, accesstoken)

    def _sendBoxcar2(self, msg, title, accesstoken):
        '''
        Sends a boxcar2 notification to the address provided

        msg: The message to send
        title: The title of the message
        accesstoken: to send to this device

        returns: True if the message succeeded, False otherwise
        '''
        # http://blog.boxcar.io/post/93211745502/boxcar-api-update-boxcar-api-update-icon-and

        post_data = {
            'user_credentials': accesstoken,
            'notification[title]': 'SickChill : {0}: {1}'.format(title, msg),
            'notification[long_message]': msg,
            'notification[sound]': 'notifier-2',
            'notification[source_name]': 'SickChill',
            'notification[icon_url]': sickbeard.LOGO_URL
        }

        response = sickbeard.helpers.getURL(self.url, post_data=post_data, session=self.session, timeout=60, returns='json')
        if not response:
            logger.exception('Boxcar2 notification failed.')
            return False

        logger.debug('Boxcar2 notification successful.')
        return True

    def notify_snatch(self, name, title=common.notifyStrings[common.NOTIFY_SNATCH]):
        if self.config('snatch'):
            self._notifyBoxcar2(title, name)

    def notify_download(self, name, title=common.notifyStrings[common.NOTIFY_DOWNLOAD]):
        if self.config('download'):
            self._notifyBoxcar2(title, name)

    def notify_subtitle_download(self, name, lang, title=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD]):
        if self.config('subtitle'):
            self._notifyBoxcar2(title, name + ': ' + lang)

    def notify_git_update(self, new_version='??'):
        if self.config('update'):
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notifyBoxcar2(title, update_text + new_version)

    def notify_login(self, ipaddress=''):
        if self.config('login'):
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notifyBoxcar2(title, update_text.format(ipaddress))

    def notify_postprocess(self, name):
        if self.config('process'):
            title = common.notifyStrings[common.NOTIFY_POSTPROCESS]
            self._notifyBoxcar2(title, name)

    def _notifyBoxcar2(self, title, message, accesstoken=None):
        '''
        Sends a boxcar2 notification based on the provided info or SB config

        title: The title of the notification to send
        message: The message string to send
        accesstoken: to send to this device
        '''

        if not self.config('enabled'):
            logger.debug('Notification for Boxcar2 not enabled, skipping this notification')
            return False

        accesstoken = accesstoken or self.config('access_token')

        logger.debug('Sending notification for {0}'.format(message))

        return self._sendBoxcar2(message, title, accesstoken)
