# -*- coding: utf-8 -*-

import unittest


class TestMemcached(unittest.TestCase):

    initstring = 'memcache://localhost:11211'

    def setUp(self):
        from shove.cache.memcached import MemCached
        self.cache = MemCached(self.initstring)

    def tearDown(self):
        self.cache = None

    def test_getitem(self):
        self.cache['test'] = 'test'
        self.assertEqual(self.cache['test'], 'test')

    def test_setitem(self):
        self.cache['test'] = 'test'
        self.assertEqual(self.cache['test'], 'test')

    def test_delitem(self):
        self.cache['test'] = 'test'
        del self.cache['test']
        self.assertEqual('test' in self.cache, False)

    def test_get(self):
        self.assertEqual(self.cache.get('min'), None)

    def test_timeout(self):
        import time
        from shove.cache.memcached import MemCached
        cache = MemCached(self.initstring, timeout=1)
        cache['test'] = 'test'
        time.sleep(1)

        def tmp():
            cache['test']
        self.assertRaises(KeyError, tmp)


if __name__ == '__main__':
    unittest.main()
