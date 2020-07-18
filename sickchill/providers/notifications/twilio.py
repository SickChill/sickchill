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
# Stdlib Imports
import re

# Third Party Imports
from twilio.base.exceptions import TwilioRestException
from twilio.rest import TwilioRestClient

# First Party Imports
from sickbeard import common, logger

# Local Folder Imports
from .base import AbstractNotifier


class Notifier(AbstractNotifier):
    def __init__(self):
        super().__init__('Twilio', extra_options=('to_number', 'account_id', 'auth_token', 'phone_sid'))

        self.number_regex = re.compile(r'^\+1-\d{3}-\d{3}-\d{4}$')
        self.account_regex = re.compile(r'^AC[a-z0-9]{32}$')
        self.auth_regex = re.compile(r'^[a-z0-9]{32}$')
        self.phone_regex = re.compile(r'^PN[a-z0-9]{32}$')

    def notify_snatch(self, name):
        if self.config('snatch'):
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + name)

    def notify_download(self, name):
        if self.config('download'):
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + name)

    def notify_subtitle_download(self, name, lang):
        if self.config('subtitle'):
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + name + ': ' + lang)

    def notify_git_update(self, new_version):
        if self.config('update'):
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            self._notifyTwilio(update_text + new_version)

    def notify_login(self, ipaddress=""):
        if self.config('enabled'):
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notifyTwilio(title + " - " + update_text.format(ipaddress))

    def notify_postprocess(self, name):
        if self.config('process'):
            title = common.notifyStrings[common.NOTIFY_POSTPROCESS]
            self._notifyTwilio(title + " - " + name)

    def test_notify(self):
        try:
            if not self.number.capabilities['sms']:
                return False
            return self._notifyTwilio(_('This is a test notification from SickChill'), force=True, allow_raise=True)
        except TwilioRestException:
            return False

    @property
    def number(self):
        return self.client.phone_numbers.get(self.config('phone_sid'))

    @property
    def client(self):
        return TwilioRestClient(self.config('account_id'), self.config('auth_token'))

    def _notifyTwilio(self, message='', force=False, allow_raise=False):
        if not (self.config('enabled') or force or self.number_regex.match(self.config('to_number'))):
            return False

        logger.debug('Sending Twilio SMS: ' + message)

        try:
            self.client.messages.create(
                body=message,
                to=self.config('to_number'),
                from_=self.number.phone_number,
            )
        except TwilioRestException as e:
            logger.exception('Twilio notification failed:' + str(e))

            if allow_raise:
                raise e

        return True
