# coding=utf-8
# Author: Maciej Olesinski (https://github.com/molesinski/)
# Based on prowl.py by Nic Wolfe <nic@wolfeden.ca>
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
        self.session = sickbeard.helpers.make_session()

    def test_notify(self, pushalot_authorizationtoken):
        return self._sendPushalot(
            pushalot_authorizationtoken=pushalot_authorizationtoken,
            event='Test',
            message='Testing Pushalot settings from SickChill',
            force=True
        )

    def notify_snatch(self, name):
        if self.config('snatch'):
            self._sendPushalot(
                pushalot_authorizationtoken=None,
                event=common.notifyStrings[common.NOTIFY_SNATCH],
                message=name
            )

    def notify_download(self, name):
        if self.config('download'):
            self._sendPushalot(
                pushalot_authorizationtoken=None,
                event=common.notifyStrings[common.NOTIFY_DOWNLOAD],
                message=name
            )

    def notify_subtitle_download(self, name, lang):
        if self.config('subtitle'):
            self._sendPushalot(
                pushalot_authorizationtoken=None,
                event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD],
                message='{0}:{1}'.format(name, lang)
            )

    def notify_git_update(self, new_version='??'):
        update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
        self._sendPushalot(
            pushalot_authorizationtoken=None,
            event=title,
            message=update_text + new_version
        )

    def notify_login(self, ipaddress=''):
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._sendPushalot(
            pushalot_authorizationtoken=None,
            event=title,
            message=update_text.format(ipaddress)
        )

    def _sendPushalot(self, pushalot_authorizationtoken=None, event=None, message=None, force=False):

        if not (self.config('enabled') or force):
            return False

        pushalot_authorizationtoken = pushalot_authorizationtoken or sickbeard.PUSHALOT_AUTHORIZATIONTOKEN

        logger.debug('Pushalot event: {0}'.format(event))
        logger.debug('Pushalot message: {0}'.format(message))
        logger.debug('Pushalot api: {0}'.format(pushalot_authorizationtoken))

        post_data = {
            'AuthorizationToken': pushalot_authorizationtoken,
            'Title': event or '',
            'Body': message or ''
        }

        jdata = sickbeard.helpers.getURL(
            'https://pushalot.com/api/sendmessage',
            post_data=post_data, session=self.session,
            returns='json'
        ) or {}

        '''
        {'Status': 200, 'Description': 'The request has been completed successfully.', 'Success': True}
        '''

        success = jdata.pop('Success', False)
        if success:
            logger.debug('Pushalot notifications sent.')
        else:
            logger.error('Pushalot notification failed: {0} {1}'.format(
                jdata.get('Status', ''),
                jdata.get('Description', 'Unknown')
            ))

        return success
