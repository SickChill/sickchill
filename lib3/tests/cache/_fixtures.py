import collections
import itertools
import random
from threading import Lock
from threading import Thread
import time
from unittest import TestCase

import pytest

from dogpile.cache import CacheRegion
from dogpile.cache import register_backend
from dogpile.cache.api import CacheBackend
from dogpile.cache.api import NO_VALUE
from dogpile.cache.region import _backend_loader
from . import assert_raises_message
from . import eq_


class _GenericBackendFixture(object):
    @classmethod
    def setup_class(cls):
        backend_cls = _backend_loader.load(cls.backend)
        try:
            arguments = cls.config_args.get("arguments", {})
            backend = backend_cls(arguments)
        except ImportError:
            pytest.skip("Backend %s not installed" % cls.backend)
        cls._check_backend_available(backend)

    def tearDown(self):
        if self._region_inst:
            for key in self._keys:
                self._region_inst.delete(key)
            self._keys.clear()
        elif self._backend_inst:
            self._backend_inst.delete("some_key")

    @classmethod
    def _check_backend_available(cls, backend):
        pass

    region_args = {}
    config_args = {}

    _region_inst = None
    _backend_inst = None

    _keys = set()

    def _region(self, backend=None, region_args={}, config_args={}):
        _region_args = self.region_args.copy()
        _region_args.update(**region_args)
        _config_args = self.config_args.copy()
        _config_args.update(config_args)

        def _store_keys(key):
            if existing_key_mangler:
                key = existing_key_mangler(key)
            self._keys.add(key)
            return key

        self._region_inst = reg = CacheRegion(**_region_args)

        existing_key_mangler = self._region_inst.key_mangler
        self._region_inst.key_mangler = _store_keys
        self._region_inst._user_defined_key_mangler = _store_keys

        reg.configure(backend or self.backend, **_config_args)
        return reg

    def _backend(self):
        backend_cls = _backend_loader.load(self.backend)
        _config_args = self.config_args.copy()
        arguments = _config_args.get("arguments", {})
        self._backend_inst = backend_cls(arguments)
        return self._backend_inst


class _GenericBackendTest(_GenericBackendFixture, TestCase):
    def test_backend_get_nothing(self):
        backend = self._backend()
        eq_(backend.get("some_key"), NO_VALUE)

    def test_backend_delete_nothing(self):
        backend = self._backend()
        backend.delete("some_key")

    def test_backend_set_get_value(self):
        backend = self._backend()
        backend.set("some_key", "some value")
        eq_(backend.get("some_key"), "some value")

    def test_backend_delete(self):
        backend = self._backend()
        backend.set("some_key", "some value")
        backend.delete("some_key")
        eq_(backend.get("some_key"), NO_VALUE)

    def test_region_set_get_value(self):
        reg = self._region()
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")

    def test_region_set_multiple_values(self):
        reg = self._region()
        values = {"key1": "value1", "key2": "value2", "key3": "value3"}
        reg.set_multi(values)
        eq_(values["key1"], reg.get("key1"))
        eq_(values["key2"], reg.get("key2"))
        eq_(values["key3"], reg.get("key3"))

    def test_region_get_zero_multiple_values(self):
        reg = self._region()
        eq_(reg.get_multi([]), [])

    def test_region_set_zero_multiple_values(self):
        reg = self._region()
        reg.set_multi({})

    def test_region_set_zero_multiple_values_w_decorator(self):
        reg = self._region()
        values = reg.get_or_create_multi([], lambda: 0)
        eq_(values, [])

    def test_region_get_or_create_multi_w_should_cache_none(self):
        reg = self._region()
        values = reg.get_or_create_multi(
            ["key1", "key2", "key3"],
            lambda *k: [None, None, None],
            should_cache_fn=lambda v: v is not None,
        )
        eq_(values, [None, None, None])

    def test_region_get_multiple_values(self):
        reg = self._region()
        key1 = "value1"
        key2 = "value2"
        key3 = "value3"
        reg.set("key1", key1)
        reg.set("key2", key2)
        reg.set("key3", key3)
        values = reg.get_multi(["key1", "key2", "key3"])
        eq_([key1, key2, key3], values)

    def test_region_get_nothing_multiple(self):
        reg = self._region()
        reg.delete_multi(["key1", "key2", "key3", "key4", "key5"])
        values = {"key1": "value1", "key3": "value3", "key5": "value5"}
        reg.set_multi(values)
        reg_values = reg.get_multi(
            ["key1", "key2", "key3", "key4", "key5", "key6"]
        )
        eq_(
            reg_values,
            ["value1", NO_VALUE, "value3", NO_VALUE, "value5", NO_VALUE],
        )

    def test_region_get_empty_multiple(self):
        reg = self._region()
        reg_values = reg.get_multi([])
        eq_(reg_values, [])

    def test_region_delete_multiple(self):
        reg = self._region()
        values = {"key1": "value1", "key2": "value2", "key3": "value3"}
        reg.set_multi(values)
        reg.delete_multi(["key2", "key10"])
        eq_(values["key1"], reg.get("key1"))
        eq_(NO_VALUE, reg.get("key2"))
        eq_(values["key3"], reg.get("key3"))
        eq_(NO_VALUE, reg.get("key10"))

    def test_region_set_get_nothing(self):
        reg = self._region()
        reg.delete_multi(["some key"])
        eq_(reg.get("some key"), NO_VALUE)

    def test_region_creator(self):
        reg = self._region()

        def creator():
            return "some value"

        eq_(reg.get_or_create("some key", creator), "some value")

    def test_threaded_dogpile(self):
        # run a basic dogpile concurrency test.
        # note the concurrency of dogpile itself
        # is intensively tested as part of dogpile.
        reg = self._region(config_args={"expiration_time": 0.25})
        lock = Lock()
        canary = []

        def creator():
            ack = lock.acquire(False)
            canary.append(ack)
            time.sleep(0.25)
            if ack:
                lock.release()
            return "some value"

        def f():
            for x in range(5):
                reg.get_or_create("some key", creator)
                time.sleep(0.5)

        threads = [Thread(target=f) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(canary) > 2
        if not reg.backend.has_lock_timeout():
            assert False not in canary
        else:
            assert False in canary

    def test_threaded_get_multi(self):
        reg = self._region(config_args={"expiration_time": 0.25})
        locks = dict((str(i), Lock()) for i in range(11))

        canary = collections.defaultdict(list)

        def creator(*keys):
            assert keys
            ack = [locks[key].acquire(False) for key in keys]

            # print(
            #        ("%s " % thread.get_ident()) + \
            #        ", ".join(sorted("%s=%s" % (key, acq)
            #                    for acq, key in zip(ack, keys)))
            #    )

            for acq, key in zip(ack, keys):
                canary[key].append(acq)

            time.sleep(0.5)

            for acq, key in zip(ack, keys):
                if acq:
                    locks[key].release()
            return ["some value %s" % k for k in keys]

        def f():
            for x in range(5):
                reg.get_or_create_multi(
                    [
                        str(random.randint(1, 10))
                        for i in range(random.randint(1, 5))
                    ],
                    creator,
                )
                time.sleep(0.5)

        f()
        return
        threads = [Thread(target=f) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sum([len(v) for v in canary.values()]) > 10
        for l in canary.values():
            assert False not in l

    def test_region_delete(self):
        reg = self._region()
        reg.set("some key", "some value")
        reg.delete("some key")
        reg.delete("some key")
        eq_(reg.get("some key"), NO_VALUE)

    def test_region_expire(self):
        reg = self._region(config_args={"expiration_time": 0.25})
        counter = itertools.count(1)

        def creator():
            return "some value %d" % next(counter)

        eq_(reg.get_or_create("some key", creator), "some value 1")
        time.sleep(0.4)
        eq_(reg.get("some key", ignore_expiration=True), "some value 1")
        eq_(reg.get_or_create("some key", creator), "some value 2")
        eq_(reg.get("some key"), "some value 2")

    def test_decorated_fn_functionality(self):
        # test for any quirks in the fn decoration that interact
        # with the backend.

        reg = self._region()

        counter = itertools.count(1)

        @reg.cache_on_arguments()
        def my_function(x, y):
            return next(counter) + x + y

        # Start with a clean slate
        my_function.invalidate(3, 4)
        my_function.invalidate(5, 6)
        my_function.invalidate(4, 3)

        eq_(my_function(3, 4), 8)
        eq_(my_function(5, 6), 13)
        eq_(my_function(3, 4), 8)
        eq_(my_function(4, 3), 10)

        my_function.invalidate(4, 3)
        eq_(my_function(4, 3), 11)

    def test_exploding_value_fn(self):
        reg = self._region()

        def boom():
            raise Exception("boom")

        assert_raises_message(
            Exception, "boom", reg.get_or_create, "some_key", boom
        )


class _GenericMutexTest(_GenericBackendFixture, TestCase):
    def test_mutex(self):
        backend = self._backend()
        mutex = backend.get_mutex("foo")

        ac = mutex.acquire()
        assert ac
        ac2 = mutex.acquire(False)
        assert not ac2
        mutex.release()
        ac3 = mutex.acquire()
        assert ac3
        mutex.release()

    def test_mutex_threaded(self):
        backend = self._backend()
        backend.get_mutex("foo")

        lock = Lock()
        canary = []

        def f():
            for x in range(5):
                mutex = backend.get_mutex("foo")
                mutex.acquire()
                for y in range(5):
                    ack = lock.acquire(False)
                    canary.append(ack)
                    time.sleep(0.002)
                    if ack:
                        lock.release()
                mutex.release()
                time.sleep(0.02)

        threads = [Thread(target=f) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert False not in canary

    def test_mutex_reentrant_across_keys(self):
        backend = self._backend()
        for x in range(3):
            m1 = backend.get_mutex("foo")
            m2 = backend.get_mutex("bar")
            try:
                m1.acquire()
                assert m2.acquire(False)
                assert not m2.acquire(False)
                m2.release()

                assert m2.acquire(False)
                assert not m2.acquire(False)
                m2.release()
            finally:
                m1.release()

    def test_reentrant_dogpile(self):
        reg = self._region()

        def create_foo():
            return "foo" + reg.get_or_create("bar", create_bar)

        def create_bar():
            return "bar"

        eq_(reg.get_or_create("foo", create_foo), "foobar")
        eq_(reg.get_or_create("foo", create_foo), "foobar")


class MockMutex(object):
    def __init__(self, key):
        self.key = key

    def acquire(self, blocking=True):
        return True

    def release(self):
        return


class MockBackend(CacheBackend):
    def __init__(self, arguments):
        self.arguments = arguments
        self._cache = {}

    def get_mutex(self, key):
        return MockMutex(key)

    def get(self, key):
        try:
            return self._cache[key]
        except KeyError:
            return NO_VALUE

    def get_multi(self, keys):
        return [self.get(key) for key in keys]

    def set(self, key, value):
        self._cache[key] = value

    def set_multi(self, mapping):
        for key, value in mapping.items():
            self.set(key, value)

    def delete(self, key):
        self._cache.pop(key, None)

    def delete_multi(self, keys):
        for key in keys:
            self.delete(key)


register_backend("mock", __name__, "MockBackend")
