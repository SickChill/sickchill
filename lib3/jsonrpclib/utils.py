#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Utility methods, for compatibility between Python version

:author: Thomas Calmant
:copyright: Copyright 2020, Thomas Calmant
:license: Apache License 2.0
:version: 0.4.2

..

    Copyright 2020 Thomas Calmant

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import sys

# ------------------------------------------------------------------------------

# Module version
__version_info__ = (0, 4, 2)
__version__ = ".".join(str(x) for x in __version_info__)

# Documentation strings format
__docformat__ = "restructuredtext en"

# ------------------------------------------------------------------------------

if sys.version_info[0] < 3:
    # Python 2
    # pylint: disable=E1101
    import types

    try:
        STRING_TYPES = (types.StringType, types.UnicodeType)
    except NameError:
        # Python built without unicode support
        STRING_TYPES = (types.StringType,)

    NUMERIC_TYPES = (types.IntType, types.LongType, types.FloatType)

    def to_bytes(string):
        """
        Converts the given string into bytes
        """
        # pylint: disable=E0602
        if type(string) is unicode:  # noqa: F821
            return str(string)
        return string

    def from_bytes(data):
        """
        Converts the given bytes into a string
        """
        if type(data) is str:
            return data
        return str(data)


else:
    # Python 3
    # pylint: disable=E1101
    STRING_TYPES = (bytes, str)

    NUMERIC_TYPES = (int, float)

    def to_bytes(string):
        """
        Converts the given string into bytes
        """
        if type(string) is bytes:
            return string
        return bytes(string, "UTF-8")

    def from_bytes(data):
        """
        Converts the given bytes into a string
        """
        if type(data) is str:
            return data
        return str(data, "UTF-8")


# ------------------------------------------------------------------------------
# Enumerations

try:
    import enum

    def is_enum(obj):
        """
        Checks if an object is from an enumeration class

        :param obj: Object to test
        :return: True if the object is an enumeration item
        """
        return isinstance(obj, enum.Enum)


except ImportError:
    # Pre-Python 3.4
    def is_enum(obj):  # pylint: disable=unused-argument
        """
        Before Python 3.4, enumerations didn't exist.

        :param obj: Object to test
        :return: Always False
        """
        return False


# ------------------------------------------------------------------------------
# Common

DictType = dict

ListType = list
TupleType = tuple

ITERABLE_TYPES = (list, set, frozenset, tuple)

VALUE_TYPES = (bool, type(None))

PRIMITIVE_TYPES = STRING_TYPES + NUMERIC_TYPES + VALUE_TYPES
