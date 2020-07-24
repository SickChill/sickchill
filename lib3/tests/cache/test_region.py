from collections import defaultdict
import configparser
import datetime
import io
import itertools
import time
from unittest import TestCase

import mock

from dogpile.cache import CacheRegion
from dogpile.cache import exception
from dogpile.cache import make_region
from dogpile.cache import util
from dogpile.cache.api import CacheBackend
from dogpile.cache.api import CachedValue
from dogpile.cache.api import NO_VALUE
from dogpile.cache.proxy import ProxyBackend
from dogpile.cache.region import _backend_loader
from dogpile.cache.region import RegionInvalidationStrategy
from dogpile.cache.region import value_version
from . import assert_raises_message
from . import eq_
from . import is_
from ._fixtures import MockBackend


def key_mangler(key):
    return "HI!" + key


class APITest(TestCase):
    def test_no_value_str(self):
        eq_(str(NO_VALUE), "<dogpile.cache.api.NoValue object>")


class RegionTest(TestCase):
    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        reg.configure(backend, **config_args)
        return reg

    def test_set_name(self):
        my_region = make_region(name="my-name")
        eq_(my_region.name, "my-name")

    def test_instance_from_dict(self):
        my_conf = {
            "cache.example.backend": "mock",
            "cache.example.expiration_time": 600,
            "cache.example.arguments.url": "127.0.0.1",
        }
        my_region = make_region()
        my_region.configure_from_config(my_conf, "cache.example.")
        eq_(my_region.expiration_time, 600)
        assert isinstance(my_region.backend, MockBackend) is True
        eq_(my_region.backend.arguments, {"url": "127.0.0.1"})

    def test_instance_from_config_string(self):
        my_conf = (
            "[xyz]\n"
            "cache.example.backend=mock\n"
            "cache.example.expiration_time=600\n"
            "cache.example.arguments.url=127.0.0.1\n"
            "cache.example.arguments.dogpile_lockfile=false\n"
            "cache.example.arguments.xyz=None\n"
        )

        my_region = make_region()
        config = configparser.ConfigParser()

        config.read_file(io.StringIO(my_conf))

        my_region.configure_from_config(
            dict(config.items("xyz")), "cache.example."
        )
        eq_(my_region.expiration_time, 600)
        assert isinstance(my_region.backend, MockBackend) is True
        eq_(
            my_region.backend.arguments,
            {"url": "127.0.0.1", "dogpile_lockfile": False, "xyz": None},
        )

    def test_datetime_expiration_time(self):
        my_region = make_region()
        my_region.configure(
            backend="mock", expiration_time=datetime.timedelta(days=1, hours=8)
        )
        eq_(my_region.expiration_time, 32 * 60 * 60)

    def test_reject_invalid_expiration_time(self):
        my_region = make_region()

        assert_raises_message(
            exception.ValidationError,
            "expiration_time is not a number or timedelta.",
            my_region.configure,
            "mock",
            "one hour",
        )

    def test_key_mangler_argument(self):
        reg = self._region(init_args={"key_mangler": key_mangler})
        assert reg.key_mangler is key_mangler

        reg = self._region()
        assert reg.key_mangler is None

        MockBackend.key_mangler = lambda self, k: "foo"
        reg = self._region()
        eq_(reg.key_mangler("bar"), "foo")
        MockBackend.key_mangler = None

    def test_key_mangler_impl(self):
        reg = self._region(init_args={"key_mangler": key_mangler})

        reg.set("some key", "some value")
        eq_(list(reg.backend._cache), ["HI!some key"])
        eq_(reg.get("some key"), "some value")
        eq_(
            reg.get_or_create("some key", lambda: "some new value"),
            "some value",
        )
        reg.delete("some key")
        eq_(reg.get("some key"), NO_VALUE)

    def test_dupe_config(self):
        reg = CacheRegion()
        reg.configure("mock")
        assert_raises_message(
            exception.RegionAlreadyConfigured,
            "This region is already configured",
            reg.configure,
            "mock",
        )
        eq_(reg.is_configured, True)

    def test_replace_backend_config(self):
        reg = CacheRegion()

        reg.configure("dogpile.cache.null")
        eq_(reg.is_configured, True)

        null_backend = _backend_loader.load("dogpile.cache.null")
        assert reg.key_mangler is null_backend.key_mangler

        reg.configure("mock", replace_existing_backend=True)
        eq_(reg.is_configured, True)

        assert isinstance(reg.backend, MockBackend)
        assert reg.key_mangler is MockBackend.key_mangler

    def test_replace_backend_config_with_custom_key_mangler(self):
        reg = CacheRegion(key_mangler=key_mangler)

        reg.configure("dogpile.cache.null")
        eq_(reg.is_configured, True)
        assert reg.key_mangler is key_mangler

        reg.configure("mock", replace_existing_backend=True)
        eq_(reg.is_configured, True)
        assert reg.key_mangler is key_mangler

    def test_no_config(self):
        reg = CacheRegion()
        assert_raises_message(
            exception.RegionNotConfigured,
            "No backend is configured on this region.",
            getattr,
            reg,
            "backend",
        )
        eq_(reg.is_configured, False)

    def test_invalid_backend(self):
        reg = CacheRegion()
        assert_raises_message(
            exception.PluginNotFound,
            "Couldn't find cache plugin to load: unknown",
            reg.configure,
            "unknown",
        )
        eq_(reg.is_configured, False)

    def test_set_get_value(self):
        reg = self._region()
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")

    def test_set_get_nothing(self):
        reg = self._region()
        eq_(reg.get("some key"), NO_VALUE)
        eq_(reg.get("some key", expiration_time=10), NO_VALUE)
        reg.invalidate()
        eq_(reg.get("some key"), NO_VALUE)

    def test_creator(self):
        reg = self._region()

        def creator():
            return "some value"

        eq_(reg.get_or_create("some key", creator), "some value")

    def test_multi_creator(self):
        reg = self._region()

        def creator(*keys):
            return ["some value %s" % key for key in keys]

        eq_(
            reg.get_or_create_multi(["k3", "k2", "k5"], creator),
            ["some value k3", "some value k2", "some value k5"],
        )

    def test_remove(self):
        reg = self._region()
        reg.set("some key", "some value")
        reg.delete("some key")
        reg.delete("some key")
        eq_(reg.get("some key"), NO_VALUE)

    def test_expire(self):
        reg = self._region(config_args={"expiration_time": 1})
        counter = itertools.count(1)

        def creator():
            return "some value %d" % next(counter)

        eq_(reg.get_or_create("some key", creator), "some value 1")
        time.sleep(2)
        is_(reg.get("some key"), NO_VALUE)
        eq_(reg.get("some key", ignore_expiration=True), "some value 1")
        eq_(
            reg.get_or_create("some key", creator, expiration_time=-1),
            "some value 1",
        )
        eq_(reg.get_or_create("some key", creator), "some value 2")
        eq_(reg.get("some key"), "some value 2")

    def test_expire_multi(self):
        reg = self._region(config_args={"expiration_time": 1})
        counter = itertools.count(1)

        def creator(*keys):
            return ["some value %s %d" % (key, next(counter)) for key in keys]

        eq_(
            reg.get_or_create_multi(["k3", "k2", "k5"], creator),
            ["some value k3 2", "some value k2 1", "some value k5 3"],
        )
        time.sleep(2)
        is_(reg.get("k2"), NO_VALUE)
        eq_(reg.get("k2", ignore_expiration=True), "some value k2 1")
        eq_(
            reg.get_or_create_multi(["k3", "k2"], creator, expiration_time=-1),
            ["some value k3 2", "some value k2 1"],
        )
        eq_(
            reg.get_or_create_multi(["k3", "k2"], creator),
            ["some value k3 5", "some value k2 4"],
        )
        eq_(reg.get("k2"), "some value k2 4")

    def test_expire_on_get(self):
        reg = self._region(config_args={"expiration_time": 0.5})
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")
        time.sleep(1)
        is_(reg.get("some key"), NO_VALUE)

    def test_ignore_expire_on_get(self):
        reg = self._region(config_args={"expiration_time": 0.5})
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")
        time.sleep(1)
        eq_(reg.get("some key", ignore_expiration=True), "some value")

    def test_override_expire_on_get(self):
        reg = self._region(config_args={"expiration_time": 0.5})
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")
        time.sleep(1)
        eq_(reg.get("some key", expiration_time=5), "some value")
        is_(reg.get("some key"), NO_VALUE)

    def test_expire_override(self):
        reg = self._region(config_args={"expiration_time": 5})
        counter = itertools.count(1)

        def creator():
            return "some value %d" % next(counter)

        eq_(
            reg.get_or_create("some key", creator, expiration_time=1),
            "some value 1",
        )
        time.sleep(2)
        eq_(reg.get("some key"), "some value 1")
        eq_(
            reg.get_or_create("some key", creator, expiration_time=1),
            "some value 2",
        )
        eq_(reg.get("some key"), "some value 2")

    def test_hard_invalidate_get(self):
        reg = self._region()
        reg.set("some key", "some value")
        time.sleep(0.1)
        reg.invalidate()
        is_(reg.get("some key"), NO_VALUE)

    def test_hard_invalidate_get_or_create(self):
        reg = self._region()
        counter = itertools.count(1)

        def creator():
            return "some value %d" % next(counter)

        eq_(reg.get_or_create("some key", creator), "some value 1")

        time.sleep(0.1)
        reg.invalidate()
        eq_(reg.get_or_create("some key", creator), "some value 2")

        eq_(reg.get_or_create("some key", creator), "some value 2")

        reg.invalidate()
        eq_(reg.get_or_create("some key", creator), "some value 3")

        eq_(reg.get_or_create("some key", creator), "some value 3")

    def test_hard_invalidate_get_or_create_multi(self):
        reg = self._region()
        counter = itertools.count(1)

        def creator(*keys):
            return ["some value %s %d" % (k, next(counter)) for k in keys]

        eq_(
            reg.get_or_create_multi(["k1", "k2"], creator),
            ["some value k1 1", "some value k2 2"],
        )

        time.sleep(0.1)
        reg.invalidate()
        eq_(
            reg.get_or_create_multi(["k1", "k2"], creator),
            ["some value k1 3", "some value k2 4"],
        )

        eq_(
            reg.get_or_create_multi(["k1", "k2"], creator),
            ["some value k1 3", "some value k2 4"],
        )

        reg.invalidate()
        eq_(
            reg.get_or_create_multi(["k1", "k2"], creator),
            ["some value k1 5", "some value k2 6"],
        )

        eq_(
            reg.get_or_create_multi(["k1", "k2"], creator),
            ["some value k1 5", "some value k2 6"],
        )

    def test_soft_invalidate_get(self):
        reg = self._region(config_args={"expiration_time": 1})
        reg.set("some key", "some value")
        time.sleep(0.1)
        reg.invalidate(hard=False)
        is_(reg.get("some key"), NO_VALUE)

    def test_soft_invalidate_get_or_create(self):
        reg = self._region(config_args={"expiration_time": 1})
        counter = itertools.count(1)

        def creator():
            return "some value %d" % next(counter)

        eq_(reg.get_or_create("some key", creator), "some value 1")

        time.sleep(0.1)
        reg.invalidate(hard=False)
        eq_(reg.get_or_create("some key", creator), "some value 2")

    def test_soft_invalidate_get_or_create_multi(self):
        reg = self._region(config_args={"expiration_time": 5})
        values = [1, 2, 3]

        def creator(*keys):
            v = values.pop(0)
            return [v for k in keys]

        ret = reg.get_or_create_multi([1, 2], creator)
        eq_(ret, [1, 1])
        time.sleep(0.1)
        reg.invalidate(hard=False)
        ret = reg.get_or_create_multi([1, 2], creator)
        eq_(ret, [2, 2])

    def test_soft_invalidate_requires_expire_time_get(self):
        reg = self._region()
        reg.invalidate(hard=False)
        assert_raises_message(
            exception.DogpileCacheException,
            "Non-None expiration time required for soft invalidation",
            reg.get_or_create,
            "some key",
            lambda: "x",
        )

    def test_soft_invalidate_requires_expire_time_get_multi(self):
        reg = self._region()
        reg.invalidate(hard=False)
        assert_raises_message(
            exception.DogpileCacheException,
            "Non-None expiration time required for soft invalidation",
            reg.get_or_create_multi,
            ["k1", "k2"],
            lambda k: "x",
        )

    def test_should_cache_fn(self):
        reg = self._region()
        values = [1, 2, 3]

        def creator():
            return values.pop(0)

        should_cache_fn = lambda val: val in (1, 3)  # noqa
        ret = reg.get_or_create(
            "some key", creator, should_cache_fn=should_cache_fn
        )
        eq_(ret, 1)
        eq_(reg.backend._cache["some key"][0], 1)
        time.sleep(0.1)
        reg.invalidate()
        ret = reg.get_or_create(
            "some key", creator, should_cache_fn=should_cache_fn
        )
        eq_(ret, 2)
        eq_(reg.backend._cache["some key"][0], 1)
        reg.invalidate()
        ret = reg.get_or_create(
            "some key", creator, should_cache_fn=should_cache_fn
        )
        eq_(ret, 3)
        eq_(reg.backend._cache["some key"][0], 3)

    def test_should_cache_fn_multi(self):
        reg = self._region()
        values = [1, 2, 3]

        def creator(*keys):
            v = values.pop(0)
            return [v for k in keys]

        should_cache_fn = lambda val: val in (1, 3)  # noqa
        ret = reg.get_or_create_multi(
            [1, 2], creator, should_cache_fn=should_cache_fn
        )
        eq_(ret, [1, 1])
        eq_(reg.backend._cache[1][0], 1)
        time.sleep(0.1)
        reg.invalidate()
        ret = reg.get_or_create_multi(
            [1, 2], creator, should_cache_fn=should_cache_fn
        )
        eq_(ret, [2, 2])
        eq_(reg.backend._cache[1][0], 1)
        time.sleep(0.1)
        reg.invalidate()
        ret = reg.get_or_create_multi(
            [1, 2], creator, should_cache_fn=should_cache_fn
        )
        eq_(ret, [3, 3])
        eq_(reg.backend._cache[1][0], 3)

    def test_should_set_multiple_values(self):
        reg = self._region()
        values = {"key1": "value1", "key2": "value2", "key3": "value3"}
        reg.set_multi(values)
        eq_(values["key1"], reg.get("key1"))
        eq_(values["key2"], reg.get("key2"))
        eq_(values["key3"], reg.get("key3"))

    def test_should_get_multiple_values(self):
        reg = self._region()
        values = {"key1": "value1", "key2": "value2", "key3": "value3"}
        reg.set_multi(values)
        reg_values = reg.get_multi(["key1", "key2", "key3"])
        eq_(reg_values, ["value1", "value2", "value3"])

    def test_should_delete_multiple_values(self):
        reg = self._region()
        values = {"key1": "value1", "key2": "value2", "key3": "value3"}
        reg.set_multi(values)
        reg.delete_multi(["key2", "key1000"])
        eq_(values["key1"], reg.get("key1"))
        eq_(NO_VALUE, reg.get("key2"))
        eq_(values["key3"], reg.get("key3"))


class ProxyRegionTest(RegionTest):

    """ This is exactly the same as the region test above, but it goes through
    a dummy proxy.  The purpose of this is to make sure the tests  still run
    successfully even when there is a proxy """

    class MockProxy(ProxyBackend):
        @property
        def _cache(self):
            return self.proxied._cache

    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        config_args["wrap"] = [ProxyRegionTest.MockProxy]
        reg.configure(backend, **config_args)
        return reg


class CustomInvalidationStrategyTest(RegionTest):

    """Try region tests with custom invalidation strategy.

    This is exactly the same as the region test above, but it uses custom
    invalidation strategy. The purpose of this is to make sure the tests
    still run successfully even when there is a proxy.

    """

    class CustomInvalidationStrategy(RegionInvalidationStrategy):
        def __init__(self):
            self._soft_invalidated = None
            self._hard_invalidated = None

        def invalidate(self, hard=None):
            if hard:
                self._soft_invalidated = None
                self._hard_invalidated = time.time()
            else:
                self._soft_invalidated = time.time()
                self._hard_invalidated = None

        def is_invalidated(self, timestamp):
            return (
                self._soft_invalidated and timestamp < self._soft_invalidated
            ) or (
                self._hard_invalidated and timestamp < self._hard_invalidated
            )

        def was_hard_invalidated(self):
            return bool(self._hard_invalidated)

        def is_hard_invalidated(self, timestamp):
            return (
                self._hard_invalidated and timestamp < self._hard_invalidated
            )

        def was_soft_invalidated(self):
            return bool(self._soft_invalidated)

        def is_soft_invalidated(self, timestamp):
            return (
                self._soft_invalidated and timestamp < self._soft_invalidated
            )

    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        invalidator = self.CustomInvalidationStrategy()
        reg.configure(backend, region_invalidator=invalidator, **config_args)
        return reg


class TestProxyValue(object):
    def __init__(self, value):
        self.value = value


class AsyncCreatorTest(TestCase):
    def _fixture(self):
        def async_creation_runner(cache, somekey, creator, mutex):
            try:
                value = creator()
                cache.set(somekey, value)
            finally:
                mutex.release()

        return mock.Mock(side_effect=async_creation_runner)

    def test_get_or_create(self):
        acr = self._fixture()
        reg = CacheRegion(async_creation_runner=acr)
        reg.configure("mock", expiration_time=0.2)

        def some_value():
            return "some value"

        def some_new_value():
            return "some new value"

        eq_(reg.get_or_create("some key", some_value), "some value")
        time.sleep(0.5)
        eq_(reg.get_or_create("some key", some_new_value), "some value")
        eq_(reg.get_or_create("some key", some_new_value), "some new value")
        eq_(
            acr.mock_calls,
            [
                mock.call(
                    reg, "some key", some_new_value, reg._mutex("some key")
                )
            ],
        )

    def test_fn_decorator(self):
        acr = self._fixture()
        reg = CacheRegion(async_creation_runner=acr)
        reg.configure("mock", expiration_time=5)

        canary = mock.Mock()

        @reg.cache_on_arguments()
        def go(x, y):
            canary(x, y)
            return x + y

        eq_(go(1, 2), 3)
        eq_(go(1, 2), 3)

        eq_(canary.mock_calls, [mock.call(1, 2)])

        eq_(go(3, 4), 7)

        eq_(canary.mock_calls, [mock.call(1, 2), mock.call(3, 4)])

        reg.invalidate(hard=False)

        eq_(go(1, 2), 3)

        eq_(
            canary.mock_calls,
            [mock.call(1, 2), mock.call(3, 4), mock.call(1, 2)],
        )

        eq_(
            acr.mock_calls,
            [
                mock.call(
                    reg,
                    "tests.cache.test_region:go|1 2",
                    mock.ANY,
                    reg._mutex("tests.cache.test_region:go|1 2"),
                )
            ],
        )

    def test_fn_decorator_with_kw(self):
        acr = self._fixture()
        reg = CacheRegion(async_creation_runner=acr)
        reg.configure("mock", expiration_time=5)

        @reg.cache_on_arguments()
        def go(x, **kw):
            return x

        test_value = TestProxyValue("Decorator Test")
        self.assertRaises(ValueError, go, x=1, foo=test_value)

        @reg.cache_on_arguments()
        def go2(x):
            return x

        # keywords that match positional names can be passed
        result = go2(x=test_value)
        self.assertTrue(isinstance(result, TestProxyValue))


class ProxyBackendTest(TestCase):
    class GetCounterProxy(ProxyBackend):
        counter = 0

        def get(self, key):
            ProxyBackendTest.GetCounterProxy.counter += 1
            return self.proxied.get(key)

    class SetCounterProxy(ProxyBackend):
        counter = 0

        def set(self, key, value):
            ProxyBackendTest.SetCounterProxy.counter += 1
            return self.proxied.set(key, value)

    class UsedKeysProxy(ProxyBackend):

        """ Keep a counter of hose often we set a particular key"""

        def __init__(self, *args, **kwargs):
            super(ProxyBackendTest.UsedKeysProxy, self).__init__(
                *args, **kwargs
            )
            self._key_count = defaultdict(lambda: 0)

        def setcount(self, key):
            return self._key_count[key]

        def set(self, key, value):
            self._key_count[key] += 1
            self.proxied.set(key, value)

    class NeverSetProxy(ProxyBackend):

        """ A totally contrived example of a Proxy that we pass arguments to.
        Never set a key that matches never_set """

        def __init__(self, never_set, *args, **kwargs):
            super(ProxyBackendTest.NeverSetProxy, self).__init__(
                *args, **kwargs
            )
            self.never_set = never_set
            self._key_count = defaultdict(lambda: 0)

        def set(self, key, value):
            if key != self.never_set:
                self.proxied.set(key, value)

    class CanModifyCachedValueProxy(ProxyBackend):
        def get(self, key):
            value = ProxyBackend.get(self, key)
            assert isinstance(value, CachedValue)
            return value

        def set(self, key, value):
            assert isinstance(value, CachedValue)
            ProxyBackend.set(self, key, value)

    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        reg.configure(backend, **config_args)
        return reg

    def test_cachedvalue_passed(self):
        reg = self._region(
            config_args={"wrap": [ProxyBackendTest.CanModifyCachedValueProxy]}
        )

        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")

    def test_counter_proxies(self):
        # count up the gets and sets and make sure they are passed through
        # to the backend properly.  Test that methods not overridden
        # continue to work

        reg = self._region(
            config_args={
                "wrap": [
                    ProxyBackendTest.GetCounterProxy,
                    ProxyBackendTest.SetCounterProxy,
                ]
            }
        )
        ProxyBackendTest.GetCounterProxy.counter = 0
        ProxyBackendTest.SetCounterProxy.counter = 0

        # set a range of values in the cache
        for i in range(10):
            reg.set(i, i)
        eq_(ProxyBackendTest.GetCounterProxy.counter, 0)
        eq_(ProxyBackendTest.SetCounterProxy.counter, 10)

        # check that the range of values is still there
        for i in range(10):
            v = reg.get(i)
            eq_(v, i)
        eq_(ProxyBackendTest.GetCounterProxy.counter, 10)
        eq_(ProxyBackendTest.SetCounterProxy.counter, 10)

        # make sure the delete function(not overridden) still
        # executes properly
        for i in range(10):
            reg.delete(i)
            v = reg.get(i)
            is_(v, NO_VALUE)

    def test_instance_proxies(self):
        # Test that we can create an instance of a new proxy and
        # pass that to make_region instead of the class.  The two instances
        # should not interfere with each other
        proxy_num = ProxyBackendTest.UsedKeysProxy(5)
        proxy_abc = ProxyBackendTest.UsedKeysProxy(5)
        reg_num = self._region(config_args={"wrap": [proxy_num]})
        reg_abc = self._region(config_args={"wrap": [proxy_abc]})
        for i in range(10):
            reg_num.set(i, True)
            reg_abc.set(chr(ord("a") + i), True)

        for i in range(5):
            reg_num.set(i, True)
            reg_abc.set(chr(ord("a") + i), True)

        # make sure proxy_num has the right counts per key
        eq_(proxy_num.setcount(1), 2)
        eq_(proxy_num.setcount(9), 1)
        eq_(proxy_num.setcount("a"), 0)

        # make sure proxy_abc has the right counts per key
        eq_(proxy_abc.setcount("a"), 2)
        eq_(proxy_abc.setcount("g"), 1)
        eq_(proxy_abc.setcount("9"), 0)

    def test_argument_proxies(self):
        # Test that we can pass an argument to Proxy on creation
        proxy = ProxyBackendTest.NeverSetProxy(5)
        reg = self._region(config_args={"wrap": [proxy]})
        for i in range(10):
            reg.set(i, True)

        # make sure 1 was set, but 5 was not
        eq_(reg.get(5), NO_VALUE)
        eq_(reg.get(1), True)

    def test_actual_backend_proxied(self):
        # ensure that `reg.actual_backend` is the actual backend
        # also ensure that `reg.backend` is a proxied backend
        reg = self._region(
            config_args={
                "wrap": [
                    ProxyBackendTest.GetCounterProxy,
                    ProxyBackendTest.SetCounterProxy,
                ]
            }
        )
        assert isinstance(reg.backend, ProxyBackend)
        assert isinstance(reg.actual_backend, CacheBackend)

    def test_actual_backend_noproxy(self):
        # ensure that `reg.actual_backend` is the actual backend
        # also ensure that `reg.backend` is NOT a proxied backend
        reg = self._region()
        assert isinstance(reg.backend, CacheBackend)
        assert isinstance(reg.actual_backend, CacheBackend)


class LoggingTest(TestCase):
    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        reg.configure(backend, **config_args)
        return reg

    def test_log_time(self):
        reg = self._region()

        times = [50, 55, 60]

        def mock_time():
            return times.pop(0)

        with mock.patch("dogpile.cache.region.log") as mock_log, mock.patch(
            "dogpile.cache.region.time", mock.Mock(time=mock_time)
        ):
            with reg._log_time(["foo", "bar", "bat"]):
                pass

        eq_(
            mock_log.mock_calls,
            [
                mock.call.debug(
                    "Cache value generated in %(seconds).3f "
                    "seconds for key(s): %(keys)r",
                    {
                        "seconds": 5,
                        "keys": util.repr_obj(["foo", "bar", "bat"]),
                    },
                )
            ],
        )

    def test_repr_obj_truncated(self):

        eq_(
            repr(util.repr_obj(["some_big_long_name" for i in range(200)])),
            "['some_big_long_name', 'some_big_long_name', "
            "'some_big_long_name', 'some_big_long_name', 'some_big_long_name',"
            " 'some_big_long_name', 'some_big_long_na ... "
            "(4100 characters truncated) ... me_big_long_name', "
            "'some_big_long_name', 'some_big_long_name', 'some_big_long_"
            "name', 'some_big_long_name', 'some_big_long_name', "
            "'some_big_long_name']",
        )

    def test_log_is_cache_miss(self):
        reg = self._region()

        with mock.patch("dogpile.cache.region.log") as mock_log:
            is_(reg._is_cache_miss(NO_VALUE, "some key"), True)
        eq_(
            mock_log.mock_calls,
            [mock.call.debug("No value present for key: %r", "some key")],
        )

    def test_log_is_value_version_miss(self):

        reg = self._region()
        inv = mock.Mock(is_hard_invalidated=lambda val: True)
        with mock.patch(
            "dogpile.cache.region.log"
        ) as mock_log, mock.patch.object(reg, "region_invalidator", inv):
            is_(
                reg._is_cache_miss(
                    CachedValue(
                        "some value", {"v": value_version - 5, "ct": 500}
                    ),
                    "some key",
                ),
                True,
            )
        eq_(
            mock_log.mock_calls,
            [
                mock.call.debug(
                    "Dogpile version update for key: %r", "some key"
                )
            ],
        )

    def test_log_is_hard_invalidated(self):

        reg = self._region()
        inv = mock.Mock(is_hard_invalidated=lambda val: True)
        with mock.patch(
            "dogpile.cache.region.log"
        ) as mock_log, mock.patch.object(reg, "region_invalidator", inv):
            is_(
                reg._is_cache_miss(
                    CachedValue("some value", {"v": value_version, "ct": 500}),
                    "some key",
                ),
                True,
            )
        eq_(
            mock_log.mock_calls,
            [
                mock.call.debug(
                    "Hard invalidation detected for key: %r", "some key"
                )
            ],
        )
