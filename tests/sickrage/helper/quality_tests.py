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

from sickbeard.common import ANY, HD, HD1080p, HD720p, Quality, SD
from sickrage.helper.quality import get_quality_string
from unittest import TestCase, TestLoader, TextTestRunner


class QualityTests(TestCase):
    def test_get_quality_string(self):
        tests = {
            ANY: 'Any',
            HD: 'HD',
            HD720p: 'HD720p',
            HD1080p: 'HD1080p',
            Quality.FULLHDBLURAY: '1080p BluRay',
            Quality.FULLHDTV: '1080p HDTV',
            Quality.FULLHDWEBDL: '1080p WEB-DL',
            Quality.HDBLURAY: '720p BluRay',
            Quality.HDTV: '720p HDTV',
            Quality.HDWEBDL: '720p WEB-DL',
            Quality.NONE: 'N/A',
            Quality.RAWHDTV: 'RawHD',
            Quality.SDDVD: 'SD DVD',
            Quality.SDTV: 'SDTV',
            Quality.UNKNOWN: 'Unknown',
            SD: 'SD',
            1000000: 'Custom',  # An invalid quality number to test the default case
        }

        for (quality, result) in tests.iteritems():
            self.assertEqual(get_quality_string(quality), result)


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    suite = TestLoader().loadTestsFromTestCase(QualityTests)
    TextTestRunner(verbosity=2).run(suite)
