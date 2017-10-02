# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


class ForeignStruct(object):
    """The foreign struct interface"""

    _FOREIGN = {}

    def from_pointer(self, pointer):
        raise NotImplementedError

    def to_pointer(self, instance):
        raise NotImplementedError

    def destroy(self, pointer):
        raise NotImplementedError

    def get_type(self):
        raise NotImplementedError

    @classmethod
    def register(cls, namespace, name):
        """Class decorator"""

        def func(kind):
            cls._FOREIGN[(namespace, name)] = kind()
            return kind
        return func

    @classmethod
    def get(cls, namespace, name):
        """Raises KeyError"""

        return cls._FOREIGN[(namespace, name)]


class ForeignError(Exception):
    pass
