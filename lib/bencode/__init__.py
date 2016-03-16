# author: plasmashadow

import six, json
import re
from functools import partial

# http://www.bittorrent.org/beps/bep_0003.html
# given specification

__DATAPATTERN = "([idel])|(\d+):|(-?\d+)"

if six.PY3:
    basestring = str
    unicode = str
    long = int


class BencodeException(Exception):
    """Base class for all bencode Exceptions"""

    def __init__(self, message, data):
        self.message = message
        self.data = data

    def __repr__(self):
        return "<BencodeException mode = %s>[%s]=>[%s]" % (self.mode, self.message, self.data)


class BencodeEncodeError(BencodeException):
    """
    Bencode Encoding Error while converting
    standard objects to bencoded Strings
    """
    mode = "Encode"


class BencodeDecodeError(BencodeException):
    """
    Bencode Decoding Error while converting
    Bencoded Strings to python Objects.
    """

    mode = "Decode"


def _encode_int(data):
    """
       Encodes the int, long in to bencoded strs
    :param data:
    :return String: becoded string
    """
    if isinstance(data, (int, long)):
        return "%s%s%s" % ("i", str(data), "e")
    else:
        raise BencodeEncodeError("Invalid Integer", data)


def _encode_string(data):
    """
      Encodes the str, basestring into becoded strs
    :param data:
    :return: String: bencoded Strings
    """
    if isinstance(data, (str, basestring, unicode,)):
        return "%s:%s" % (str(len(data)), data)
    else:
        raise BencodeEncodeError("Invalid String", data)


def _recursive_baselist_encode(data):
    """
      Encodes the sequence of str, int bencoded strs
    :param data:
    :return:
    """
    strs = ""
    for element in data:
        if isinstance(element, (str, basestring, unicode)):
            strs += _encode_string(element)
        elif isinstance(element, (int, long,)):
            strs += _encode_int(element)
        elif isinstance(element, (list, set, tuple)):
            strs += _encode_list(element)
        elif isinstance(element, (dict, )):
            strs += _encode_dict(element)
    return strs


def _encode_list(lst):
    """
     Encodes the list, set, tuple into bencoded strs
    :param list:
    :return: String: bencoded Strings
    """
    if isinstance(lst, (list, set, tuple,)):
        lst = list(lst)
        return "%s%s%s" % ("l", _recursive_baselist_encode(lst), "e")
    else:
        raise BencodeEncodeError("Invalid Collection ", lst)


def _encode_dict(dct):
    """
     Encodes the key, value pair to becoded strs
    :param dct:
    :return: String: bencoded strings
    """
    strs = ""
    if isinstance(dct, (dict,)):
        valrs = ""
        for key, value in six.iteritems(dct):
            if isinstance(value, (list, set, tuple)):
                value = _encode_list(value)
            elif isinstance(value, (str,)):
                value = _encode_string(value)
            elif isinstance(value, (int, long)):
                value = _encode_int(value)
            elif isinstance(value, dict):
                value = _encode_dict(value)
            key = _encode_string(key)
            valrs += "%s%s" % (key, value)
        strs = "%s%s%s" % ("d", valrs, "e")
    else:
        raise BencodeEncodeError("Invalid Dictionary", dct)
    return strs


# decoding part
# will try to use serial recursive tokenizer where input is divided
# into list of meaning full parts. and then parsed.

def _tokenizer(text_to_match):
    """
      Tokenises the bencodes string into a python list of tokens
      and types
      i for integer
      s for string
      d for dict
      l for list
    :param text_to_match:
    """

    match = re.compile(__DATAPATTERN).match  # match(string, pos=0, endpos=-1)
    token_length = 0
    while token_length < len(text_to_match):
        m = match(text_to_match, token_length)
        s = m.group(m.lastindex)  # http://stackoverflow.com/questions/22489243/re-in-python-lastindex-attribute
        token_length = m.end()

        if m.lastindex == 2:  # then it is a bencoded string
            yield "s"
            if int(s) == 0:
                yield ""
            else:
                yield text_to_match[token_length: token_length + int(s)]
                token_length += int(s)
        else:
            yield s


def _decode_item(next, token):
    """
      parses the decoded token
    :param next: iterator
    :param token: value of iterator
    """
    if token == "i":
        data = int(next())
        if next() != "e":  # then invalid integer
            raise BencodeDecodeError("Invalid parsable Integer", token)
    elif token == "s":  # then it is a string
        data = next()
    elif token == "l" or token == "d":
        data = []
        tok = next()
        while tok != "e":
            data.append(_decode_item(next, tok))
            tok = next()
        if token == "d":
            # since we get key value pairs like ["map", "hello", "we", "play",]
            # set map = 0 = key, hello = 1 = value
            # set we  = 2 = key, play  = 3= value
            # the parser has to move from 2 positions from the current position
            # in the token list
            data = dict(zip(data[0::2], data[1::2]))
    else:
        raise BencodeDecodeError("Invalid Structure Object", token)

    return data


def _decode(text):
    """Decodes the becode String"""
    try:
        src = _tokenizer(text)
        pf = partial(six.next, src)
        data = _decode_item(pf, six.next(src))
        for token in src:  # look for more tokens
            raise BencodeDecodeError("Trailing junk tokens", token)
    except BencodeException:
        raise BencodeDecodeError("Ilegal syntax", data)
    return data


class Bencoder(object):
    """
      A class wrapper around bencode encoding.
    """

    @classmethod
    def encode(cls, obj):
        """encodes each python std object to bencoded strs"""
        if isinstance(obj, (str, basestring, unicode)):
            return _encode_string(obj)
        elif isinstance(obj, (int, long,)):
            return _encode_int(obj)
        elif isinstance(obj, (list, tuple, set)):
            return _encode_list(obj)
        elif isinstance(obj, (dict,)):
            return _encode_dict(obj)

        else:
            raise BencodeEncodeError("Object Doesn't match any base types", obj)

    @classmethod
    def decode(cls, becode_string):
        """decodes the becoded strings to python objects"""
        return _decode(becode_string)
