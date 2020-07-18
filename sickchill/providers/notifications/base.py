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
# Stdlib Imports
from abc import ABCMeta, abstractmethod

# First Party Imports
import sickbeard
import sickchill.config.mixin


class AbstractNotifier(sickchill.config.mixin.ConfigMixin, metaclass=ABCMeta):
    def __init__(self, name: str, extra_options: tuple = tuple()):
        self.name = name
        self._options = ('enabled', 'snatch', 'download', 'subtitle', 'update', 'login', 'process')
        if extra_options:
            self._options += extra_options

        sickchill.config.assure_config(['providers', 'notifications', self.name])
        self._config = sickbeard.CFG2['providers']['notifications'][self.name]

    @abstractmethod
    def notify_snatch(self, name: str):
        raise NotImplementedError

    @abstractmethod
    def notify_download(self, name: str):
        raise NotImplementedError

    @abstractmethod
    def notify_subtitle_download(self, name: str, lang: str):
        raise NotImplementedError

    @abstractmethod
    def notify_git_update(self, new_version: str):
        raise NotImplementedError

    @abstractmethod
    def notify_login(self, ipaddress: str):
        raise NotImplementedError

    @abstractmethod
    def notify_postprocess(self, name: str):
        raise NotImplementedError

    @staticmethod
    def test_notify(username):
        raise NotImplementedError
