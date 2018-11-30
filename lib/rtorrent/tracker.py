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


class Tracker:
    """Represents an individual tracker within a L{Torrent} instance."""

    def __init__(self, _rt_obj, info_hash, **kwargs):
        self._rt_obj = _rt_obj
        self.info_hash = info_hash  # : info hash for the torrent using this tracker
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))

        # for clarity's sake...
        self.index = self.group  # : position of tracker within the torrent's tracker list
        self.rpc_id = '{0}:t{1}'.format(
            self.info_hash, self.index)  # : unique id to pass to rTorrent

    def __repr__(self):
        return safe_repr('Tracker(index={0}, url="{1}")',
                         self.index, self.url)

    def enable(self):
        """Alias for set_enabled('yes')."""
        self.set_enabled('yes')

    def disable(self):
        """Alias for set_enabled('no')."""
        self.set_enabled('no')

    def update(self):
        """Refresh tracker data.

        @note: All fields are stored as attributes to self.

        @return: None
        """
        multicall = rtorrent.rpc.Multicall(self)
        retriever_methods = [m for m in methods
                             if m.is_retriever() and m.is_available(self._rt_obj)]
        for method in retriever_methods:
            multicall.add(method, self.rpc_id)

        multicall.call()


methods = [
    # RETRIEVERS
    Method(Tracker, 'is_enabled', 't.is_enabled', boolean=True),
    Method(Tracker, 'get_id', 't.id'),
    Method(Tracker, 'get_scrape_incomplete', 't.scrape_incomplete'),
    Method(Tracker, 'is_open', 't.is_open', boolean=True),
    Method(Tracker, 'get_min_interval', 't.min_interval'),
    Method(Tracker, 'get_scrape_downloaded', 't.scrape_downloaded'),
    Method(Tracker, 'get_group', 't.group'),
    Method(Tracker, 'get_scrape_time_last', 't.scrape_time_last'),
    Method(Tracker, 'get_type', 't.type'),
    Method(Tracker, 'get_normal_interval', 't.normal_interval'),
    Method(Tracker, 'get_url', 't.url'),
    Method(Tracker, 'get_scrape_complete', 't.scrape_complete',
           min_version=(0, 8, 9),
           ),
    Method(Tracker, 'get_activity_time_last', 't.activity_time_last',
           min_version=(0, 8, 9),
           ),
    Method(Tracker, 'get_activity_time_next', 't.activity_time_next',
           min_version=(0, 8, 9),
           ),
    Method(Tracker, 'get_failed_time_last', 't.failed_time_last',
           min_version=(0, 8, 9),
           ),
    Method(Tracker, 'get_failed_time_next', 't.failed_time_next',
           min_version=(0, 8, 9),
           ),
    Method(Tracker, 'get_success_time_last', 't.success_time_last',
           min_version=(0, 8, 9),
           ),
    Method(Tracker, 'get_success_time_next', 't.success_time_next',
           min_version=(0, 8, 9),
           ),
    Method(Tracker, 'can_scrape', 't.can_scrape',
           min_version=(0, 9, 1),
           boolean=True
           ),
    Method(Tracker, 'get_failed_counter', 't.failed_counter',
           min_version=(0, 8, 9)
           ),
    Method(Tracker, 'get_scrape_counter', 't.scrape_counter',
           min_version=(0, 8, 9)
           ),
    Method(Tracker, 'get_success_counter', 't.success_counter',
           min_version=(0, 8, 9)
           ),
    Method(Tracker, 'is_usable', 't.is_usable',
           min_version=(0, 9, 1),
           boolean=True
           ),
    Method(Tracker, 'is_busy', 't.is_busy',
           min_version=(0, 9, 1),
           boolean=True
           ),
    Method(Tracker, 'is_extra_tracker', 't.is_extra_tracker',
           min_version=(0, 9, 1),
           boolean=True,
           ),
    Method(Tracker, 'get_latest_sum_peers', 't.latest_sum_peers',
           min_version=(0, 9, 0)
           ),
    Method(Tracker, 'get_latest_new_peers', 't.latest_new_peers',
           min_version=(0, 9, 0)
           ),

    # MODIFIERS
    Method(Tracker, 'set_enabled', 't.is_enabled.set'),
]
