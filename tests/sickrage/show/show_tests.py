# This file is part of SickRage.
#
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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

import os
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import sickbeard

from sickbeard.common import Quality
from sickbeard.tv import TVShow
from sickrage.show.Show import Show
from unittest import TestCase, TestLoader, TextTestRunner


class ShowTests(TestCase):
    def test_validate_indexer_id(self):
        sickbeard.QUALITY_DEFAULT = Quality.FULLHDTV

        show123 = TestTVShow(0, 123)
        show456 = TestTVShow(0, 456)
        show789 = TestTVShow(0, 789)
        sickbeard.showList = [
            show123,
            show456,
            show789,
        ]

        invalid_show_id = ('Invalid show ID', None)

        indexer_id_list = [
            None, '', u'', '123', u'123', '456', u'456', '789', u'789', 123, 456, 789, ['123', '456'], [u'123', u'456'],
            [123, 456]
        ]
        results_list = [
            invalid_show_id, invalid_show_id, invalid_show_id, (None, show123), (None, show123), (None, show456),
            (None, show456), (None, show789), (None, show789), (None, show123), (None, show456), (None, show789),
            invalid_show_id, invalid_show_id, invalid_show_id
        ]

        self.assertEqual(
                len(indexer_id_list), len(results_list),
                'Number of parameters (%d) and results (%d) does not match' % (len(indexer_id_list), len(results_list))
        )

        for (index, indexer_id) in enumerate(indexer_id_list):
            self.assertEqual(Show._validate_indexer_id(indexer_id), results_list[index])


class TestTVShow(TVShow):
    """
    A test ``TVShow`` object that do not need DB access.
    """

    def __init__(self, indexer, indexer_id):
        super(TestTVShow, self).__init__(indexer, indexer_id)

    def loadFromDB(self, skip_nfo=False):
        pass


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    suite = TestLoader().loadTestsFromTestCase(ShowTests)
    TextTestRunner(verbosity=2).run(suite)
