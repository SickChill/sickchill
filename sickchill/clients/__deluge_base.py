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
# First Party Imports
import sickbeard

# Local Folder Imports
from .generic import GenericClient


class DelugeBase(GenericClient):
    def make_options(self, result):
        options = {}

        if self.config('download_path') or self.config('incomplete_path') :
            options.update({
                'download_location': self.config('incomplete_path') or self.config('download_path') ,
                'move_completed': bool(self.config('incomplete_path')),
            })

        if self.config('download_path') and self.config('incomplete_path') :
            options.update({
                'move_completed': True,
                'move_completed_path': self.config('download_path')
            })

        if self.config('add_paused'):
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
