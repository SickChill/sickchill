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

import sys, os.path
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import test_lib as test
import threading

class DBBasicTests(test.SickbeardTestDBCase):
    def setUp(self):
        super(DBBasicTests, self).setUp()
        self.db = test.db.DBConnection()

    def test_select(self):
        self.db.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [0000])

class DBMultiTests(test.SickbeardTestDBCase):
    def setUp(self):
        super(DBMultiTests, self).setUp()
        self.db = test.db.DBConnection()

    def select(self):
        self.db.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [0000])

    def test_threaded(self):
        for i in xrange(4):
            t = threading.Thread(target=self.select)
            t.start()

if __name__ == '__main__':
    print "=================="
    print "STARTING - DB TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(DBBasicTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

    #suite = unittest.TestLoader().loadTestsFromTestCase(DBMultiTests)
    #unittest.TextTestRunner(verbosity=2).run(suite)
