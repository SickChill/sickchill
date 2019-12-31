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


from __future__ import absolute_import, print_function, unicode_literals


class Notifier(object):

    def notify_snatch(self, ep_name):
        raise NotImplementedError

    def notify_download(self, ep_name):
        raise NotImplementedError

    def notify_subtitle_download(self, ep_name, lang):
        raise NotImplementedError

    def notify_git_update(self, new_version):
        raise NotImplementedError

    def notify_login(self, ipaddress=""):
        raise NotImplementedError

    @staticmethod
    def test_notify(username):
        raise NotImplementedError
