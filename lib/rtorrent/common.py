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

from rtorrent.compat import is_py3


def bool_to_int(value):
    """Translate Python booleans to RPC-safe integers."""
    if value is True:
        return("1")
    elif value is False:
        return("0")
    else:
        return(value)


def cmd_exists(cmds_list, cmd):
    """Check if given command is in list of available commands.

    @param cmds_list: see L{RTorrent._rpc_methods}
    @type cmds_list: list

    @param cmd: name of command to be checked
    @type cmd: str

    @return: bool
    """
    return(cmd in cmds_list)


def find_torrent(info_hash, torrent_list):
    """Find torrent file in given list of Torrent classes.

    @param info_hash: info hash of torrent
    @type info_hash: str

    @param torrent_list: list of L{Torrent} instances (see L{RTorrent.get_torrents})
    @type torrent_list: list

    @return: L{Torrent} instance, or -1 if not found
    """
    for t in torrent_list:
        if t.info_hash == info_hash:
            return t

    return None


def is_valid_port(port):
    """Check if given port is valid."""
    return(0 <= int(port) <= 65535)


def convert_version_tuple_to_str(t):
    return(".".join([str(n) for n in t]))


def safe_repr(fmt, *args, **kwargs):
    """Formatter that handles unicode arguments."""
    if not is_py3():
        # unicode fmt can take str args, str fmt cannot take unicode args
        fmt = fmt.decode("utf-8")
        out = fmt.format(*args, **kwargs)
        return out.encode("utf-8")
    else:
        return fmt.format(*args, **kwargs)
