# coding=UTF-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: http://github.come/SiCKRAGETV/SickRage
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

import unittest
import sys, os.path
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib import requests
from sickbeard.providers.torrentday import provider as torrentday
from sickbeard.providers.rarbg import provider as rarbg
from sickbeard.providers.scc import provider as sceneaccess

enabled_sni = True
if sys.version_info < (2, 7, 9):
    try:
        import cryptography
    except ImportError:
        enabled_sni = False

class SNI_Tests(unittest.TestCase):
    def test_SNI_URLS(self):
        if not enabled_sni:
            print("\nSNI is disabled when the cryptography module is missing, you may encounter SSL errors!")
        else:
            for provider in [ torrentday, rarbg, sceneaccess ]:
                #print 'Checking ' + provider.name
                self.assertEqual(requests.get(provider.url).status_code, 200)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(SNI_Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
