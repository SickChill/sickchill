from collections import OrderedDict
from collections.abc import Iterable
import bencodepy


class Decoder:
    def __init__(self, data: bytes):
        self.data = data
        self.idx = 0

    def __read(self, i: int) -> bytes:
        """Returns a set number (i) of bytes from self.data."""
        b = self.data[self.idx: self.idx + i]
        self.idx += i
        if len(b) != i:
            raise bencodepy.DecodingError(
                "Incorrect byte length returned between indexes of {0} and {1}. Possible unexpected End of File."
                    .format(str(self.idx), str(self.idx - i)))
        return b

    def __read_to(self, terminator: bytes) -> bytes:
        """Returns bytes from self.data starting at index (self.idx) until terminator character."""
        try:
            # noinspection PyTypeChecker
            i = self.data.index(terminator, self.idx)
            b = self.data[self.idx:i]
            self.idx = i + 1
            return b
        except ValueError:
            raise bencodepy.DecodingError(
                'Unable to locate terminator character "{0}" after index {1}.'.format(str(terminator), str(self.idx)))

    def __parse(self) -> object:
        """Selects the appropriate method to decode next bencode element and returns the result."""
        char = self.data[self.idx: self.idx + 1]
        if char in [b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b'0']:
            str_len = int(self.__read_to(b':'))
            return self.__read(str_len)
        elif char == b'i':
            self.idx += 1
            return int(self.__read_to(b'e'))
        elif char == b'd':
            return self.__parse_dict()
        elif char == b'l':
            return self.__parse_list()
        elif char == b'':
            raise bencodepy.DecodingError('Unexpected End of File at index position of {0}.'.format(str(self.idx)))
        else:
            raise bencodepy.DecodingError(
                'Invalid token character ({0}) at position {1}.'.format(str(char), str(self.idx)))

    def decode(self) -> Iterable:
        """Start of decode process. Returns final results."""
        if self.data[0:1] not in (b'd', b'l'):
            return self.__wrap_with_tuple()
        return self.__parse()

    def __wrap_with_tuple(self) -> tuple:
        """Returns a tuple of all nested bencode elements."""
        l = list()
        length = len(self.data)
        while self.idx < length:
            l.append(self.__parse())
        return tuple(l)

    def __parse_dict(self) -> OrderedDict:
        """Returns an Ordered Dictionary of nested bencode elements."""
        self.idx += 1
        d = OrderedDict()
        key_name = None
        while self.data[self.idx: self.idx + 1] != b'e':
            if key_name is None:
                key_name = self.__parse()
            else:
                d[key_name] = self.__parse()
                key_name = None
        self.idx += 1
        return d

    def __parse_list(self) -> list:
        """Returns an list of nested bencode elements."""
        self.idx += 1
        l = []
        while self.data[self.idx: self.idx + 1] != b'e':
            l.append(self.__parse())
        self.idx += 1
        return l


def decode_from_file(path: str) -> Iterable:
    """Convenience function. Reads file and calls decode()."""
    with open(path, 'rb') as f:
        b = f.read()
    return decode(b)


def decode(data: bytes) -> Iterable:
    """Convenience function. Initializes Decoder class, calls decode method, and returns the result."""
    decoder = Decoder(data)
    return decoder.decode()
