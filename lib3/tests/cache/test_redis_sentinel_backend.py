from concurrent.futures import ThreadPoolExecutor
import os
from threading import Event
import time
from unittest import TestCase

import pytest

from . import eq_
from ._fixtures import _GenericBackendFixture
from ._fixtures import _GenericBackendTest
from ._fixtures import _GenericMutexTest

REDIS_HOST = "127.0.0.1"
REDIS_PORT = int(os.getenv("DOGPILE_REDIS_SENTINEL_PORT", "26379"))
expect_redis_running = os.getenv("DOGPILE_REDIS_SENTINEL_PORT") is not None


class _TestRedisSentinelConn(object):

    @classmethod
    def _check_backend_available(cls, backend):
        try:
            backend._create_client()
            backend.set("x", "y")
            # on py3k it appears to return b"y"
            assert backend.get("x") == "y"
            backend.delete("x")
        except Exception:
            if not expect_redis_running:
                pytest.skip(
                    "redis is not running or "
                    "otherwise not functioning correctly"
                )
            else:
                raise


class RedisSentinelTest(_TestRedisSentinelConn, _GenericBackendTest):
    backend = "dogpile.cache.redis_sentinel"
    config_args = {
        "arguments": {
            "sentinels": [[REDIS_HOST, REDIS_PORT]],
            "service_name": "pifpaf",
            "db": 0,
            "distributed_lock": False,
        }
    }


class RedisSentinelDistributedMutexTest(
    _TestRedisSentinelConn, _GenericMutexTest
):
    backend = "dogpile.cache.redis_sentinel"
    config_args = {
        "arguments": {
            "sentinels": [[REDIS_HOST, REDIS_PORT]],
            "service_name": "pifpaf",
            "db": 0,
            "distributed_lock": True,
        }
    }


class RedisSentinelAsyncCreationTest(
    _TestRedisSentinelConn, _GenericBackendFixture, TestCase
):
    backend = "dogpile.cache.redis_sentinel"
    config_args = {
        "arguments": {
            "sentinels": [[REDIS_HOST, REDIS_PORT]],
            "service_name": "pifpaf",
            "db": 0,
            "distributed_lock": True,
            # This is the important bit:
            "thread_local_lock": False,
        }
    }

    def test_distributed_async_locks(self):
        pool = ThreadPoolExecutor(max_workers=1)
        ev = Event()

        # A simple example of how people may implement an async runner -
        # plugged into a thread pool executor.
        def asyncer(cache, key, creator, mutex):
            def _call():
                try:
                    value = creator()
                    cache.set(key, value)
                finally:
                    # If a thread-local lock is used here, this will fail
                    # because generally the async calls run in a different
                    # thread (that's the point of async creators).
                    try:
                        mutex.release()
                    except Exception:
                        pass
                    else:
                        ev.set()

            return pool.submit(_call)

        reg = self._region(
            region_args={"async_creation_runner": asyncer},
            config_args={"expiration_time": 0.1},
        )

        @reg.cache_on_arguments()
        def blah(k):
            return k * 2

        # First call adds to the cache without calling the async creator.
        eq_(blah("asd"), "asdasd")

        # Wait long enough to cause the cached value to get stale.
        time.sleep(0.3)

        # This will trigger the async runner and return the stale value.
        eq_(blah("asd"), "asdasd")

        # Wait for the the async runner to finish or timeout. If the mutex
        # release errored, then the event won't be set and we'll timeout.
        # On <= Python 3.1, wait returned nothing. So check is_set after.
        ev.wait(timeout=1.0)
        eq_(ev.is_set(), True)
