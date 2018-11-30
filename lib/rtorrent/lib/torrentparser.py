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

import hashlib
import os.path
import re

import rtorrent.lib.bencode as bencode
from rtorrent.compat import is_py3

if is_py3():
    from urllib.request import urlopen  # @UnresolvedImport @UnusedImport
else:
    from urllib2 import urlopen  # @UnresolvedImport @Reimport


class TorrentParser():
    def __init__(self, torrent):
        """Decode and parse given torrent.

        @param torrent: handles: urls, file paths, string of torrent data
        @type torrent: str

        @raise AssertionError: Can be raised for a couple reasons:
                               - If _get_raw_torrent() couldn't figure out
                               what X{torrent} is
                               - if X{torrent} isn't a valid bencoded torrent file
        """
        self.torrent = torrent
        self._raw_torrent = None  # : testing yo
        self._torrent_decoded = None  # : what up
        self.file_type = None

        self._get_raw_torrent()
        assert self._raw_torrent is not None, "Couldn't get raw_torrent."
        if self._torrent_decoded is None:
            self._decode_torrent()
        assert isinstance(self._torrent_decoded, dict), "Invalid torrent file."
        self._parse_torrent()

    def _is_raw(self):
        raw = False
        if isinstance(self.torrent, (str, bytes)):
            if isinstance(self._decode_torrent(self.torrent), dict):
                raw = True
            else:
                # reset self._torrent_decoded (currently equals False)
                self._torrent_decoded = None

        return(raw)

    def _get_raw_torrent(self):
        """Get raw torrent data by determining what self.torrent is."""
        # already raw?
        if self._is_raw():
            self.file_type = "raw"
            self._raw_torrent = self.torrent
            return
        # local file?
        if os.path.isfile(self.torrent):
            self.file_type = "file"
            self._raw_torrent = open(self.torrent, "rb").read()
        # url?
        elif re.search("^(http|ftp):\/\/", self.torrent, re.I):
            self.file_type = "url"
            self._raw_torrent = urlopen(self.torrent).read()

    def _decode_torrent(self, raw_torrent=None):
        if raw_torrent is None:
            raw_torrent = self._raw_torrent
        self._torrent_decoded = bencode.decode(raw_torrent)
        return(self._torrent_decoded)

    def _calc_info_hash(self):
        self.info_hash = None
        if "info" in self._torrent_decoded.keys():
                info_encoded = bencode.encode(self._torrent_decoded["info"])

                if info_encoded:
                    self.info_hash = hashlib.sha1(info_encoded).hexdigest().upper()

        return(self.info_hash)

    def _parse_torrent(self):
        for k in self._torrent_decoded:
            key = k.replace(" ", "_").lower()
            setattr(self, key, self._torrent_decoded[k])

        self._calc_info_hash()


class NewTorrentParser(object):
    @staticmethod
    def _read_file(fp):
        return fp.read()

    @staticmethod
    def _write_file(fp):
        fp.write()
        return fp

    @staticmethod
    def _decode_torrent(data):
        return bencode.decode(data)

    def __init__(self, input):
        self.input = input
        self._raw_torrent = None
        self._decoded_torrent = None
        self._hash_outdated = False

        if isinstance(self.input, (str, bytes)):
            # path to file?
            if os.path.isfile(self.input):
                self._raw_torrent = self._read_file(open(self.input, "rb"))
            else:
                # assume input was the raw torrent data (do we really want
                # this?)
                self._raw_torrent = self.input

        # file-like object?
        elif self.input.hasattr("read"):
            self._raw_torrent = self._read_file(self.input)

        assert self._raw_torrent is not None, "Invalid input: input must be a path or a file-like object"

        self._decoded_torrent = self._decode_torrent(self._raw_torrent)

        assert isinstance(
            self._decoded_torrent, dict), "File could not be decoded"

    def _calc_info_hash(self):
        self.info_hash = None
        info_dict = self._torrent_decoded["info"]
        self.info_hash = hashlib.sha1(bencode.encode(
            info_dict)).hexdigest().upper()

        return(self.info_hash)

    def set_tracker(self, tracker):
        self._decoded_torrent["announce"] = tracker

    def get_tracker(self):
        return self._decoded_torrent.get("announce")
