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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=line-too-long

"""
Test sickrage.common
"""

from __future__ import print_function

import unittest
import os
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import sickbeard
from sickrage.helper.common import http_code_description, is_sync_file, is_torrent_or_nzb_file, pretty_file_size
from sickrage.helper.common import remove_extension, replace_extension, sanitize_filename, try_int


class CommonTests(unittest.TestCase):
    """
    Test common
    """

    def test_http_code_description(self):
        test_cases = {
            None: None,
            '': None,
            '300': None,
            0: None,
            123: None,
            12.3: None,
            -123: None,
            -12.3: None,
            300: 'Multiple Choices',
            451: '(Redirect, Unavailable For Legal Reasons)',
            497: 'HTTP to HTTPS',
            499: '(Client Closed Request, Token required)',
            600: None,
        }

        unicode_test_cases = {
            u'': None,
            u'300': None,
        }

        for test in test_cases, unicode_test_cases:
            for (http_code, result) in test.iteritems():
                self.assertEqual(http_code_description(http_code), result)

    def test_is_sync_file(self):
        """
        Test is sync file
        """
        sickbeard.SYNC_FILES = '!sync,lftp-pget-status,part'

        test_cases = {
            None: False,
            42: False,
            '': False,
            'filename': False,
            '.syncthingfilename': True,
            '.syncthing.filename': True,
            '.syncthing-filename': True,
            '.!sync': True,
            'file.!sync': True,
            'file.!sync.ext': False,
            '.lftp-pget-status': True,
            'file.lftp-pget-status': True,
            'file.lftp-pget-status.ext': False,
            '.part': True,
            'file.part': True,
            'file.part.ext': False,
        }

        unicode_test_cases = {
            u'': False,
            u'filename': False,
            u'.syncthingfilename': True,
            u'.syncthing.filename': True,
            u'.syncthing-filename': True,
            u'.!sync': True,
            u'file.!sync': True,
            u'file.!sync.ext': False,
            u'.lftp-pget-status': True,
            u'file.lftp-pget-status': True,
            u'file.lftp-pget-status.ext': False,
            u'.part': True,
            u'file.part': True,
            u'file.part.ext': False,
        }

        for tests in test_cases, unicode_test_cases:
            for (filename, result) in tests.iteritems():
                self.assertEqual(is_sync_file(filename), result)

    def test_is_torrent_or_nzb_file(self):
        """
        Test is torrent or nzb file
        """
        test_cases = {
            None: False,
            42: False,
            '': False,
            'filename': False,
            '.nzb': True,
            'file.nzb': True,
            'file.nzb.part': False,
            '.torrent': True,
            'file.torrent': True,
            'file.torrent.part': False,
        }

        unicode_test_cases = {
            u'': False,
            u'filename': False,
            u'.nzb': True,
            u'file.nzb': True,
            u'file.nzb.part': False,
            u'.torrent': True,
            u'file.torrent': True,
            u'file.torrent.part': False,
        }

        for tests in test_cases, unicode_test_cases:
            for (filename, result) in tests.iteritems():
                self.assertEqual(is_torrent_or_nzb_file(filename), result)

    def test_pretty_file_size(self):
        """
        Test pretty file size
        """
        test_cases = {
            None: '',
            '': '',
            '1024': '1.00 KB',
            '1024.5': '',
            -42.5: '-42.50 B',
            -42: '-42.00 B',
            0: '0.00 B',
            25: '25.00 B',
            25.5: '25.50 B',
            2 ** 10: '1.00 KB',
            50 * 2 ** 10 + 25: '50.02 KB',
            2 ** 20: '1.00 MB',
            100 * 2 ** 20 + 50 * 2 ** 10 + 25: '100.05 MB',
            2 ** 30: '1.00 GB',
            200 * 2 ** 30 + 100 * 2 ** 20 + 50 * 2 ** 10 + 25: '200.10 GB',
            2 ** 40: '1.00 TB',
            400 * 2 ** 40 + 200 * 2 ** 30 + 100 * 2 ** 20 + 50 * 2 ** 10 + 25: '400.20 TB',
            2 ** 50: '1.00 PB',
            800 * 2 ** 50 + 400 * 2 ** 40 + 200 * 2 ** 30 + 100 * 2 ** 20 + 50 * 2 ** 10 + 25: '800.39 PB',
            2 ** 60: 2 ** 60,
        }

        unicode_test_cases = {
            u'': '',
            u'1024': '1.00 KB',
            u'1024.5': '',
        }

        for tests in test_cases, unicode_test_cases:
            for (size, result) in tests.iteritems():
                self.assertEqual(pretty_file_size(size), result)

    def test_remove_extension(self):
        """
        Test remove extension
        """
        test_cases = {
            None: None,
            42: 42,
            '': '',
            '.': '.',
            'filename': 'filename',
            '.bashrc': '.bashrc',
            '.nzb': '.nzb',
            'file.nzb': 'file',
            'file.name.nzb': 'file.name',
            '.torrent': '.torrent',
            'file.torrent': 'file',
            'file.name.torrent': 'file.name',
            '.avi': '.avi',
            'file.avi': 'file',
            'file.name.avi': 'file.name',
        }

        unicode_test_cases = {
            u'': u'',
            u'.': u'.',
            u'filename': u'filename',
            u'.bashrc': u'.bashrc',
            u'.nzb': u'.nzb',
            u'file.nzb': u'file',
            u'file.name.nzb': u'file.name',
            u'.torrent': u'.torrent',
            u'file.torrent': u'file',
            u'file.name.torrent': u'file.name',
            u'.avi': u'.avi',
            u'file.avi': u'file',
            u'file.name.avi': u'file.name',
        }
        for tests in test_cases, unicode_test_cases:
            for (extension, result) in tests.iteritems():
                self.assertEqual(remove_extension(extension), result)

    def test_replace_extension(self):
        """
        Test replace extension
        """
        test_cases = {
            (None, None): None,
            (None, ''): None,
            (42, None): 42,
            (42, ''): 42,
            ('', None): '',
            ('', ''): '',
            ('.', None): '.',
            ('.', ''): '.',
            ('.', 'avi'): '.',
            ('filename', None): 'filename',
            ('filename', ''): 'filename',
            ('filename', 'avi'): 'filename',
            ('.bashrc', None): '.bashrc',
            ('.bashrc', ''): '.bashrc',
            ('.bashrc', 'avi'): '.bashrc',
            ('file.mkv', None): 'file.None',
            ('file.mkv', ''): 'file.',
            ('file.mkv', 'avi'): 'file.avi',
            ('file.name.mkv', None): 'file.name.None',
            ('file.name.mkv', ''): 'file.name.',
            ('file.name.mkv', 'avi'): 'file.name.avi',
        }

        unicode_test_cases = {
            (None, u''): None,
            (42, u''): 42,
            ('', u''): '',
            (u'', None): u'',
            (u'', ''): u'',
            (u'', u''): u'',
            ('.', u''): '.',
            ('.', u'avi'): '.',
            (u'.', None): u'.',
            (u'.', ''): u'.',
            (u'.', u''): u'.',
            (u'.', 'avi'): u'.',
            (u'.', u'avi'): u'.',
            ('filename', u''): 'filename',
            ('filename', u'avi'): 'filename',
            (u'filename', None): u'filename',
            (u'filename', ''): u'filename',
            (u'filename', u''): u'filename',
            (u'filename', 'avi'): u'filename',
            (u'filename', u'avi'): u'filename',
            ('.bashrc', u''): '.bashrc',
            ('.bashrc', u'avi'): '.bashrc',
            (u'.bashrc', None): u'.bashrc',
            (u'.bashrc', ''): u'.bashrc',
            (u'.bashrc', u''): u'.bashrc',
            (u'.bashrc', 'avi'): u'.bashrc',
            (u'.bashrc', u'avi'): u'.bashrc',
            ('file.mkv', u''): 'file.',
            ('file.mkv', u'avi'): 'file.avi',
            (u'file.mkv', None): u'file.None',
            (u'file.mkv', ''): u'file.',
            (u'file.mkv', u''): u'file.',
            (u'file.mkv', 'avi'): u'file.avi',
            (u'file.mkv', u'avi'): u'file.avi',
            ('file.name.mkv', u''): 'file.name.',
            ('file.name.mkv', u'avi'): 'file.name.avi',
            (u'file.name.mkv', None): u'file.name.None',
            (u'file.name.mkv', ''): u'file.name.',
            (u'file.name.mkv', u''): u'file.name.',
            (u'file.name.mkv', 'avi'): u'file.name.avi',
            (u'file.name.mkv', u'avi'): u'file.name.avi',
        }

        for tests in test_cases, unicode_test_cases:
            for ((filename, extension), result) in tests.iteritems():
                self.assertEqual(replace_extension(filename, extension), result)

    def test_sanitize_filename(self):
        """
        Test sanitize filename
        """
        test_cases = {
            None: '',
            42: '',
            '': '',
            'filename': 'filename',
            'fi\\le/na*me': 'fi-le-na-me',
            'fi:le"na<me': 'filename',
            'fi>le|na?me': 'filename',
            ' . file\u2122name. .': 'file-u2122name',  # pylint: disable=anomalous-unicode-escape-in-string
        }

        unicode_test_cases = {
            u'': u'',
            u'filename': u'filename',
            u'fi\\le/na*me': u'fi-le-na-me',
            u'fi:le"na<me': u'filename',
            u'fi>le|na?me': u'filename',
            u' . file\u2122name. .': u'filename',
        }

        for tests in test_cases, unicode_test_cases:
            for (filename, result) in tests.iteritems():
                self.assertEqual(sanitize_filename(filename), result)

    def test_try_int(self):
        """
        Test try int
        """
        test_cases = {
            None: 0,
            '': 0,
            '123': 123,
            '-123': -123,
            '12.3': 0,
            '-12.3': 0,
            0: 0,
            123: 123,
            -123: -123,
            12.3: 12,
            -12.3: -12,
        }

        unicode_test_cases = {
            u'': 0,
            u'123': 123,
            u'-123': -123,
            u'12.3': 0,
            u'-12.3': 0,
        }

        for test in test_cases, unicode_test_cases:
            for (candidate, result) in test.iteritems():
                self.assertEqual(try_int(candidate), result)

    def test_try_int_with_default(self):
        """
        Test try int
        """
        default_value = 42
        test_cases = {
            None: default_value,
            '': default_value,
            '123': 123,
            '-123': -123,
            '12.3': default_value,
            '-12.3': default_value,
            0: 0,
            123: 123,
            -123: -123,
            12.3: 12,
            -12.3: -12,
        }

        unicode_test_cases = {
            u'': default_value,
            u'123': 123,
            u'-123': -123,
            u'12.3': default_value,
            u'-12.3': default_value,
        }

        for test in test_cases, unicode_test_cases:
            for (candidate, result) in test.iteritems():
                self.assertEqual(try_int(candidate, default_value), result)


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(CommonTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
