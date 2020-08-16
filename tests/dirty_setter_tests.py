import unittest

from sickchill.tv import DirtySetter


class DirtySetterTests(unittest.TestCase):
    test_none = DirtySetter(None)
    test_bool = DirtySetter(False)

    def setUp(self) -> None:
        super().setUp()
        self.dirty = True

    def test_dirty_setter(self):
        self.assertTrue(self.dirty)
        self.dirty = False

        self.assertIsNone(self.test_none)
        self.test_none = None
        self.assertFalse(self.dirty)

        self.test_none = 1
        self.assertTrue(self.dirty)
        self.assertIs(self.test_none, 1)
        self.assertTrue(self.dirty)

        self.dirty = False

        self.test_none = None
        self.assertTrue(self.dirty)
        self.assertIsNone(self.test_none)

        self.assertTrue(self.dirty)
        self.dirty = False

        self.test_none = dict(one=1)
        self.assertTrue(self.dirty)
        self.assertDictEqual(self.test_none, dict(one=1))

        self.assertTrue(self.dirty)
        self.dirty = False

        self.test_none = [dict(one=1)]
        self.assertTrue(self.dirty)
        self.assertListEqual(self.test_none, [dict(one=1)])

        self.assertTrue(self.dirty)
        self.dirty = False

        self.test_none = 'RANDOM'
        self.assertTrue(self.dirty)
        self.assertEqual(self.test_none, 'RANDOM')

        self.assertTrue(self.dirty)
        self.dirty = False

    def test_dirty_setter_stays_dirty(self):
        self.assertTrue(self.dirty)
        self.dirty = False

        self.assertFalse(self.test_bool)
        self.test_bool = True
        self.assertTrue(self.test_bool)
        self.assertTrue(self.dirty)

        self.test_bool = False
        self.assertFalse(self.test_bool)
        self.assertTrue(self.dirty)

        self.test_bool = None
        self.assertIsNone(self.test_bool)
        self.assertTrue(self.dirty)
