# coding=utf-8
# This file is part of SickRage.
#
# URL: https://SickRage.GitHub.io
# Git: https://github.com/SickRage/SickRage.git
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

"""
Test GenericMedia
"""

from __future__ import print_function

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import sickbeard
import six

from sickrage.media.GenericMedia import GenericMedia


class GenericMediaTests(unittest.TestCase):
    """
    Test GenericMedia
    """

    def test___init__(self):
        """
        Test __init__
        """
        test_cases = {
            (None, None): (0, 'normal'),
            ('', None): (0, 'normal'),
            ('123', None): (123, 'normal'),
            ('12.3', None): (0, 'normal'),
            (123, None): (123, 'normal'),
            (12.3, None): (12, 'normal'),
            (None, ''): (0, 'normal'),
            ('', ''): (0, 'normal'),
            ('123', ''): (123, 'normal'),
            ('12.3', ''): (0, 'normal'),
            (123, ''): (123, 'normal'),
            (12.3, ''): (12, 'normal'),
            (None, 'normal'): (0, 'normal'),
            ('', 'normal'): (0, 'normal'),
            ('123', 'normal'): (123, 'normal'),
            ('12.3', 'normal'): (0, 'normal'),
            (123, 'normal'): (123, 'normal'),
            (12.3, 'normal'): (12, 'normal'),
            (None, 'thumb'): (0, 'thumb'),
            ('', 'thumb'): (0, 'thumb'),
            ('123', 'thumb'): (123, 'thumb'),
            ('12.3', 'thumb'): (0, 'thumb'),
            (123, 'thumb'): (123, 'thumb'),
            (12.3, 'thumb'): (12, 'thumb'),
            (None, 'foo'): (0, 'normal'),
            ('', 'foo'): (0, 'normal'),
            ('123', 'foo'): (123, 'normal'),
            ('12.3', 'foo'): (0, 'normal'),
            (123, 'foo'): (123, 'normal'),
            (12.3, 'foo'): (12, 'normal'),
        }

        unicode_test_cases = {
            (u'', None): (0, 'normal'),
            (u'123', None): (123, 'normal'),
            (u'12.3', None): (0, 'normal'),
            (None, u''): (0, 'normal'),
            (u'', u''): (0, 'normal'),
            (u'123', u''): (123, 'normal'),
            (u'12.3', u''): (0, 'normal'),
            (123, u''): (123, 'normal'),
            (12.3, u''): (12, 'normal'),
            (None, u'normal'): (0, 'normal'),
            (u'', u'normal'): (0, 'normal'),
            (u'123', u'normal'): (123, 'normal'),
            (u'12.3', u'normal'): (0, 'normal'),
            (123, u'normal'): (123, 'normal'),
            (12.3, u'normal'): (12, 'normal'),
            (None, u'thumb'): (0, 'thumb'),
            (u'', u'thumb'): (0, 'thumb'),
            (u'123', u'thumb'): (123, 'thumb'),
            (u'12.3', u'thumb'): (0, 'thumb'),
            (123, u'thumb'): (123, 'thumb'),
            (12.3, u'thumb'): (12, 'thumb'),
            (None, u'foo'): (0, 'normal'),
            (u'', u'foo'): (0, 'normal'),
            (u'123', u'foo'): (123, 'normal'),
            (u'12.3', u'foo'): (0, 'normal'),
            (123, u'foo'): (123, 'normal'),
            (12.3, u'foo'): (12, 'normal'),
        }

        for test in test_cases, unicode_test_cases:
            for ((indexer_id, media_format), (expected_indexer_id, expected_media_format)) in six.iteritems(test):
                generic_media = GenericMedia(indexer_id, media_format)

                self.assertEqual(generic_media.indexer_id, expected_indexer_id)
                self.assertEqual(generic_media.media_format, expected_media_format)

    def test_get_default_media_name(self):
        """
        Test get_default_media_name
        """

        self.assertEqual(GenericMedia(0, '').get_default_media_name(), '')

    def test_get_media_path(self):
        """
        Test get_media_path
        """

        self.assertEqual(GenericMedia(0, '').get_media_path(), '')

    def test_get_media_root(self):
        """
        Test get_media_root
        """

        sickbeard.PROG_DIR = os.path.join('some', 'path', 'to', 'SickRage')

        self.assertEqual(GenericMedia.get_media_root(), os.path.join('some', 'path', 'to', 'SickRage', 'gui', 'slick'))


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(GenericMediaTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
