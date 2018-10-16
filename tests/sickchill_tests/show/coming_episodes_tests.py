# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

"""
Test coming episodes
"""

# pylint: disable=line-too-long

from __future__ import print_function, unicode_literals

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sickchill.show.ComingEpisodes import ComingEpisodes


import six


class ComingEpisodesTests(unittest.TestCase):
    """
    Test comping episodes
    """
    def test_get_categories(self):
        """
        Tests if get_categories returns the valid format and the right values
        """
        categories_list = [
            None, [], ['A', 'B'], ['A', 'B'], '', 'A|B', 'A|B',
        ]
        results_list = [
            [], [], ['A', 'B'], ['A', 'B'], [], ['A', 'B'], ['A', 'B']
        ]

        self.assertEqual(
            len(categories_list), len(results_list),
            'Number of parameters ({0:d}) and results ({1:d}) does not match'.format(len(categories_list), len(results_list))
        )

        for (index, categories) in enumerate(categories_list):
            self.assertEqual(ComingEpisodes._get_categories(categories), results_list[index])  # pylint: disable=protected-access

    def test_get_categories_map(self):
        """
        Tests if get_categories_map returns the valid format and the right values
        """
        categories_list = [
            None, [], ['A', 'B'], ['A', 'B']
        ]
        results_list = [
            {}, {}, {'A': [], 'B': []}, {'A': [], 'B': []}
        ]

        self.assertEqual(
            len(categories_list), len(results_list),
            'Number of parameters ({0:d}) and results ({1:d}) does not match'.format(len(categories_list), len(results_list))
        )

        for (index, categories) in enumerate(categories_list):
            self.assertEqual(ComingEpisodes._get_categories_map(categories), results_list[index])  # pylint: disable=protected-access

    def test_get_sort(self):
        """
        Tests if get_sort returns the right sort of coming episode
        """
        test_cases = {
            None: 'date',
            '': 'date',
            'wrong': 'date',
            'date': 'date',
            'Date': 'date',
            'network': 'network',
            'NetWork': 'network',
            'show': 'show',
            'Show': 'show',
        }

        unicode_test_cases = {
            '': 'date',
            'wrong': 'date',
            'date': 'date',
            'Date': 'date',
            'network': 'network',
            'NetWork': 'network',
            'show': 'show',
            'Show': 'show',
        }

        for tests in test_cases, unicode_test_cases:
            for (sort, result) in six.iteritems(tests):
                self.assertEqual(ComingEpisodes._get_sort(sort), result)  # pylint: disable=protected-access


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ComingEpisodesTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
