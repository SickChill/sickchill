# -*- coding: utf-8 -*
# Author: Pedro Correia (http://github.com/pedrocorreia/)
# Based on pushalot.py by Nic Wolfe <nic@wolfeden.ca>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import json
import requests
import traceback

import sickbeard
from sickbeard import logger
from sickbeard.common import notifyStrings
from sickbeard.common import NOTIFY_SNATCH
from sickbeard.common import NOTIFY_DOWNLOAD
from sickbeard.common import NOTIFY_GIT_UPDATE
from sickbeard.common import NOTIFY_GIT_UPDATE_TEXT
from sickbeard.common import NOTIFY_SUBTITLE_DOWNLOAD


class PushbulletNotifier(object):
    session = requests.Session()
    TEST_EVENT = 'Test'

    def __init__(self):
        pass

    def test_notify(self, pushbullet_api):
        logger.log(u"Sending a test Pushbullet notification.", logger.DEBUG)
        return self._sendPushbullet(pushbullet_api, event=self.TEST_EVENT, message="Testing Pushbullet settings from SickRage")

    def get_devices(self, pushbullet_api):
        logger.log(u"Testing Pushbullet authentication and retrieving the device list.", logger.DEBUG)
        return self._sendPushbullet(pushbullet_api)

    def notify_snatch(self, ep_name):
        if sickbeard.PUSHBULLET_NOTIFY_ONSNATCH:
            self._sendPushbullet(pushbullet_api=None, event=notifyStrings[NOTIFY_SNATCH] + " : " + ep_name, message=ep_name)

    def notify_download(self, ep_name):
        if sickbeard.PUSHBULLET_NOTIFY_ONDOWNLOAD:
            self._sendPushbullet(pushbullet_api=None, event=notifyStrings[NOTIFY_DOWNLOAD] + " : " + ep_name, message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendPushbullet(pushbullet_api=None, event=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD] + " : " + ep_name + " : " + lang, message=ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_PUSHBULLET:
            self._sendPushbullet(pushbullet_api=None, event=notifyStrings[NOTIFY_GIT_UPDATE], message=notifyStrings[NOTIFY_GIT_UPDATE_TEXT] + new_version)

    def _sendPushbullet(self, pushbullet_api=None, pushbullet_device=None, event=None, message=None):

        if not (sickbeard.USE_PUSHBULLET or event is 'Test' or event is None):
            return False

        pushbullet_api = pushbullet_api or sickbeard.PUSHBULLET_API
        pushbullet_device = pushbullet_device or sickbeard.PUSHBULLET_DEVICE

        logger.log(u"Pushbullet event: %r" % event, logger.DEBUG)
        logger.log(u"Pushbullet message: %r" % message, logger.DEBUG)
        logger.log(u"Pushbullet api: %r" % pushbullet_api, logger.DEBUG)
        logger.log(u"Pushbullet devices: %r" % pushbullet_device, logger.DEBUG)
        logger.log(u"Pushbullet notification type: %r" % 'note' if event else 'None', logger.DEBUG)

        url = 'https://api.pushbullet.com/v2/%s' % ('devices', 'pushes')[event is not None]

        data = json.dumps({
            'title': event.encode('utf-8'),
            'body': message.encode('utf-8'),
            'device_iden': pushbullet_device.encode('utf-8'),
            'type': 'note'
        }) if event else None

        method = 'GET' if data is None else 'POST'
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % pushbullet_api}

        try:
            response = self.session.request(method, url, data=data, headers=headers)
        except Exception:
            logger.log(u'Pushbullet authorization failed with exception: %r' % traceback.format_exc(), logger.DEBUG)
            return False

        if response.status_code == 410:
            logger.log(u'Pushbullet authorization failed', logger.DEBUG)
            return False

        if response.status_code != 200:
            logger.log(u'Pushbullet call failed with error code %r' % response.status_code, logger.DEBUG)
            return False

        logger.log(u"Pushbullet response: %r" % response.text, logger.DEBUG)

        if not response.text:
            logger.log(u"Pushbullet notification failed.", logger.ERROR)
            return False

        logger.log(u"Pushbullet notifications sent.", logger.DEBUG)
        return (True, response.text)[event is self.TEST_EVENT or event is None]


notifier = PushbulletNotifier
