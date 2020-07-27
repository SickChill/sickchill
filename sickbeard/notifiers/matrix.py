# coding=utf-8
# Author: Joao Santos <jmigueltsantos@riseup.net>
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
# Stdlib Imports
import json
import time

# Third Party Imports
import requests

# First Party Imports
from sickbeard import common, logger
from sickchill import settings


class Notifier(object):

    def notify_snatch(self, ep_name):
        if settings.MATRIX_NOTIFY_SNATCH:
            show = self._parseEp(ep_name)
            message = '''<body>
                        <h3>SickChill Notification - Snatched</h3>
                        <p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p><p>Quality: <b>{3}</b></p>
                        <h5>Powered by SickChill.</h5></body>'''.format(show[0], show[1], show[2], show[3])
            self._notify_matrix(message)

    def notify_download(self, ep_name):
        if settings.MATRIX_NOTIFY_DOWNLOAD:
            show = self._parseEp(ep_name)
            message = '''<body>
                        <h3>SickChill Notification - Downloaded</h3>
                        <p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p><p>Quality: <b>{3}</b></p>
                        <h5 style="margin-top: 2.5em; padding: .7em 0;
                        color: #777; border-top: #BBB solid 1px;">
                        Powered by SickChill.</h5></body>'''.format(show[0], show[1], show[2], show[3])
            self._notify_matrix(message)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.MATRIX_NOTIFY_SUBTITLEDOWNLOAD:
            show = self._parseEp(ep_name)
            message = '''<body>
                        <h3>SickChill Notification - Subtitle Downloaded</h3>
                        <p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p></p>
                        <p>Language: <b>{3}</b></p>
                        <h5>Powered by SickChill.</h5></body>'''.format(show[0], show[1], show[2], lang)
            self._notify_matrix(message)

    def notify_git_update(self, new_version="??"):
        if settings.USE_MATRIX:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_matrix(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_MATRIX:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_matrix(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_matrix("This is a test notification from SickChill", force=True)

    def _send_matrix(self, message=None):
        url = 'https://{0}/_matrix/client/r0/rooms/{1}/send/m.room.message/{2}?access_token={3}'.format(settings.MATRIX_SERVER,
                                                                                                        settings.MATRIX_ROOM, time.time(),
                                                                                                        settings.MATRIX_API_TOKEN)

        logger.info("Sending matrix message: " + message)
        logger.info("Sending matrix message to url: " + url)

        jsonMessage={
            "msgtype": "m.text",
            "format": "org.matrix.custom.html",
            "body": message,
            "formatted_body": message,
        }

        headers = {"Content-Type": "application/json"}
        try:
            r = requests.put(url , data=json.dumps(jsonMessage), headers=headers)
            r.raise_for_status()

        except Exception as e:
            logger.exception("Error Sending Matrix message: " + str(e))
            return False

        return True

    def _notify_matrix(self, message='', force=False):
        if not settings.USE_MATRIX and not force:
            return False

        return self._send_matrix(message)

    @staticmethod
    def _parseEp(ep_name):
        sep = ' - '
        titles = ep_name.split(sep)
        logger.debug('TITLES: {0}'.format(titles))
        return titles
