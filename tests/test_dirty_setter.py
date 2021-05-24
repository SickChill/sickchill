import unittest

from sickchill.tv import DirtySetter


class DirtySetterTests(unittest.TestCase):
    test_none = DirtySetter(None)
    test_bool = DirtySetter(False)

    def setUp(self) -> None:
        super().setUp()
        self.dirty = True

    def test_dirty_setter(self):
        assert self.dirty
        self.dirty = False

        self.assertIsNone(self.test_none)
        self.test_none = None
        assert not self.dirty

        self.test_none = 1
        assert self.dirty
        self.assertIs(self.test_none, 1)
        assert self.dirty

        self.dirty = False

        self.test_none = None
        assert self.dirty
        self.assertIsNone(self.test_none)

        assert self.dirty
        self.dirty = False

        self.test_none = dict(one=1)
        assert self.dirty
        self.assertDictEqual(self.test_none, dict(one=1))

        assert self.dirty
        self.dirty = False

        self.test_none = [dict(one=1)]
        assert self.dirty
        self.assertListEqual(self.test_none, [dict(one=1)])

        assert self.dirty
        self.dirty = False

        self.test_none = "RANDOM"
        assert self.dirty
        assert self.test_none == "RANDOM"

        assert self.dirty
        self.dirty = False

    def test_dirty_setter_stays_dirty(self):
        assert self.dirty
        self.dirty = False

        assert not self.test_bool
        self.test_bool = True
        assert self.test_bool
        assert self.dirty

        self.test_bool = False
        assert not self.test_bool
        assert self.dirty

        self.test_bool = None
        self.assertIsNone(self.test_bool)
        assert self.dirty
