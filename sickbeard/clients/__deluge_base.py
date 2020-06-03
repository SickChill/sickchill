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

# First Party Imports
import sickbeard


class DelugeBase(object):
    @staticmethod
    def make_options(result):
        options = {}

        if sickbeard.TORRENT_PATH or sickbeard.TORRENT_PATH_INCOMPLETE:
            options.update({
                'download_location': sickbeard.TORRENT_PATH_INCOMPLETE or sickbeard.TORRENT_PATH,
                'move_completed': bool(sickbeard.TORRENT_PATH_INCOMPLETE),
            })

        if sickbeard.TORRENT_PATH and sickbeard.TORRENT_PATH_INCOMPLETE:
            options.update({
                'move_completed': True,
                'move_completed_path': sickbeard.TORRENT_PATH
            })

        if sickbeard.TORRENT_PAUSED:
            options.update({'add_paused': True})

        # TODO: Figure out a nice way to do this. Will currently only work if there is only one file in the download.
        # file_priorities (list of int): The priority for files in torrent, range is [0..7] however
        # only [0, 1, 4, 7] are normally used and correspond to [Skip, Low, Normal, High]
        priority_map = {
            -1: [1],
            0: [4],
            1: [7]
        }

        # result.priority =  -1 = low, 0 = normal, 1 = high
        options.update({'file_priorities': priority_map[result.priority]})
        # options.update({'file_priorities': priority_map[result.priority] * num_files})

        if result.ratio:
            options.update({'stop_at_ratio': True})
            options.update({'stop_ratio': float(result.ratio)})
            # options.update({'remove_at_ratio': True})
            # options.update({'remove_ratio': float(result.ratio)})

        return options
