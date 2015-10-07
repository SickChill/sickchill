# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
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

from __future__ import with_statement

import sys, os.path

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from sickbeard import logger
from sickrage.helper.exceptions import ex

def error():
    try:
        raise Exception('FAKE EXCEPTION')
    except Exception as e:
        logger.log("FAKE ERROR: " + ex(e), logger.ERROR)
        logger.submit_errors()
        raise


class IssueSubmitterBasicTests(unittest.TestCase):
    def test_submitter(self):
        self.assertRaises(Exception, error)


if __name__ == "__main__":
    print "=================="
    print "STARTING - ISSUE SUBMITTER TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(IssueSubmitterBasicTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
