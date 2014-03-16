"""
structures.py
~~~~~~~~~~~~~

Defines structures used by the httpcache module.
"""

class RecentOrderedDict(dict):
    """
    A custom variant of the dictionary that ensures that the object most
    recently inserted _or_ retrieved from the dictionary is enumerated first.
    """
    def __init__(self):
        self._data = {}
        self._order = []

    def __setitem__(self, key, value):
        if key in self._data:
            self._order.remove(key)

        self._order.append(key)
        self._data[key] = value

    def __getitem__(self, key):
        value = self._data[key]
        self._order.remove(key)
        self._order.append(key)
        return value

    def __delitem__(self, key):
        del self._data[key]
        self._order.remove(key)

    def __iter__(self):
        return self._order

    def __len__(self):
        return len(self._order)

    def __contains__(self, value):
        return self._data.__contains__(value)

    def items(self):
        return [(key, self._data[key]) for key in self._order]

    def keys(self):
        return self._order

    def values(self):
        return [self._data[key] for key in self._order]

    def clear(self):
        self._data = {}
        self._order = []

    def copy(self):
        c = RecentOrderedDict()
        c._data = self._data.copy()
        c._order = self._order[:]
