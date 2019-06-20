# coding=utf-8

# Author: Dustyn Gibson <miigotu@gmail.com>
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

from __future__ import print_function, unicode_literals

from _base import NotifierBase

import sickbeard
from sickbeard.notifiers import (boxcar2, desktop_notifications, discord, emailnotify, emby, freemobile, growl, join, kodi, matrix, nmj, nmjv2, plex, prowl,
                                 pushalot, pushbullet, pushover, pytivo, slack, synoindex, synologynotifier, telegram, trakt, tweet, twilio_notify)


class NotificationsController(NotifierBase):
    def __init__(self):
        self.options = {}
        self.notifiers = {}

    def __del__(self):
        pass

    def __getattr__(self, item):
        if item in self.notifiers:
            return self.notifiers[item]
        return self.notifiers[item]

    def __getitem__(self, item):
        if item in self.notifiers:
            return self.notifiers[item]

        notifier = import_the_thing.Notifier()
        self.notifiers[item] = notifier
        return self.notifiers[item]

    def enable(self, item):
        pass

    def disable(self, item):
        pass

    def notify_download(self, ep_name):
        for notifier in self.notifiers:
            notifier.notify_download(self, ep_name)

    def notify_git_update(self, new_version=""):
        if self.NOTIFY_ON_UPDATE:
            for notifier in self.notifiers:
                notifier.notify_git_update(new_version)

    def notify_login(self, ip_address):
        if self.NOTIFY_ON_LOGIN and not sickbeard.helpers.is_ip_private(ip_address):
            for notifier in self.notifiers:
                notifier.notify_login(ip_address)

    def notify_postprocess(self, ep_name):
        if self.NOTIFY_POSTPROCESS:
            for notifier in self.notifiers:
                notifier.notify_postprocess(ep_name)

    def notify_snatch(self, ep_name):
        for notifier in self.notifiers:
            notifier.notify_snatch(self, ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        for notifier in self.notifiers:
            notifier.notify_subtitle_download(self, ep_name, lang)

    def test_notify(self):
        pass
