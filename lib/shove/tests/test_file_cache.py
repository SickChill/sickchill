# -*- coding: utf-8 -*-

import unittest


class TestFileCache(unittest.TestCase):

    initstring = 'file://test'

    def setUp(self):
        from shove.cache.file import FileCache
        self.cache = FileCache(self.initstring)

    def tearDown(self):
        import os
        self.cache = None
        for x in os.listdir('test'):
            os.remove(os.path.join('test', x))
        os.rmdir('test')

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
        from shove.cache.file import FileCache
        cache = FileCache(self.initstring, timeout=1)
        cache['test'] = 'test'
        time.sleep(2)

        def tmp():
            cache['test']
        self.assertRaises(KeyError, tmp)

    def test_cull(self):
        from shove.cache.file import FileCache
        cache = FileCache(self.initstring, max_entries=1)
        cache['test'] = 'test'
        cache['test2'] = 'test'
        num = len(cache)
        self.assertEquals(num, 1)


if __name__ == '__main__':
    unittest.main()
