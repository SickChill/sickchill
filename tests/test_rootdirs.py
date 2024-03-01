import logging
import tempfile
from pathlib import Path
from unittest import skip, TestCase
from unittest.mock import patch

from sickchill.helper.rootdirs import RootDirectories

logging.basicConfig(format="{levelname} :: {message}", style="{", level=logging.DEBUG)


@skip("Not implemented")
class TestRootDirectories(TestCase):
    path_one = None
    path_two = None
    patcher = None
    settings_root_dirs = None

    @classmethod
    def setUpClass(cls):
        cls.path_one = Path(__file__).parent.resolve()
        cls.path_two = Path(__file__).parent.parent.resolve()

        cls.settings_root_dirs = f"1|{cls.path_one}|{cls.path_two}"

        cls.patcher = patch("sickchill.settings.ROOT_DIRS", cls.settings_root_dirs)
        cls.patcher.start()
        cls.addClassCleanup(cls.patcher.stop)

    def setUp(self):
        self.object = RootDirectories()
        self.initial = str(self.object)
        self.initial_length = len(self.object)
        self.initial_list = [item for item in self.object]

        self.initial_index = self.object.default_root_index

    def test_parse(self):
        from sickchill import settings

        self.object.parse()
        self.assertEqual(self.initial, str(self.object))

        self.object.parse(settings.ROOT_DIRS)
        self.assertEqual(self.initial, str(self.object))

        self.object.root_directories.clear()
        self.object.default_root_index = None

        self.object.parse(settings.ROOT_DIRS)
        self.assertEqual(self.initial, str(self.object))
        self.assertEqual(len(self.object.root_directories), self.initial_length)
        self.assertEqual(self.object.root_directories, self.initial_list)
        self.assertEqual(self.object.default_root_index, self.initial_index)

        self.object.parse(root_directories_list=settings.ROOT_DIRS.split("|"))
        self.assertEqual(len(self.object.root_directories), self.initial_length)
        self.assertEqual(self.object.root_directories, self.initial_list)
        self.assertEqual(self.object.default_root_index, self.initial_index)
        self.assertEqual(self.object.root_directories, RootDirectories(root_directories_string=self.settings_root_dirs).root_directories)

    def test_add(self):
        self.object.add(self.path_one)
        self.assertEqual(len(self.object.root_directories), self.initial_length, msg=f"{self.object.root_directories}")
        self.assertEqual(self.object.root_directories, self.initial_list)
        self.assertEqual(self.object.default_root_index, self.initial_index)

        self.object.add(tempfile.tempdir)

        self.assertNotEqual(len(self.object.root_directories), self.initial_length)
        self.assertNotEqual(self.object.root_directories, self.initial_list)
        self.assertEqual(self.object.default_root_index, self.initial_index)

    def test_delete(self):
        self.object.delete(self.path_one)
        self.assertLess(len(self.object), self.initial_length)

        length = len(self.object)
        self.object.delete(self.path_one)
        self.assertEqual(len(self.object), length)
        self.assertIsNotNone(self.object.default_root_index)
        self.assertEqual(self.object.default_root_index, self.initial_index)

        self.object.delete(self.path_two)
        self.assertFalse(len(self.object))

        self.assertIsNone(self.object.default_root_index)

    def test_default(self):
        self.object.add(tempfile.tempdir)
        self.assertEqual(self.object.default, self.initial_index)

        self.object.default = 10
        self.assertEqual(self.object.default, self.initial_index)
        self.assertEqual(self.object.default, self.initial_index)

        self.object.delete(self.path_one)
        self.object.delete(self.path_two)
        self.object.delete(tempfile.tempdir)
        self.assertIsNone(self.object.default, self.object.root_directories)

        self.object.add(tempfile.tempdir)
        self.assertEqual(self.object.default, self.initial_index)

    def test_info(self):
        info = self.object.info()
        self.assertEqual(len(info), len(self.object))

        self.assertIn("valid", info[0])
        self.assertEqual(info[0]["valid"], True)

        self.assertIn("default", info[0])
        self.assertEqual(info[0]["default"], True)

        self.assertEqual(info[1]["default"], False)
        self.assertEqual(info[0]["location"], str(self.path_one))

        self.object.delete(self.path_one)
        self.object.delete(self.path_two)

        info = self.object.info()
        self.assertEqual(len(info), len(self.object))
        self.assertEqual(info, {})

    def test_str(self):
        self.assertEqual(self.object.__str__(), self.settings_root_dirs)

        self.object.add(tempfile.tempdir)
        self.assertNotEqual(self.object.__str__(), self.settings_root_dirs)

        self.object.delete(tempfile.tempdir)
        self.assertEqual(self.object.__str__(), self.settings_root_dirs)

    def test_getitem(self):
        self.assertEqual(self.object[1], self.path_one)
        self.assertEqual(self.object[1], self.object.root_directories[0])

    def test_setitem(self):
        self.assertEqual(self.object[1], self.path_one)
        self.object[1] = self.path_two
        self.assertEqual(self.object[1], self.path_two)

    def test_del(self):
        del self.object[1]
        self.assertEqual(self.object[1], self.path_two)
        self.assertLess(len(self.object), self.initial_length)

    def test_contains(self):
        self.assertFalse(tempfile.tempdir in self.object)
        self.assertTrue(self.path_one in self.object)
        self.assertTrue(self.path_two in self.object)

        self.object.delete(self.path_one)
        self.assertFalse(self.path_one in self.object)
        self.assertTrue(self.path_two in self.object)

    def test_iter(self):
        object_list = []
        for item in self.object:
            object_list.append(item)

        self.assertEqual(object_list, self.object.root_directories)

    def test_len(self):
        self.assertEqual(len(self.object), len(self.object.root_directories))
