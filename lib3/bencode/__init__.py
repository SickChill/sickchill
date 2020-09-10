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

from bencode.BTL import BTFailure
from bencode.exceptions import BencodeDecodeError

from bencodepy import Bencached, Bencode

__all__ = (
    'BTFailure',
    'Bencached',
    'BencodeDecodeError',
    'bencode',
    'bdecode',
    'bread',
    'bwrite',
    'encode',
    'decode'
)


DEFAULT = Bencode(
    encoding='utf-8',
    encoding_fallback='value',
    dict_ordered=True,
    dict_ordered_sort=True
)

bdecode = DEFAULT.decode
bencode = DEFAULT.encode
bread = DEFAULT.read
bwrite = DEFAULT.write

decode = bdecode
encode = bencode
