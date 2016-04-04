# coding=utf-8
# This file is part of SickRage.
#
# URL: https://SickRage.GitHub.io
# Git: https://github.com/SickRage/SickRage.git
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

"""
Test ThePirateBay Result Parsing
"""

from __future__ import print_function, unicode_literals

import os
import sys

import unittest
from vcr_unittest import VCRTestCase

# Have to do this before importing sickbeard
sys.path.insert(1, 'lib')

import sickbeard

overwrite_cassettes = False


class ThePirateBayParsingTests(VCRTestCase):
    def __init__(self, test):
        super(ThePirateBayParsingTests, self).__init__(test)

        self.provider = sickbeard.providers.getProviderModule(os.path.basename(__file__)[:-3]).provider
        self.provider.session.verify = False

        self.search_strings = {
            'rss': {'RSS': ['']},
            'episode': {'Episode': ['Game of Thrones S05E08']},
            'season': {'Season': ['Game of Thrones S05']}
        }

    def _get_vcr_kwargs(self):
        if overwrite_cassettes:
            return {'record_mode': 'new_episodes'}
        return {'record_mode': 'once'}

    def _get_cassette_name(self):
        return self.provider.get_id() + '.yaml'

    def test_rss_search(self):
        results = self.provider.search(self.search_strings['rss'])

        self.assertTrue(self.cassette.requests)
        self.assertTrue(results)
        self.assertTrue(len(self.cassette))

        if len(self.cassette) > 1:
            print('Url is being called more than once, redirecting? %s',
                  [x.url for x in self.cassette.requests])

    def test_season_search(self):
        results = self.provider.search(self.search_strings['season'])

        self.assertTrue(self.cassette.requests)
        self.assertTrue(results)
        self.assertTrue(len(self.cassette))

        if len(self.cassette) > 1:
            print('Url is being called more than once, redirecting? %s',
                  [x.url for x in self.cassette.requests])

    def test_episode_search(self):
        results = self.provider.search(self.search_strings['episode'])

        self.assertTrue(self.cassette.requests)
        self.assertTrue(results)
        self.assertTrue(len(self.cassette))

        if len(self.cassette) > 1:
            print('Url is being called more than once, redirecting? %s',
                  [x.url for x in self.cassette.requests])


if __name__ == '__main__':
    print('=====> Testing %s', __file__)

    def override_log(msg, *args, **kwargs):
        _ = args, kwargs
        print(msg)

    sickbeard.logger.log = override_log

    test_suite = unittest.TestLoader().loadTestsFromTestCase(ThePirateBayParsingTests)
    unittest.TextTestRunner(verbosity=3).run(test_suite)
