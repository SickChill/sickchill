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

"""bencode.py - bencode encoder."""

from bencodepy.common import Bencached
from bencodepy.compat import PY2, to_binary
from collections import deque

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


class BencodeEncoder(object):
    def __init__(self):
        # noinspection PyDictCreation
        self.encode_func = {}
        self.encode_func[Bencached] = self.encode_bencached

        if PY2:
            from types import DictType, IntType, ListType, LongType, StringType, TupleType, UnicodeType

            self.encode_func[DictType] = self.encode_dict
            self.encode_func[IntType] = self.encode_int
            self.encode_func[ListType] = self.encode_list
            self.encode_func[LongType] = self.encode_int
            self.encode_func[StringType] = self.encode_bytes
            self.encode_func[TupleType] = self.encode_list
            self.encode_func[UnicodeType] = self.encode_string

            if OrderedDict is not None:
                self.encode_func[OrderedDict] = self.encode_dict

            try:
                from types import BooleanType

                self.encode_func[BooleanType] = self.encode_bool
            except ImportError:
                pass
        else:
            self.encode_func[OrderedDict] = self.encode_dict
            self.encode_func[bool] = self.encode_bool
            self.encode_func[dict] = self.encode_dict
            self.encode_func[int] = self.encode_int
            self.encode_func[list] = self.encode_list
            self.encode_func[str] = self.encode_string
            self.encode_func[tuple] = self.encode_list
            self.encode_func[bytes] = self.encode_bytes

    def encode(self, value):
        # type: (Union[Tuple, List, OrderedDict, Dict, bool, int, str, bytes]) -> bytes
        """
        Encode ``value`` into the bencode format.

        :param value: Value
        :type value: object

        :return: Bencode formatted string
        :rtype: str
        """
        r = deque()  # makes more sense for something with lots of appends

        # Encode provided value
        self.encode_func[type(value)](value, r)

        # Join parts
        return b''.join(r)

    def encode_bencached(self, x, r):
        # type: (Bencached, Deque[bytes]) -> None
        r.append(x.bencoded)

    def encode_int(self, x, r):
        # type: (int, Deque[bytes]) -> None
        r.extend((b'i', str(x).encode('utf-8'), b'e'))

    def encode_bool(self, x, r):
        # type: (bool, Deque[bytes]) -> None
        if x:
            self.encode_int(1, r)
        else:
            self.encode_int(0, r)

    def encode_bytes(self, x, r):
        # type: (bytes, Deque[bytes]) -> None
        r.extend((str(len(x)).encode('utf-8'), b':', x))

    def encode_string(self, x, r):
        # type: (str, Deque[bytes]) -> None
        return self.encode_bytes(x.encode("UTF-8"), r)

    def encode_list(self, x, r):
        # type: (List, Deque[bytes]) -> None
        r.append(b'l')

        for i in x:
            self.encode_func[type(i)](i, r)

        r.append(b'e')

    def encode_dict(self, x, r):
        # type: (Dict, Deque[bytes]) -> None
        r.append(b'd')

        # force all keys to bytes, because str and bytes are incomparable
        ilist = [(to_binary(k), v) for k, v in x.items()]
        ilist.sort(key=lambda kv: kv[0])

        for k, v in ilist:
            self.encode_func[type(k)](k, r)
            self.encode_func[type(v)](v, r)

        r.append(b'e')
