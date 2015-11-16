# -*- coding: utf-8 -*-

import sys, os.path
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

import test_lib as test
from sickrage.helper.exceptions import ex

class ExceptionsHelperTestCase(unittest.TestCase):

    def test_none_returns_empty(self):
        self.assertEqual(ex(None), u'')

    def test_empty_args_returns_empty(self):
        self.assertEqual(ex(Exception()), u'')

    def test_args_of_none_returns_empty(self):
        self.assertEqual(ex(Exception(None, None)), u'')

    def test_Exception_returns_args_string(self):
        self.assertEqual(ex(Exception('hi')), 'hi')

# TODO why doesn't this work?
#    def test_Exception_returns_args_ustring(self):
#        self.assertEqual(ex(Exception('\xc3\xa4h')), u'äh')

    def test_Exception_returns_concatenated_args_strings(self):
        self.assertEqual(ex(Exception('lots', 'of', 'strings')), 'lots : of : strings')

    def test_Exception_returns_stringified_args(self):
        self.assertEqual(ex(Exception(303)), 'error 303')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        suite = unittest.TestLoader().loadTestsFromName('exceptions_helper_tests.ExceptionsHelperTestCase.test_' + sys.argv[1])
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(ExceptionsHelperTestCase)
        unittest.TextTestRunner(verbosity=2).run(suite)
