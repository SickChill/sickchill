# coding=utf-8

# Author: Rafael Silva <rpluto@gmail.com>
# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
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
import sickbeard

from sickbeard import logger, common


class Notifier(object):
    def __init__(self):
        self.session = sickbeard.helpers.make_session()
        self.url = 'https://new.boxcar.io/api/notifications'

    def test_notify(self, accesstoken, title='SickRage : Test'):
        return self._sendBoxcar2('This is a test notification from SickRage', title, accesstoken)

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
            'notification[title]': 'SickRage : {0}: {1}'.format(title, msg),
            'notification[long_message]': msg,
            'notification[sound]': 'notifier-2',
            'notification[source_name]': 'SickRage',
            'notifications[icon_url]': sickbeard.LOGO_URL
        }

        response = sickbeard.helpers.getURL(self.url, post_data=post_data, session=self.session, timeout=60, returns='json')
        if not response:
            logger.log('Boxcar2 notification failed.', logger.ERROR)
            return False

        logger.log('Boxcar2 notification successful.', logger.DEBUG)
        return True

    def notify_snatch(self, ep_name, title=common.notifyStrings[common.NOTIFY_SNATCH]):
        if sickbeard.BOXCAR2_NOTIFY_ONSNATCH:
            self._notifyBoxcar2(title, ep_name)

    def notify_download(self, ep_name, title=common.notifyStrings[common.NOTIFY_DOWNLOAD]):
        if sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD:
            self._notifyBoxcar2(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyBoxcar2(title, ep_name + ': ' + lang)

    def notify_git_update(self, new_version='??'):
        update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
        self._notifyBoxcar2(title, update_text + new_version)

    def notify_login(self, ipaddress=''):
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._notifyBoxcar2(title, update_text.format(ipaddress))

    def _notifyBoxcar2(self, title, message, accesstoken=None):
        '''
        Sends a boxcar2 notification based on the provided info or SB config

        title: The title of the notification to send
        message: The message string to send
        accesstoken: to send to this device
        '''

        if not sickbeard.USE_BOXCAR2:
            logger.log('Notification for Boxcar2 not enabled, skipping this notification', logger.DEBUG)
            return False

        accesstoken = accesstoken or sickbeard.BOXCAR2_ACCESSTOKEN

        logger.log('Sending notification for {0}'.format(message), logger.DEBUG)

        return self._sendBoxcar2(message, title, accesstoken)
