# coding=utf-8
# Author: Dustyn Gibson (miigotu) <miigotu@gmail.com>
# URL: https://sick-rage.github.io
# Git: https://github.com/Sick-Rage/Sick-Rage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty    of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.
# pylint:disable=too-many-lines

from __future__ import print_function, unicode_literals


def hide(value):
    return 'hidden_value' if value else ''


def unhide(old, new):
    return (new, old)[new == 'hidden_value'] or None
