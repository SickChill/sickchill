# coding=utf-8

"""
Test encoding
"""

from __future__ import print_function, unicode_literals

import locale
import os.path
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sickbeard
from sickbeard import ek, ex
from sickchill.helper.common import sanitize_filename


import six


class EncodingTests(unittest.TestCase):
    """
    Test encodings
    """
    def test_encoding(self):
        """
        Test encoding
        """
        root_dir = 'C:\\Temp\\TV'
        strings = ['Les Enfants De La T\xe9l\xe9', 'RT� One']

        sickbeard.SYS_ENCODING = None

        try:
            locale.setlocale(locale.LC_ALL, "")
            sickbeard.SYS_ENCODING = locale.getpreferredencoding()
        except (locale.Error, IOError):
            pass

        # For OSes that are poorly configured I'll just randomly force UTF-8
        if not sickbeard.SYS_ENCODING or sickbeard.SYS_ENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
            sickbeard.SYS_ENCODING = 'UTF-8'

        for test in strings:
            try:
                show_dir = ek(os.path.join, root_dir, sanitize_filename(test))
                self.assertTrue(isinstance(show_dir, six.text_type))
            except Exception as error:  # pylint: disable=broad-except
                ex(error)

if __name__ == "__main__":
    print("==================")
    print("STARTING - ENCODING TESTS")
    print("==================")
    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(EncodingTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
