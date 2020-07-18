# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
#
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
from abc import ABCMeta

# Third Party Imports
import configobj

# First Party Imports
from sickbeard import logger


class ConfigMixin(metaclass=ABCMeta):
    _options: tuple
    _config: configobj.ConfigObj
    name: str

    def config(self, key: str):
        if not self.options(key):
            raise Exception('Unsupported key attempted to be read for provider: {}, key: {}'.format(self.name, key))
        return self._config.get(key)

    def set_config(self, key: str, value) -> None:
        if not self.options(key):
            logger.debug('Unsupported key attempted to be written for provider: {}, key: {}, value: {}'.format(self.name, key, value))
            return
        self._config[key] = value

    def options(self, option):
        return option in self._options
