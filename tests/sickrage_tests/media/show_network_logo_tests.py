# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sick-rage.github.io
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
Test ShowNetworkLogo
"""

from generic_media_tests import GenericMediaTests

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sickchill.media.ShowNetworkLogo import ShowNetworkLogo


class ShowNetworkLogoTests(GenericMediaTests):
    """
    Test ShowNetworkLogo
    """

    def test_get_default_media_name(self):
        """
        Test get_default_media_name
        """

        self.assertEqual(ShowNetworkLogo(0, '').get_default_media_name(), os.path.join('network', 'nonetwork.png'))


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ShowNetworkLogoTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
