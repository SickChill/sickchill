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

import rtorrent.rpc

Method = rtorrent.rpc.Method


class Group:
    __name__ = 'Group'

    def __init__(self, _rt_obj, name):
        self._rt_obj = _rt_obj
        self.name = name

        self.methods = [
            # RETRIEVERS
            Method(Group, 'get_max', 'group.' + self.name + '.ratio.max', varname='max'),
            Method(Group, 'get_min', 'group.' + self.name + '.ratio.min', varname='min'),
            Method(Group, 'get_upload', 'group.' + self.name + '.ratio.upload', varname='upload'),

            # MODIFIERS
            Method(Group, 'set_max', 'group.' + self.name + '.ratio.max.set', varname='max'),
            Method(Group, 'set_min', 'group.' + self.name + '.ratio.min.set', varname='min'),
            Method(Group, 'set_upload', 'group.' + self.name + '.ratio.upload.set', varname='upload')
        ]

        rtorrent.rpc._build_rpc_methods(self, self.methods)

        # Setup multicall_add method
        caller = lambda multicall, method, *args: \
            multicall.add(method, *args)
        setattr(self, 'multicall_add', caller)

    def _get_prefix(self):
        return 'group.' + self.name + '.ratio.'

    def update(self):
        multicall = rtorrent.rpc.Multicall(self)

        retriever_methods = [m for m in self.methods
                             if m.is_retriever() and m.is_available(self._rt_obj)]

        for method in retriever_methods:
            multicall.add(method)

        multicall.call()

    def enable(self):
        p = self._rt_obj._get_conn()
        return getattr(p, self._get_prefix() + 'enable')()

    def disable(self):
        p = self._rt_obj._get_conn()
        return getattr(p, self._get_prefix() + 'disable')()

    def set_command(self, *methods):
        methods = [m + '=' for m in methods]

        m = rtorrent.rpc.Multicall(self)
        self.multicall_add(
            m, 'method.set', '',
            self._get_prefix() + 'command',
            *methods
        )

        return(m.call()[-1])
