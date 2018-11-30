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


class Peer:
    """Represents an individual peer within a L{Torrent} instance."""

    def __init__(self, _rt_obj, info_hash, **kwargs):
        self._rt_obj = _rt_obj
        self.info_hash = info_hash  # : info hash for the torrent the peer is associated with
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))

        self.rpc_id = '{0}:p{1}'.format(
            self.info_hash, self.id)  # : unique id to pass to rTorrent

    def __repr__(self):
        return safe_repr('Peer(id={0})', self.id)

    def update(self):
        """Refresh peer data.

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
    Method(Peer, 'is_preferred', 'p.is_preferred',
           boolean=True,
           ),
    Method(Peer, 'get_down_rate', 'p.down_rate'),
    Method(Peer, 'is_unwanted', 'p.is_unwanted',
           boolean=True,
           ),
    Method(Peer, 'get_peer_total', 'p.peer_total'),
    Method(Peer, 'get_peer_rate', 'p.peer_rate'),
    Method(Peer, 'get_port', 'p.port'),
    Method(Peer, 'is_snubbed', 'p.is_snubbed',
           boolean=True,
           ),
    Method(Peer, 'get_id_html', 'p.id_html'),
    Method(Peer, 'get_up_rate', 'p.up_rate'),
    Method(Peer, 'is_banned', 'p.banned',
           boolean=True,
           ),
    Method(Peer, 'get_completed_percent', 'p.completed_percent'),
    Method(Peer, 'get_id', 'p.id'),
    Method(Peer, 'is_obfuscated', 'p.is_obfuscated',
           boolean=True,
           ),
    Method(Peer, 'get_down_total', 'p.down_total'),
    Method(Peer, 'get_client_version', 'p.client_version'),
    Method(Peer, 'get_address', 'p.address'),
    Method(Peer, 'is_incoming', 'p.is_incoming',
           boolean=True,
           ),
    Method(Peer, 'is_encrypted', 'p.is_encrypted',
           boolean=True,
           ),
    Method(Peer, 'get_options_str', 'p.options_str'),
    Method(Peer, 'get_client_version', 'p.client_version'),
    Method(Peer, 'get_up_total', 'p.up_total'),

    # MODIFIERS
]
