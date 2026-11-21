from collections.abc import MutableMapping


class NumDict(MutableMapping):
    """
    NumDict() -> new empty dictionary

    NumDict(mapping) -> new dictionary initialized from a mapping object's
        (key, value) pairs

    NumDict(iterable) -> new dictionary initialized as if via:
        d = {}
        for k, v in iterable:
            d[k] = v

    NumDict(**kwargs) -> TypeError - key words cannot be numeric

    All keys must be numeric or None
    """

    def __init__(self, iterable=None, **kwargs):
        self.data = {}
        iterable = kwargs.pop("dict", None) if iterable is None else iterable
        if iterable is not None:
            self.update(iterable)
        if kwargs:
            self.update(kwargs)

    def __len__(self):
        return len(self.data)

    # noinspection PyCallingNonCallable
    def __getitem__(self, key):
        key = self.numeric(key)
        if key in self.data:
            return self.data[key]
        if hasattr(self.__class__, "__missing__"):
            # noinspection PyUnresolvedReferences
            return self.__class__.__missing__(self, key)
        raise KeyError(key)

    def __setitem__(self, key, item):
        try:
            key = self.numeric(key)
        except KeyError:
            raise TypeError(key)
        self.data[key] = item

    def __delitem__(self, key):
        key = self.numeric(key)
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, key):
        try:
            key = self.numeric(key)
            return key in self.data
        except KeyError:
            return False

    def __repr__(self):
        return repr(self.data)

    def has_key(self, key):
        """
        DEPRECATED: Check for existence of key

        :param key: A numeric key
        :return: True if key is found, else False
        """
        return key in self

    def copy(self):
        """
        Create a copy of a NumDict
        :return: A copy
        """
        if self.__class__ is NumDict:
            return NumDict(self.data.copy())
        import copy

        data = self.data
        try:
            self.data = {}
            c = copy.copy(self)
        finally:
            self.data = data
        c.update(self)
        return c

    @classmethod
    def fromkeys(cls, iterable, value=None):
        """
        Build a NumDict from a dictionary

        :param iterable:
        :param value:
        :return:
        """
        d = cls()
        for key in iterable:
            key = cls.numeric(key)
            d[key] = value
        return d

    @staticmethod
    def numeric(key):
        """
        Converts a key to its numeric representation

        :param key: numeric dict key
        :raise KeyError: if key can't be converted to an integer
        :return: a numeric key
        :rtype: int
        """
        if key is None:
            key = 0
        try:
            return int(key)
        except (TypeError, ValueError):
            if key is not None:
                raise KeyError(key)
