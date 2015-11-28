# coding=UTF-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: http://github.come/SickRage/SickRage
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

# pylint: disable=line-too-long

"""
Test SNI and SSL
"""

import sys
import os.path
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests  # pylint: disable=import-error
import sickbeard.providers as providers
import certifi  # pylint: disable=import-error
from sickrage.helper.exceptions import ex


class SniTests(unittest.TestCase):
    """
    Test SNI
    """
    self_signed_cert_providers = ["Womble's Index", "Libertalia"]

    def test_sni_urls(self):
        """
        Test SNI urls
        :return:
        """
        print ''
        # Just checking all providers - we should make this error on non-existent urls.
        for provider in [provider for provider in providers.makeProviderList() if provider.name not in self.self_signed_cert_providers]:
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
                    print 'Cannot verify certificate for %s' % provider.name
            except Exception:  # pylint: disable=broad-except
                pass

if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(SniTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
