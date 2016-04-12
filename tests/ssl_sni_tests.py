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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=line-too-long

"""
Test SNI and SSL
"""

import os.path
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard import ex
import certifi  # pylint: disable=import-error
import requests  # pylint: disable=import-error
import sickbeard.providers as providers


def generator(_provider):
    """
    Generate tests for each provider

    :param test_strings: to generate tests from
    :return: test
    """
    def _connectivity_test():
        """
        Generate tests
        :param self:
        :return: test to run
        """
        if not _provider.url:
            print '{0} has no url set, skipping'.format(_provider.name)
            return

        try:
            requests.head(_provider.url, verify=certifi.old_where(), timeout=10)
        except requests.exceptions.SSLError as error:
            if 'certificate verify failed' in str(error):
                print 'Cannot verify certificate for {0}'.format(_provider.name)
            else:
                print 'SSLError on {0}: {1}'.format(_provider.name, ex(error.message))
                raise
        except requests.exceptions.Timeout:
            print 'Provider timed out'

    return _connectivity_test


class SniTests(unittest.TestCase):
    pass

if __name__ == "__main__":
    print "=================="
    print "STARTING - Provider Connectivity TESTS and SSL/SNI"
    print "=================="
    print "######################################################################"
    # Just checking all providers - we should make this error on non-existent urls.
    for provider in [p for p in providers.make_provider_list()]:
        test_name = 'test_{0}'.format(provider.name)
        test = generator(provider)
        setattr(SniTests, test_name, test)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(SniTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
