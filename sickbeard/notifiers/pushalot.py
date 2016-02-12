# coding=utf-8

# Author: Maciej Olesinski (https://github.com/molesinski/)
# Based on prowl.py by Nic Wolfe <nic@wolfeden.ca>
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

import socket
from httplib import HTTPSConnection, HTTPException
from urllib import urlencode
from ssl import SSLError

import sickbeard
from sickbeard import logger, common


class Notifier(object):
    def test_notify(self, pushalot_authorizationtoken):
        return self._sendPushalot(pushalot_authorizationtoken, event="Test",
                                  message="Testing Pushalot settings from SickRage", force=True)

    def notify_snatch(self, ep_name):
        if sickbeard.PUSHALOT_NOTIFY_ONSNATCH:
            self._sendPushalot(pushalot_authorizationtoken=None, event=common.notifyStrings[common.NOTIFY_SNATCH],
                               message=ep_name)

    def notify_download(self, ep_name):
        if sickbeard.PUSHALOT_NOTIFY_ONDOWNLOAD:
            self._sendPushalot(pushalot_authorizationtoken=None, event=common.notifyStrings[common.NOTIFY_DOWNLOAD],
                               message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendPushalot(pushalot_authorizationtoken=None,
                               event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD],
                               message=ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_PUSHALOT:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._sendPushalot(pushalot_authorizationtoken=None,
                               event=title,
                               message=update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_PUSHALOT:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._sendPushalot(pushalot_authorizationtoken=None,
                               event=title,
                               message=update_text.format(ipaddress))

    def _sendPushalot(self, pushalot_authorizationtoken=None, event=None, message=None, force=False):

        if not sickbeard.USE_PUSHALOT and not force:
            return False

        if pushalot_authorizationtoken is None:
            pushalot_authorizationtoken = sickbeard.PUSHALOT_AUTHORIZATIONTOKEN

        logger.log(u"Pushalot event: " + event, logger.DEBUG)
        logger.log(u"Pushalot message: " + message, logger.DEBUG)
        logger.log(u"Pushalot api: " + pushalot_authorizationtoken, logger.DEBUG)

        http_handler = HTTPSConnection("pushalot.com")

        data = {'AuthorizationToken': pushalot_authorizationtoken,
                'Title': event.encode('utf-8'),
                'Body': message.encode('utf-8')}

        try:
            http_handler.request("POST",
                                 "/api/sendmessage",
                                 headers={'Content-type': "application/x-www-form-urlencoded"},
                                 body=urlencode(data))
        except (SSLError, HTTPException, socket.error):
            logger.log(u"Pushalot notification failed.", logger.ERROR)
            return False
        response = http_handler.getresponse()
        request_status = response.status

        if request_status == 200:
            logger.log(u"Pushalot notifications sent.", logger.DEBUG)
            return True
        elif request_status == 410:
            logger.log(u"Pushalot auth failed: %s" % response.reason, logger.ERROR)
            return False
        else:
            logger.log(u"Pushalot notification failed.", logger.ERROR)
            return False
