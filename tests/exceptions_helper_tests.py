# -*- coding: utf-8 -*-

"""
Test exceptions helpers
"""

# pylint: disable=line-too-long

from __future__ import print_function, unicode_literals

import os.path
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickchill import ex


import six


class ExceptionsHelperTestCase(unittest.TestCase):
    """
    Test exceptions helper
    """

    def test_none_returns_empty(self):
        """
        Test none returns empty
        """
        self.assertEqual(ex(None), '')

    def test_empty_args_returns_empty(self):
        """
        Test empty args returns empty
        """
        self.assertEqual(ex(Exception()), '')

    def test_args_of_none_returns_empty(self):
        """
        Test args of none returns empty
        """
        self.assertEqual(ex(Exception(None, None)), '')

    def test_ex_ret_args_string(self):
        """
        Test exception returns args strings
        :return:
        """
        self.assertEqual(ex(Exception('hi')), 'hi')

    # TODO why doesn't this work?@
    @unittest.skip('Errors with six.text_type conversion')
    def test_ex_ret_args_ustring(self):
        """
        Test exception returns args ustring
        """
        self.assertEqual(ex(Exception('\xc3\xa4h')), 'äh')

    def test_ex_ret_concat_args_strings(self):
        """
        Test exception returns concatenated args and strings
        """
        self.assertEqual(ex(Exception('lots', 'of', 'strings')), 'lots : of : strings')

    def test_ex_ret_stringed_args(self):
        """
        Test exception returns stringed args
        """
        self.assertEqual(ex(Exception(303)), 'error 303')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        SUITE = unittest.TestLoader().loadTestsFromName('exceptions_helper_tests.ExceptionsHelperTestCase.test_' + sys.argv[1])
        unittest.TextTestRunner(verbosity=2).run(SUITE)
    else:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(ExceptionsHelperTestCase)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
