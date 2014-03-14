import os
import codecs

from hashlib import md5

try:
    from pickle import load, dump
except ImportError:
    from cPickle import load, dump

from lib.lockfile import FileLock


class FileCache(object):

    def __init__(self, directory, forever=False):
        self.directory = directory
        self.forever = forever

        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)

    def encode(self, x):
        return md5(x.encode()).hexdigest()

    def _fn(self, name):
        return os.path.join(self.directory, self.encode(name))

    def get(self, key):
        name = self._fn(key)
        if os.path.exists(name):
            return load(codecs.open(name, 'rb'))

    def set(self, key, value):
        name = self._fn(key)
        lock = FileLock(name)
        with lock:
            with codecs.open(lock.path, 'w+b') as fh:
                dump(value, fh)

    def delete(self, key):
        if not self.forever:
            os.remove(self._fn(key))
