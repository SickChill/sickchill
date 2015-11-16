#!/usr/bin/env python2.7
"""
Author: Dustyn Gibson <miigotu@gmail.com>
URL: http://github.com/SiCKRAGETV/SickRage

This file is part of SickRage.

SickRage is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SickRage is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SickRage.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import os.path

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from sickbeard.helpers import remove_non_release_groups

test_result = 'Show.Name.S01E01.HDTV.x264-RLSGROUP'
test_cases = {
    'removewords': [
        test_result,
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[cttv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP.RiPSaLoT',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[GloDLS]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[EtHD]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-20-40',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[NO-RAR] - [ www.torrentday.com ]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[rarbg]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[Seedbox]',
        '{ www.SceneTime.com } - Show.Name.S01E01.HDTV.x264-RLSGROUP',
        '].[www.tensiontorrent.com] - Show.Name.S01E01.HDTV.x264-RLSGROUP',
        '[ www.TorrentDay.com ] - Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[silv4]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[AndroidTwoU]',
        '[www.newpct1.com]Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-NZBGEEK',
        '.www.Cpasbien.pwShow.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP [1044]',
        '[ www.Cpasbien.pw ] Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP.[BT]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[vtv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP.[www.usabit.com]',
        '[www.Cpasbien.com] Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[ettv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[rartv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-Siklopentan',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-RP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[PublicHD]',
        '[www.Cpasbien.pe] Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[eztv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-[SpastikusTV]',
        '].[ www.tensiontorrent.com ] - Show.Name.S01E01.HDTV.x264-RLSGROUP',
        '[ www.Cpasbien.com ] Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP- { www.SceneTime.com }',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP- [ www.torrentday.com ]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP.Renc'
    ]
}

class HelpersTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(HelpersTests, self).__init__(*args, **kwargs)

def test_generator(test_strings):
    def _test(self):
        for test_string in test_strings:
            self.assertEqual(remove_non_release_groups(test_string), test_result)
    return _test

if __name__ == '__main__':
    print "=================="
    print "STARTING - Helpers TESTS"
    print "=================="
    print "######################################################################"
    for name, test_data in test_cases.items():
        test_name = 'test_%s' % name
        test = test_generator(test_data)
        setattr(HelpersTests, test_name, test)

    suite = unittest.TestLoader().loadTestsFromTestCase(HelpersTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
