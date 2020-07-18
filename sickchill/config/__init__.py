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
from typing import Sequence

# Third Party Imports
from validate import Validator

# First Party Imports
import sickbeard


def assure_config(keys: Sequence[str], copy: bool = True) -> None:
    if keys[0] not in sickbeard.CFG2:
        section = sickbeard.CFG2[keys[0]] = {}
        sickbeard.CFG2.validate(Validator(), copy=copy)

    if len(keys) > 1 and keys[1] not in sickbeard.CFG2[keys[0]]:
        section = sickbeard.CFG2[keys[0]][keys[1]] = {}
        sickbeard.CFG2.validate(Validator(), copy=copy)

    if len(keys) > 2 and keys[2] not in sickbeard.CFG2[keys[0]][keys[1]]:
        section = sickbeard.CFG2[keys[0]][keys[1]][keys[2]] = {}
        sickbeard.CFG2.validate(Validator(), copy=copy)

    if len(keys) > 3 and keys[3] not in sickbeard.CFG2[keys[0]][keys[1]][keys[2]]:
        section = sickbeard.CFG2[keys[0]][keys[1]][keys[2]][keys[3]] = {}
        sickbeard.CFG2.validate(Validator(), copy=copy)

    if len(keys) > 4 and keys[4] not in sickbeard.CFG2[keys[0]][keys[1]][keys[2]][keys[4]]:
        section = sickbeard.CFG2[keys[0]][keys[1]][keys[2]][keys[3]][keys[4]] = {}
        sickbeard.CFG2.validate(Validator(), copy=copy)
