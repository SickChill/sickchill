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
Test GenericProvider
"""

from __future__ import print_function

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sickrage.providers.GenericProvider import GenericProvider


class GenericProviderTests(unittest.TestCase):
    """
    Test GenericProvider
    """

    def test_get_id(self):
        """
        Test get_id
        """
        test_cases = {
            None: '',
            123: '123',
            12.3: '12_3',
            0: '',
            -123: '_123',
            -12.3: '_12_3',
            '': '',
            ' ': '',
            '123': '123',
            ' 123 ': '123',
            '12.3': '12_3',
            ' 12.3 ': '12_3',
            '0': '0',
            ' 0 ': '0',
            '-123': '_123',
            ' -123 ': '_123',
            '-12.3': '_12_3',
            ' -12.3 ': '_12_3',
            'abc': 'abc',
            ' abc ': 'abc',
            'ABC': 'abc',
            ' ABC ': 'abc',
            '.def': '_def',
            'g,hi': 'g_hi',
            'jk!l': 'jk_l',
            'mno?': 'mno_',
            '_pqr$': '_pqr_',
        }

        unicode_test_cases = {
            u'': '',
            u' ': '',
            u'123': '123',
            u' 123 ': '123',
            u'12.3': '12_3',
            u' 12.3 ': '12_3',
            u'0': '0',
            u' 0 ': '0',
            u'-123': '_123',
            u' -123 ': '_123',
            u'-12.3': '_12_3',
            u' -12.3 ': '_12_3',
            u'abc': 'abc',
            u' abc ': 'abc',
            u'ABC': 'abc',
            u' ABC ': 'abc',
            u'.def': '_def',
            u'g,hi': 'g_hi',
            u'jk!l': 'jk_l',
            u'mno?': 'mno_',
            u'_pqr$': '_pqr_',
        }

        for test in test_cases, unicode_test_cases:
            for (name, result) in test.iteritems():
                self.assertEqual(GenericProvider(name).get_id(), result)

    def test_image_name(self):
        """
        Test image_name
        """
        test_cases = {
            None: '.png',
            123: '123.png',
            12.3: '12_3.png',
            0: '.png',
            -123: '_123.png',
            -12.3: '_12_3.png',
            '': '.png',
            ' ': '.png',
            '123': '123.png',
            ' 123 ': '123.png',
            '12.3': '12_3.png',
            ' 12.3 ': '12_3.png',
            '0': '0.png',
            ' 0 ': '0.png',
            '-123': '_123.png',
            ' -123 ': '_123.png',
            '-12.3': '_12_3.png',
            ' -12.3 ': '_12_3.png',
            'abc': 'abc.png',
            ' abc ': 'abc.png',
            'ABC': 'abc.png',
            ' ABC ': 'abc.png',
            '.def': '_def.png',
            'g,hi': 'g_hi.png',
            'jk!l': 'jk_l.png',
            'mno?': 'mno_.png',
            '_pqr$': '_pqr_.png',
        }

        unicode_test_cases = {
            u'': '.png',
            u' ': '.png',
            u'123': '123.png',
            u' 123 ': '123.png',
            u'12.3': '12_3.png',
            u' 12.3 ': '12_3.png',
            u'0': '0.png',
            u' 0 ': '0.png',
            u'-123': '_123.png',
            u' -123 ': '_123.png',
            u'-12.3': '_12_3.png',
            u' -12.3 ': '_12_3.png',
            u'abc': 'abc.png',
            u' abc ': 'abc.png',
            u'ABC': 'abc.png',
            u' ABC ': 'abc.png',
            u'.def': '_def.png',
            u'g,hi': 'g_hi.png',
            u'jk!l': 'jk_l.png',
            u'mno?': 'mno_.png',
            u'_pqr$': '_pqr_.png',
        }

        for test in test_cases, unicode_test_cases:
            for (name, result) in test.iteritems():
                self.assertEqual(GenericProvider(name).image_name(), result)

    def test_is_active(self):
        """
        Test is_active
        """
        self.assertFalse(GenericProvider('Test Provider').is_active())

    def test_is_enabled(self):
        """
        Test is_enabled
        """
        self.assertFalse(GenericProvider('Test Provider').is_enabled())

    def test_make_id(self):
        """
        Test make_id
        """
        test_cases = {
            None: '',
            123: '123',
            12.3: '12_3',
            0: '',
            -123: '_123',
            -12.3: '_12_3',
            '': '',
            ' ': '',
            '123': '123',
            ' 123 ': '123',
            '12.3': '12_3',
            ' 12.3 ': '12_3',
            '0': '0',
            ' 0 ': '0',
            '-123': '_123',
            ' -123 ': '_123',
            '-12.3': '_12_3',
            ' -12.3 ': '_12_3',
            'abc': 'abc',
            ' abc ': 'abc',
            'ABC': 'abc',
            ' ABC ': 'abc',
            '.def': '_def',
            'g,hi': 'g_hi',
            'jk!l': 'jk_l',
            'mno?': 'mno_',
            '_pqr$': '_pqr_',
        }

        unicode_test_cases = {
            u'': '',
            u' ': '',
            u'123': '123',
            u' 123 ': '123',
            u'12.3': '12_3',
            u' 12.3 ': '12_3',
            u'0': '0',
            u' 0 ': '0',
            u'-123': '_123',
            u' -123 ': '_123',
            u'-12.3': '_12_3',
            u' -12.3 ': '_12_3',
            u'abc': 'abc',
            u' abc ': 'abc',
            u'ABC': 'abc',
            u' ABC ': 'abc',
            u'.def': '_def',
            u'g,hi': 'g_hi',
            u'jk!l': 'jk_l',
            u'mno?': 'mno_',
            u'_pqr$': '_pqr_',
        }

        for test in test_cases, unicode_test_cases:
            for (name, result) in test.iteritems():
                self.assertEqual(GenericProvider.make_id(name), result)

    def test_seed_ratio(self):
        """
        Test seed_ratio
        """
        self.assertEqual(GenericProvider('Test Provider').seed_ratio(), '')

    def test__check_auth(self):
        """
        Test _check_auth
        """
        self.assertTrue(GenericProvider('Test Provider')._check_auth())

    def test_login(self):
        """
        Test login
        """
        self.assertTrue(GenericProvider('Test Provider').login())

    def test_search(self):
        """
        Test search
        """
        test_cases = {
            None: [],
            123: [],
            12.3: [],
            -123: [],
            -12.3: [],
            '': [],
            '123': [],
            '12.3': [],
            '-123': [],
            '-12.3': [],
        }

        unicode_test_cases = {
            u'': [],
            u'123': [],
            u'12.3': [],
            u'-123': [],
            u'-12.3': [],
        }

        for test in test_cases, unicode_test_cases:
            for (search_params, result) in test.iteritems():
                self.assertEqual(GenericProvider('Test Provider').search(search_params), result)

    def test__get_size(self):
        """
        Test _get_size
        """
        self.assertEqual(GenericProvider('Test Provider')._get_size(None), -1)

    def test__get_storage_dir(self):
        """
        Test _get_storage_dir
        """
        self.assertEqual(GenericProvider('Test Provider')._get_storage_dir(), '')

    def test__get_title_and_url(self):
        """
        Test _get_title_and_url
        """
        items_list = [
            None, {}, {'link': None, 'title': None, 'seeders': None, 'leechers': None}, {'link': '', 'title': '', 'seeders': '1', 'leechers': '1'},
            {'link': 'http://www.google.com/&amp;foo=bar%26tr%3Dtest', 'title': 'Some Title', 'seeders': '10', 'leechers': '0'}
        ]
        results_list = [
            ('', '', '', ''), ('', '', '', ''), ('', '', '', ''), ('', '', '1', '1'), ('Some.Title', 'http://www.google.com/&foo=bar&tr=test', '10', '0')
        ]

        unicode_items_list = [
            {'link': u'', 'title': u'', 'seeders': u'', 'leechers': u''},
            {'link': u'http://www.google.com/&amp;foo=bar%26tr%3Dtest', 'title': u'Some Title', 'seeders': '1', 'leechers': '1'}
        ]
        unicode_results_list = [
            ('', '', '', ''), ('Some.Title', 'http://www.google.com/&foo=bar&tr=test', '1', '1')
        ]

        self.assertEqual(
            len(items_list), len(results_list),
            'Number of parameters (%d) and results (%d) does not match' % (len(items_list), len(results_list))
        )

        self.assertEqual(
            len(unicode_items_list), len(unicode_results_list),
            'Number of parameters (%d) and results (%d) does not match' % (
                len(unicode_items_list), len(unicode_results_list))
        )

        for (index, item) in enumerate(items_list):
            self.assertEqual(GenericProvider('Test Provider')._get_title_and_url(item), results_list[index])

        for (index, item) in enumerate(unicode_items_list):
            self.assertEqual(GenericProvider('Test Provider')._get_title_and_url(item), unicode_results_list[index])

    def test__verify_download(self):
        """
        Test _verify_download
        """
        self.assertTrue(GenericProvider('Test Provider')._verify_download())


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(GenericProviderTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
