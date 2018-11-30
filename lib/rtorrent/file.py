# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
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

# File based on work done by Medariox

# from rtorrent.rpc import Method
import rtorrent.rpc
from rtorrent.common import safe_repr

Method = rtorrent.rpc.Method


class File:
    """Represents an individual file within a L{Torrent} instance."""

    def __init__(self, _rt_obj, info_hash, index, **kwargs):
        self._rt_obj = _rt_obj
        self.info_hash = info_hash  # : info hash for the torrent the file is associated with
        self.index = index  # : The position of the file within the file list
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))

        self.rpc_id = '{0}:f{1}'.format(
            self.info_hash, self.index)  # : unique id to pass to rTorrent

    def update(self):
        """Refresh file data.

        @note: All fields are stored as attributes to self.

        @return: None
        """
        multicall = rtorrent.rpc.Multicall(self)
        retriever_methods = [m for m in methods
                             if m.is_retriever() and m.is_available(self._rt_obj)]
        for method in retriever_methods:
            multicall.add(method, self.rpc_id)

        multicall.call()

    def __repr__(self):
        return safe_repr('File(index={0} path="{1}")', self.index, self.path)


methods = [
    # RETRIEVERS
    Method(File, 'get_last_touched', 'f.last_touched'),
    Method(File, 'get_range_second', 'f.range_second'),
    Method(File, 'get_size_bytes', 'f.size_bytes'),
    Method(File, 'get_priority', 'f.priority'),
    Method(File, 'get_match_depth_next', 'f.match_depth_next'),
    Method(File, 'is_resize_queued', 'f.is_resize_queued',
           boolean=True,
           ),
    Method(File, 'get_range_first', 'f.range_first'),
    Method(File, 'get_match_depth_prev', 'f.match_depth_prev'),
    Method(File, 'get_path', 'f.path'),
    Method(File, 'get_completed_chunks', 'f.completed_chunks'),
    Method(File, 'get_path_components', 'f.path_components'),
    Method(File, 'is_created', 'f.is_created',
           boolean=True,
           ),
    Method(File, 'is_open', 'f.is_open',
           boolean=True,
           ),
    Method(File, 'get_size_chunks', 'f.size_chunks'),
    Method(File, 'get_offset', 'f.offset'),
    Method(File, 'get_frozen_path', 'f.frozen_path'),
    Method(File, 'get_path_depth', 'f.path_depth'),
    Method(File, 'is_create_queued', 'f.is_create_queued',
           boolean=True,
           ),

    # MODIFIERS
]
