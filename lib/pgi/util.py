# Copyright 2012,2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import keyword
import re
from operator import itemgetter
from ctypes import cdll
from ctypes.util import find_library

from . import const
from .clib.gir import GITypeTag, GIInfoType
from ._compat import xrange, text_type


class PyGIWarning(Warning):
    pass


class PyGIDeprecationWarning(DeprecationWarning):
    pass


def decode_return(codec="ascii"):
    """Decodes the return value of it isn't None"""

    def outer(f):
        def wrap(*args, **kwargs):
            res = f(*args, **kwargs)
            if res is not None:
                return res.decode(codec)
            return res
        return wrap
    return outer


def decode_return_list(codec="ascii"):
    """Decodes a list return value"""

    def outer(f):
        def wrap(*args, **kwargs):
            return [res.decode(codec) for res in f(*args, **kwargs)]
        return wrap
    return outer


def load_ctypes_library(name):
    """Takes a library name and calls find_library in case loading fails,
    since some girs don't include the real .so name.

    Raises OSError like LoadLibrary if loading fails.

    e.g. javascriptcoregtk-3.0 should be libjavascriptcoregtk-3.0.so on unix
    """

    try:
        return cdll.LoadLibrary(name)
    except OSError:
        name = find_library(name)
        if name is None:
            raise
        return cdll.LoadLibrary(name)


class InfoIterWrapper(object):
    """Allow fast name lookup for gi structs.

    Most GIBaseInfo struct define an interface to iterate sub structs.
    Those are usually sorted by name, so we can do a binary search.
    Since they aren't guaranteed to be sorted we have to look through all
    of them in case of a miss.

    Slow/fast paths are separated since we need to check all fast paths
    of multiple sources before falling back to the slow ones.
    """

    def __init__(self, source):
        super(InfoIterWrapper, self).__init__()
        self._source = source
        self.__infos = {}
        self.__names = {}
        self.__count = -1

    def _get_count(self, source):
        raise NotImplementedError

    def _get_info(self, source, index):
        raise NotImplementedError

    def _get_name(self, info):
        raise NotImplementedError

    def _get_by_name(self, source, name):
        raise NotImplementedError

    def __get_name_cached(self, index):
        info = self.__get_info_cached(index)
        name = self._get_name(info)
        self.__names[name] = info
        return name

    def __get_info_cached(self, index):
        if index not in self.__infos:
            self.__infos[index] = self._get_info(self._source, index)
        return self.__infos[index]

    def __get_count_cached(self):
        if self.__count == -1:
            self.__count = self._get_count(self._source)
        return self.__count

    def lookup_name_fast(self, name):
        """Might return a struct"""

        if name in self.__names:
            return self.__names[name]

        count = self.__get_count_cached()
        lo = 0
        hi = count
        while lo < hi:
            mid = (lo + hi) // 2
            if self.__get_name_cached(mid) < name:
                lo = mid + 1
            else:
                hi = mid

        if lo != count and self.__get_name_cached(lo) == name:
            return self.__get_info_cached(lo)

    def lookup_name_slow(self, name):
        """Returns a struct if one exists"""

        for index in xrange(self.__get_count_cached()):
            if self.__get_name_cached(index) == name:
                return self.__get_info_cached(index)

    def lookup_name(self, name):
        """Returns a struct if one exists"""

        try:
            info = self._get_by_name(self._source, name)
        except NotImplementedError:
            pass
        else:
            if info:
                return info
            return

        info = self.lookup_name_fast(name)
        if info:
            return info
        return self.lookup_name_slow(name)

    def iternames(self):
        """Iterate over all struct names in no defined order"""

        for index in xrange(self.__get_count_cached()):
            yield self.__get_name_cached(index)

    def clear(self):
        """Unref all structs and clear cache"""

        self.__infos.clear()
        self.__names.clear()


def set_gvalue_from_py(ptr, is_interface, tag, value):
    if is_interface:
        if tag == GIInfoType.ENUM:
            ptr.set_enum(int(value))
        else:
            raise NotImplementedError
    else:
        if tag == GITypeTag.BOOLEAN:
            ptr.set_boolean(value)
        elif tag == GITypeTag.INT32:
            ptr.set_int(value)
        elif tag == GITypeTag.UINT32:
            ptr.set_uint(value)
        elif tag == GITypeTag.DOUBLE:
            ptr.set_double(value)
        elif tag == GITypeTag.FLOAT:
            ptr.set_float(value)
        elif tag == GITypeTag.UTF8:
            if isinstance(value, text_type):
                value = value.encode("utf-8")
            ptr.set_string(value)
        else:
            return False

    return True


def import_attribute(namespace, name):
    try:
        mod = __import__(const.PREFIX[-1] + "." + namespace, fromlist=[name])
    except RuntimeError as e:
        # this happens on Windows, no idea why
        raise ImportError(e)

    try:
        return getattr(mod, name)
    except AttributeError as e:
        # callback types
        raise ImportError(e)


def import_module(namespace):
    mod = __import__(const.PREFIX[-1], fromlist=[namespace])
    return getattr(mod, namespace)


def encode(string):
    if not isinstance(string, bytes):
        return string.encode("utf-8")
    return string


KWD_RE = re.compile("^(%s)$" % "|".join(keyword.kwlist + ["print", "exec"]))


def escape_identifier(text, reg=KWD_RE):
    """Escape partial C identifiers so they can be used as
    attributes/arguments"""

    # see http://docs.python.org/reference/lexical_analysis.html#identifiers
    if not text:
        return "_"
    if text[0].isdigit():
        text = "_" + text
    return reg.sub(r"\1_", text)


def unescape_identifier(text):
    # XXX: get rid of this

    if len(text) >= 2:
        if text[0] == "_" and text[1].isdigit():
            text = text[1:]
    if text.endswith("_"):
        return text[:-1]
    return text


def escape_parameter(text):
    """Escape a GObejct parameter name so it can be used as python
    attribute/argument
    """

    return escape_identifier(text.replace("-", "_"))


def unescape_parameter(text):
    # XXX: get rid of this

    return unescape_identifier(text).replace("_", "-")


def cache_return(func):
    """Cache the return value of a function without arguments"""

    _cache = []

    def wrap():
        if not _cache:
            _cache.append(func())
        return _cache[0]
    return wrap


class cached_property(object):
    """A read-only @property that is only evaluated once."""

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result

    def __set__(self, instance, value):
        raise AttributeError


class cached_property_writable(object):
    """A @property that is only evaluated once."""

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result


class ResultTuple(tuple):

    __slots__ = ()
    _fformat = ()

    def __repr__(self):
        return self._fformat % self

    def __reduce__(self):
        return (tuple, (tuple(self),))

    @classmethod
    def _new_type(cls, args):
        """Creates a new class similar to namedtuple.

        Pass a list of field names or None for no field name.

        >>> x = ResultTuple._new_type([None, "bar"])
        >>> x((1, 3))
        ResultTuple(1, bar=3)
        """

        fformat = ["%r" if f is None else "%s=%%r" % f for f in args]
        fformat = "(%s)" % ", ".join(fformat)

        class _ResultTuple(cls):
            __slots__ = ()
            _fformat = fformat
            if args:
                for i, a in enumerate(args):
                    if a is not None:
                        vars()[a] = property(itemgetter(i))
                del i, a

        return _ResultTuple
