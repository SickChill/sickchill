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
from abc import ABCMeta, abstractmethod, abstractproperty

# Third Party Imports
from validate import Validator

# First Party Imports
import sickbeard


class AbstractNotifier(metaclass=ABCMeta):
    def __init__(self, name: str, extra_options: tuple = tuple()):
        self.name = name
        self.all_supported_options = ('enabled', 'snatch', 'download', 'subtitle', 'update', 'login', 'process')
        if extra_options:
            self.all_supported_options += extra_options

    def __assure_config(self):
        if 'notifications' not in sickbeard.CFG2:
            sickbeard.CFG2['notifications'] = {}
        if self.name not in sickbeard.CFG2['notifications']:
            sickbeard.CFG2['notifications'][self.name] = {}
            sickbeard.CFG2.validate(Validator(), copy=True)

    @property
    def __config(self):
        return sickbeard.CFG2['notifications'][self.name]

    def config(self, key: str):
        self.__assure_config()
        if self.options(key):
            raise Exception('Unsupported key attempted to be read for provider: {}, key: {}'.format(self.name, key))
        return self.__config.get(key)

    def set_config(self, key: str, value):
        self.__assure_config()
        if self.options(key):
            raise Exception('Unsupported key attempted to be read for provider: {}, key: {}, value: {}'.format(self.name, key, value))
        self.__config[key] = value

    def options(self, key: str):
        return key in self.all_supported_options

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

    @abstractmethod
    def update_library(self, item, remove: bool = False):
        raise NotImplementedError

    @staticmethod
    def test_notify(username):
        raise NotImplementedError
