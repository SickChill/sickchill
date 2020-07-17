# -*- coding: utf-8 -*
# Author: Pedro Correia (https://github.com/pedrocorreia/)
# Based on pushalot.py by Nic Wolfe <nic@wolfeden.ca>
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
# Third Party Imports
from requests.compat import urljoin

# First Party Imports
import sickbeard
from sickbeard import common, helpers, logger

# Local Folder Imports
from .base import AbstractNotifier


class Notifier(AbstractNotifier):

    def __init__(self):
        self.session = helpers.make_session()
        self.url = 'https://api.pushbullet.com/v2/'

    def test_notify(self, pushbullet_api):
        logger.debug('Sending a test Pushbullet notification.')
        return self._sendPushbullet(
            pushbullet_api,
            event='Test',
            message='Testing Pushbullet settings from SickChill',
            force=True
        )

    def get_devices(self, pushbullet_api):
        logger.debug('Testing Pushbullet authentication and retrieving the device list.')
        headers = {'Access-Token': pushbullet_api}
        return helpers.getURL(urljoin(self.url, 'devices'), session=self.session, headers=headers, returns='text') or {}

    def get_channels(self, pushbullet_api):
        """Fetches the list of channels a given access key has permissions to push to"""
        logger.debug('Testing Pushbullet authentication and retrieving the device list.')
        headers = {'Access-Token': pushbullet_api}
        return helpers.getURL(urljoin(self.url, 'channels'), session=self.session, headers=headers, returns='text') or {}

    def notify_snatch(self, name):
        if self.config('snatch'):
            self._sendPushbullet(
                pushbullet_api=None,
                event=common.notifyStrings[common.NOTIFY_SNATCH] + ' : ' + name,
                message=name
            )

    def notify_download(self, name):
        if self.config('download'):
            self._sendPushbullet(
                pushbullet_api=None,
                event=common.notifyStrings[common.NOTIFY_DOWNLOAD] + ' : ' + name,
                message=name
            )

    def notify_subtitle_download(self, name, lang):
        if self.config('subtitle'):
            self._sendPushbullet(
                pushbullet_api=None,
                event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' : ' + name + ' : ' + lang,
                message=name + ': ' + lang
            )

    def notify_git_update(self, new_version='??'):
        self._sendPushbullet(
            pushbullet_api=None,
            event=common.notifyStrings[common.NOTIFY_GIT_UPDATE],
            message=common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT] + new_version,
            # link=link
        )

    def notify_login(self, ipaddress=''):
        self._sendPushbullet(
            pushbullet_api=None,
            event=common.notifyStrings[common.NOTIFY_LOGIN],
            message=common.notifyStrings[common.NOTIFY_LOGIN_TEXT].format(ipaddress)
        )

    def _sendPushbullet(
            self, pushbullet_api=None, pushbullet_device=None, pushbullet_channel=None, event=None, message=None, link=None, force=False):

        if not (self.config('enabled') or force):
            return False

        pushbullet_api = pushbullet_api or sickbeard.PUSHBULLET_API
        pushbullet_device = pushbullet_device or sickbeard.PUSHBULLET_DEVICE
        pushbullet_channel = pushbullet_channel or sickbeard.PUSHBULLET_CHANNEL

        logger.debug('Pushbullet event: {0!r}'.format(event))
        logger.debug('Pushbullet message: {0!r}'.format(message))
        logger.debug('Pushbullet api: {0!r}'.format(pushbullet_api))
        logger.debug('Pushbullet devices: {0!r}'.format(pushbullet_device))

        post_data = {
            'title': event,
            'body': message,
            'type': 'link' if link else 'note'
        }
        if link:
            post_data['url'] = link

        headers = {'Access-Token': pushbullet_api}

        if pushbullet_device:
            post_data['device_iden'] = pushbullet_device
        elif pushbullet_channel:
            post_data['channel_tag'] = pushbullet_channel

        response = helpers.getURL(urljoin(self.url, 'pushes'), session=self.session, post_data=post_data, headers=headers, returns='json') or {}

        failed = response.pop('error', {})
        if failed:
            logger.warning('Pushbullet notification failed: {0}'.format(failed.pop('message')))
        else:
            logger.debug('Pushbullet notification sent.')

        return False if failed else True
