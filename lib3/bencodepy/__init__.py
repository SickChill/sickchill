# The contents of this file are subject to the BitTorrent Open Source License
# Version 1.1 (the License).  You may not copy or use this file, in either
# source code or executable form, except in compliance with the License.  You
# may obtain a copy of the License at http://www.bittorrent.com/license/.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.

# Written by Petru Paler

"""bencode.py - bencode encoder + decoder."""

from bencodepy.common import Bencached
from bencodepy.decoder import BencodeDecoder
from bencodepy.encoder import BencodeEncoder
from bencodepy.exceptions import BencodeDecodeError

try:
    from typing import Dict, List, Tuple, Deque, Union, TextIO, BinaryIO, Any
except ImportError:
    Dict = List = Tuple = Deque = Union = TextIO = BinaryIO = Any = None

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = None

try:
    import pathlib
except ImportError:
    pathlib = None

__all__ = (
    'Bencached',
    'Bencode',
    'BencodeDecoder',
    'BencodeDecodeError',
    'BencodeEncoder',
    'bencode',
    'bdecode',
    'bread',
    'bwrite',
    'encode',
    'decode'
)


class Bencode(object):
    def __init__(self, encoding=None, encoding_fallback=None, dict_ordered=False, dict_ordered_sort=False):
        self.decoder = BencodeDecoder(
            encoding=encoding,
            encoding_fallback=encoding_fallback,
            dict_ordered=dict_ordered,
            dict_ordered_sort=dict_ordered_sort
        )

        self.encoder = BencodeEncoder()

    def decode(self, value):
        # type: (bytes) -> Union[Tuple, List, OrderedDict, bool, int, str, bytes]
        """
        Decode bencode formatted byte string ``value``.

        :param value: Bencode formatted string
        :type value: bytes

        :return: Decoded value
        :rtype: object
        """
        return self.decoder.decode(value)

    def encode(self, value):
        # type: (Union[Tuple, List, OrderedDict, Dict, bool, int, str, bytes]) -> bytes
        """
        Encode ``value`` into the bencode format.

        :param value: Value
        :type value: object

        :return: Bencode formatted string
        :rtype: str
        """
        return self.encoder.encode(value)

    def read(self,
             fd  # type: Union[bytes, str, pathlib.Path, pathlib.PurePath, TextIO, BinaryIO]
             ):
        # type: (...) -> Union[Tuple, List, OrderedDict, bool, int, str, bytes]
        """Return bdecoded data from filename, file, or file-like object.

        if fd is a bytes/string or pathlib.Path-like object, it is opened and
        read, otherwise .read() is used. if read() not available, exception
        raised.
        """
        if isinstance(fd, (bytes, str)):
            with open(fd, 'rb') as fd:
                return self.decode(fd.read())
        elif pathlib is not None and isinstance(fd, (pathlib.Path, pathlib.PurePath)):
            with open(str(fd), 'rb') as fd:
                return self.decode(fd.read())
        else:
            return self.decode(fd.read())

    def write(self,
              data,  # type: Union[Tuple, List, OrderedDict, Dict, bool, int, str, bytes]
              fd     # type: Union[bytes, str, pathlib.Path, pathlib.PurePath, TextIO, BinaryIO]
              ):
        # type: (...) -> None
        """Write data in bencoded form to filename, file, or file-like object.

        if fd is bytes/string or pathlib.Path-like object, it is opened and
        written to, otherwise .write() is used. if write() is not available,
        exception raised.
        """
        if isinstance(fd, (bytes, str)):
            with open(fd, 'wb') as fd:
                fd.write(self.encode(data))
        elif pathlib is not None and isinstance(fd, (pathlib.Path, pathlib.PurePath)):
            with open(str(fd), 'wb') as fd:
                fd.write(self.encode(data))
        else:
            fd.write(self.encode(data))


DEFAULT = Bencode()


def bencode(value):
    # type: (Union[Tuple, List, OrderedDict, Dict, bool, int, str, bytes]) -> bytes
    """
    Encode ``value`` into the bencode format.

    :param value: Value
    :type value: object

    :return: Bencode formatted string
    :rtype: str
    """
    return DEFAULT.encode(value)


def bdecode(value):
    # type: (bytes) -> Union[Tuple, List, OrderedDict, bool, int, str, bytes]
    """
    Decode bencode formatted byte string ``value``.

    :param value: Bencode formatted string
    :type value: bytes

    :return: Decoded value
    :rtype: object
    """
    return DEFAULT.decode(value)


def bread(fd  # type: Union[bytes, str, pathlib.Path, pathlib.PurePath, TextIO, BinaryIO]
          ):
    # type: (...) -> Union[Tuple, List, OrderedDict, bool, int, str, bytes]
    """Return bdecoded data from filename, file, or file-like object.

    if fd is a bytes/string or pathlib.Path-like object, it is opened and
    read, otherwise .read() is used. if read() not available, exception
    raised.
    """
    return DEFAULT.read(fd)


def bwrite(data,  # type: Union[Tuple, List, OrderedDict, Dict, bool, int, str, bytes]
           fd     # type: Union[bytes, str, pathlib.Path, pathlib.PurePath, TextIO, BinaryIO]
           ):
    # type: (...) -> None
    """Write data in bencoded form to filename, file, or file-like object.

    if fd is bytes/string or pathlib.Path-like object, it is opened and
    written to, otherwise .write() is used. if write() is not available,
    exception raised.
    """
    return DEFAULT.write(data, fd)


# Compatibility Proxies
encode = bencode
decode = bdecode
