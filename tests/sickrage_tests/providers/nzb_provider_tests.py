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
Test NZBProvider
"""

from __future__ import print_function

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import sickbeard

from generic_provider_tests import GenericProviderTests
from sickrage.providers.GenericProvider import GenericProvider
from sickrage.providers.nzb.NZBProvider import NZBProvider


class NZBProviderTests(GenericProviderTests):
    """
    Test NZBProvider
    """

    def test___init__(self):
        """
        Test __init__
        """
        self.assertEqual(NZBProvider('Test Provider').provider_type, GenericProvider.NZB)

    def test_is_active(self):
        """
        Test is_active
        """
        test_cases = {
            (False, False): False,
            (False, None): False,
            (False, True): False,
            (None, False): False,
            (None, None): False,
            (None, True): False,
            (True, False): False,
            (True, None): False,
            (True, True): True,
        }

        for ((use_nzb, enabled), result) in test_cases.iteritems():
            sickbeard.USE_NZBS = use_nzb

            provider = NZBProvider('Test Provider')
            provider.enabled = enabled

            self.assertEqual(provider.is_active(), result)

    def test__get_size(self):
        """
        Test _get_size
        """
        items_list = [
            None, {}, {'links': None}, {'links': []}, {'links': [{}]},
            {'links': [{'length': 1}, {'length': None}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': ''}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': '0'}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': '123'}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': '12.3'}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': '-123'}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': '-12.3'}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': 0}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': 123}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': 12.3}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': -123}, {'length': 3}]},
            {'links': [{'length': 1}, {'length': -12.3}, {'length': 3}]},
        ]
        results_list = [
            -1, -1, -1, -1, -1, -1, -1, 0, 123, -1, -123, -1, 0, 123, 12, -123, -12
        ]

        unicode_items_list = [
            {u'links': None}, {u'links': []}, {u'links': [{}]},
            {u'links': [{u'length': 1}, {u'length': None}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': u''}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': u'0'}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': u'123'}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': u'12.3'}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': u'-123'}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': u'-12.3'}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': 0}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': 123}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': 12.3}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': -123}, {u'length': 3}]},
            {u'links': [{u'length': 1}, {u'length': -12.3}, {u'length': 3}]},
        ]
        unicode_results_list = [
            -1, -1, -1, -1, -1, 0, 123, -1, -123, -1, 0, 123, 12, -123, -12
        ]

        self.assertEqual(
            len(items_list), len(results_list),
            'Number of parameters ({0:d}) and results ({1:d}) does not match'.format(len(items_list), len(results_list))
        )

        self.assertEqual(
            len(unicode_items_list), len(unicode_results_list),
            'Number of parameters ({0:d}) and results ({1:d}) does not match'.format(
                len(unicode_items_list), len(unicode_results_list))
        )

        for (index, item) in enumerate(items_list):
            self.assertEqual(NZBProvider('Test Provider')._get_size(item), results_list[index])

        for (index, item) in enumerate(unicode_items_list):
            self.assertEqual(NZBProvider('Test Provider')._get_size(item), unicode_results_list[index])

    def test__get_storage_dir(self):
        """
        Test _get_storage_dir
        """
        test_cases = [
            None, 123, 12.3, '', os.path.join('some', 'path', 'to', 'folder')
        ]

        for nzb_dir in test_cases:
            sickbeard.NZB_DIR = nzb_dir

            self.assertEqual(NZBProvider('Test Provider')._get_storage_dir(), nzb_dir)


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(NZBProviderTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
