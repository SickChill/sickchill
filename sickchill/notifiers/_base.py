# coding=utf-8
from __future__ import unicode_literals

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


class NotifierBase(object):
    NOTIFY_SNATCH = False
    NOTIFY_DOWNLOAD = False
    NOTIFY_SUBTITLE_DOWNLOAD = False
    NOTIFY_UPDATE = False
    NOTIFY_LOGIN = False
    NOTIFY_POSTPROCESS = False

    def __init__(self):
        self.enabled = False
        self.defaults = {
            'NOTIFY_SNATCH': self.NOTIFY_SNATCH,
            'NOTIFY_DOWNLOAD': self.NOTIFY_DOWNLOAD,
            'NOTIFY_SUBTITLE_DOWNLOAD': self.NOTIFY_SUBTITLE_DOWNLOAD,
            'NOTIFY_UPDATE': self.NOTIFY_UPDATE,
            'NOTIFY_LOGIN': self.NOTIFY_LOGIN,
            'NOTIFY_POSTPROCESS': self.NOTIFY_POSTPROCESS
        }

    def notify_snatch(self, ep_name):
        raise NotImplementedError

    def notify_download(self, ep_name):
        raise NotImplementedError

    def notify_subtitle_download(self, ep_name, lang):
        raise NotImplementedError

    def notify_update(self, new_version="??"):
        raise NotImplementedError

    def notify_login(self, ip_address):
        raise NotImplementedError

    def notify_postprocess(self, ep_name):
        raise NotImplementedError

    def test_notify(self):
        raise NotImplementedError
