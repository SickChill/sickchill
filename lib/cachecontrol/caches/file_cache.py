import os
import sys
from hashlib import md5

try:
    from pickle import load, dump, HIGHEST_PROTOCOL
except ImportError:
    from cPickle import load, dump, HIGHEST_PROTOCOL

from lockfile import FileLock


class FileCache(object):
    def __init__(self, directory, forever=False):
        self.directory = directory
        self.forever = forever

        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)

    @staticmethod
    def encode(x):
        return md5(x.encode()).hexdigest()

    def _fn(self, name):
        return os.path.join(self.directory, self.encode(name))

    def get(self, key):
        name = self._fn(key)
        if not os.path.exists(name):
            return None

        with open(name, 'rb') as fh:
            try:
                if sys.version < '3':
                    return load(fh)
                else:
                    return load(fh, encoding='latin1')
            except ValueError:
                return None

    def set(self, key, value):
        name = self._fn(key)
        with FileLock(name) as lock:
            with open(lock.path, 'wb') as fh:
                dump(value, fh, HIGHEST_PROTOCOL)

    def delete(self, key):
        name = self._fn(key)
        if not self.forever:
            os.remove(name)