try:
    from collections import UserList
    # noinspection PyCompatibility,PyUnresolvedReferences
    from collections.abc import Iterable
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from UserList import UserList
    from collections import Iterable

from attrdict import AttrDict
from pkg_resources import parse_version

import six


def list2string(input_list=None, delimiter="|"):
    """
    Convert entries in a list to a concatenated string

    :param input_list: list to convert
    :param delimiter: delimiter for concatenation
    :return: if input is a list, concatenated string...else whatever the input was
    """
    if not isinstance(input_list, six.string_types) and isinstance(input_list, Iterable):
        return delimiter.join(map(str, input_list))
    return input_list


def suppress_context(exc):
    """
    This is used to mask an exception with another one.

    For instance, below, the divide by zero error is masked by the CustomException.
        try:
            1/0
        except ZeroDivisionError:
            raise suppress_context(CustomException())

    Note: In python 3, the last line would simply be raise CustomException() from None
    :param exc: new Exception that will be raised
    :return: Exception to be raised
    """
    exc.__cause__ = None
    return exc


def is_version_less_than(ver1, ver2, lteq=True):
    """
    Determine if ver1 is equal to or later than ver2.

    :param ver1: version to check
    :param ver2: current version of application
    :param lteq: True for Less Than or Equals; False for just Less Than
    :return: True or False
    """
    if lteq:
        return parse_version(ver1) <= parse_version(ver2)
    return parse_version(ver1) < parse_version(ver2)


class APINames(object):
    """
    API names for API endpoints

    e.g 'torrents' in http://localhost:8080/api/v2/torrents/addTrackers
    """
    Authorization = 'auth'
    Application = 'app'
    Log = 'log'
    Sync = 'sync'
    Transfer = 'transfer'
    Torrents = 'torrents'
    RSS = 'rss'
    Search = 'search'


class ClientCache(object):

    """Caches the client. Subclass this for any object that needs access to the Client."""

    def __init__(self, *args, **kwargs):
        self._client = kwargs.pop('client')
        super(ClientCache, self).__init__(*args, **kwargs)


class Dictionary(ClientCache, AttrDict):

    """Base definition of dictionary-like objects returned from qBittorrent."""

    def __init__(self, data=None, client=None):

        # iterate through a dictionary converting any nested dictionaries to AttrDicts
        def convert_dict_values_to_attrdicts(d):
            converted_dict = AttrDict()
            if isinstance(d, dict):
                for key, value in d.items():
                    # if the value is a dictionary, convert it to a AttrDict
                    if isinstance(value, dict):
                        # recursively send each value to convert its dictionary children
                        converted_dict[key] = convert_dict_values_to_attrdicts(AttrDict(value))
                    else:
                        converted_dict[key] = value
                return converted_dict

        data = convert_dict_values_to_attrdicts(data)
        super(Dictionary, self).__init__(data or dict(), client=client)
        # allows updating properties that aren't necessarily a part of the AttrDict
        self._setattr('_allow_invalid_attributes', True)


class List(ClientCache, UserList):

    """Base definition for list-like objects returned from qBittorrent."""

    def __init__(self, list_entries=None, entry_class=None, client=None):

        entries = []
        for entry in list_entries:
            if isinstance(entry, dict):
                entries.append(entry_class(data=entry, client=client))
            else:
                entries.append(entry)
        super(List, self).__init__(entries, client=client)


class ListEntry(Dictionary):

    """Base definition for objects within a list returned from qBittorrent."""
