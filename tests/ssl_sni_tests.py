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

import sys, os.path
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import requests

import sickbeard.providers as providers
import certifi
from sickrage.helper.exceptions import ex


class SNI_Tests(unittest.TestCase):
    def test_SNI_URLS(self):
        print ''
        #Just checking all providers - we should make this error on non-existent urls.
        for provider in providers.makeProviderList():
            print 'Checking %s' % provider.name
            try:
                requests.head(provider.url, verify=certifi.where(), timeout=5)
            except requests.exceptions.Timeout:
                pass
            except requests.exceptions.SSLError as error:
                if u'SSL3_GET_SERVER_CERTIFICATE' not in ex(error):
                    print 'SSLError on %s: %s' % (provider.name, ex(error.message))
                    raise
                else:
                    print  'Cannot verify certificate for %s' % provider.name
                    pass
            except Exception:
                pass

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(SNI_Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
