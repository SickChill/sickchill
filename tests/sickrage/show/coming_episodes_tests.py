# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SickRage/SickRage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sickrage.show.ComingEpisodes import ComingEpisodes
from unittest import TestCase, TestLoader, TextTestRunner


class ComingEpisodesTests(TestCase):
    def test_get_categories(self):
        categories_list = [
            None, [], ['A', 'B'], '', 'A|B',
        ]
        results_list = [
            [], [], ['A', 'B'], [], ['A', 'B']
        ]

        self.assertEqual(
                len(categories_list), len(results_list),
                'Number of parameters (%d) and results (%d) does not match' % (len(categories_list), len(results_list))
        )

        for (index, categories) in enumerate(categories_list):
            self.assertEqual(ComingEpisodes._get_categories(categories), results_list[index])

    def test_get_sort(self):
        tests = {
            None: 'date',
            '': 'date',
            'wrong': 'date',
            'date': 'date',
            'DaTe': 'date',
            'network': 'network',
            'NetWork': 'network',
            'show': 'show',
            'Show': 'show',
        }

        for (sort, result) in tests.iteritems():
            self.assertEqual(ComingEpisodes._get_sort(sort), result)


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    suite = TestLoader().loadTestsFromTestCase(ComingEpisodesTests)
    TextTestRunner(verbosity=2).run(suite)
