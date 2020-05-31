# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
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

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import re

# First Party Imports
import sickbeard
from sickbeard import common, logger
from sickchill.helper.exceptions import ex

# import twilio



class Notifier(object):

    number_regex = re.compile(r'^\+1-\d{3}-\d{3}-\d{4}$')
    account_regex = re.compile(r'^AC[a-z0-9]{32}$')
    auth_regex = re.compile(r'^[a-z0-9]{32}$')
    phone_regex = re.compile(r'^PN[a-z0-9]{32}$')

    def notify_snatch(self, ep_name):
        if sickbeard.TWILIO_NOTIFY_ONSNATCH:
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickbeard.TWILIO_NOTIFY_ONDOWNLOAD:
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ': ' + lang)

    def notify_git_update(self, new_version):
        if sickbeard.USE_TWILIO:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            self._notifyTwilio(update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_TWILIO:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notifyTwilio(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        try:
            if not self.number.capabilities['sms']:
                return False


            return self._notifyTwilio(_('This is a test notification from SickChill'), force=True, allow_raise=True)
        except twilio.TwilioRestException:
            return False

    @property
    def number(self):
        return self.client.phone_numbers.get(sickbeard.TWILIO_PHONE_SID)

    @property
    def client(self):
        return twilio.rest.TwilioRestClient(sickbeard.TWILIO_ACCOUNT_SID, sickbeard.TWILIO_AUTH_TOKEN)

    def _notifyTwilio(self, message='', force=False, allow_raise=False):
        if not (sickbeard.USE_TWILIO or force or self.number_regex.match(sickbeard.TWILIO_TO_NUMBER)):
            return False

        logger.log('Sending Twilio SMS: ' + message, logger.DEBUG)

        try:
            self.client.messages.create(
                body=message,
                to=sickbeard.TWILIO_TO_NUMBER,
                from_=self.number.phone_number,
            )
        except twilio.TwilioRestException as e:
            logger.log('Twilio notification failed:' + ex(e), logger.ERROR)

            if allow_raise:
                raise e

        return True
