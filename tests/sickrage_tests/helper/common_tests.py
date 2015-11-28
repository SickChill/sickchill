# This file is part of SickRage.
#
# URL: https://sickrage.github.io
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

from unittest import TestCase, TestLoader, TextTestRunner

import os
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import sickbeard

from sickrage.helper.common import is_sync_file, is_torrent_or_nzb_file, pretty_file_size, remove_extension
from sickrage.helper.common import replace_extension, sanitize_filename


class CommonTests(TestCase):
    def test_is_sync_file(self):
        sickbeard.SYNC_FILES = '!sync,lftp-pget-status,part'

        tests = {
            None: False,
            42: False,
            '': False,
            u'': False,
            'filename': False,
            u'filename': False,
            '.syncthingfilename': True,
            u'.syncthingfilename': True,
            '.syncthing.filename': True,
            u'.syncthing.filename': True,
            '.syncthing-filename': True,
            u'.syncthing-filename': True,
            '.!sync': True,
            u'.!sync': True,
            'file.!sync': True,
            u'file.!sync': True,
            'file.!sync.ext': False,
            u'file.!sync.ext': False,
            '.lftp-pget-status': True,
            u'.lftp-pget-status': True,
            'file.lftp-pget-status': True,
            u'file.lftp-pget-status': True,
            'file.lftp-pget-status.ext': False,
            u'file.lftp-pget-status.ext': False,
            '.part': True,
            u'.part': True,
            'file.part': True,
            u'file.part': True,
            'file.part.ext': False,
            u'file.part.ext': False,
        }

        for (filename, result) in tests.iteritems():
            self.assertEqual(is_sync_file(filename), result)

    def test_is_torrent_or_nzb_file(self):
        tests = {
            None: False,
            42: False,
            '': False,
            u'': False,
            'filename': False,
            u'filename': False,
            '.nzb': True,
            u'.nzb': True,
            'file.nzb': True,
            u'file.nzb': True,
            'file.nzb.part': False,
            u'file.nzb.part': False,
            '.torrent': True,
            u'.torrent': True,
            'file.torrent': True,
            u'file.torrent': True,
            'file.torrent.part': False,
            u'file.torrent.part': False,
        }

        for (filename, result) in tests.iteritems():
            self.assertEqual(is_torrent_or_nzb_file(filename), result)

    def test_pretty_file_size(self):
        tests = {
            None: '',
            '': '',
            u'': '',
            '1024': '1.00 KB',
            u'1024': '1.00 KB',
            '1024.5': '',
            u'1024.5': '',
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

        for (size, result) in tests.iteritems():
            self.assertEqual(pretty_file_size(size), result)

    def test_remove_extension(self):
        tests = {
            None: None,
            42: 42,
            '': '',
            u'': u'',
            '.': '.',
            u'.': u'.',
            'filename': 'filename',
            u'filename': u'filename',
            '.bashrc': '.bashrc',
            u'.bashrc': u'.bashrc',
            '.nzb': '.nzb',
            u'.nzb': u'.nzb',
            'file.nzb': 'file',
            u'file.nzb': u'file',
            'file.name.nzb': 'file.name',
            u'file.name.nzb': u'file.name',
            '.torrent': '.torrent',
            u'.torrent': u'.torrent',
            'file.torrent': 'file',
            u'file.torrent': u'file',
            'file.name.torrent': 'file.name',
            u'file.name.torrent': u'file.name',
            '.avi': '.avi',
            u'.avi': u'.avi',
            'file.avi': 'file',
            u'file.avi': u'file',
            'file.name.avi': 'file.name',
            u'file.name.avi': u'file.name',
        }

        for (extension, result) in tests.iteritems():
            self.assertEqual(remove_extension(extension), result)

    def test_replace_extension(self):
        tests = {
            (None, None): None,
            (None, ''): None,
            (None, u''): None,
            (42, None): 42,
            (42, ''): 42,
            (42, u''): 42,
            ('', None): '',
            ('', ''): '',
            ('', u''): '',
            (u'', None): u'',
            (u'', ''): u'',
            (u'', u''): u'',
            ('.', None): '.',
            ('.', ''): '.',
            ('.', u''): '.',
            ('.', 'avi'): '.',
            ('.', u'avi'): '.',
            (u'.', None): u'.',
            (u'.', ''): u'.',
            (u'.', u''): u'.',
            (u'.', 'avi'): u'.',
            (u'.', u'avi'): u'.',
            ('filename', None): 'filename',
            ('filename', ''): 'filename',
            ('filename', u''): 'filename',
            ('filename', 'avi'): 'filename',
            ('filename', u'avi'): 'filename',
            (u'filename', None): u'filename',
            (u'filename', ''): u'filename',
            (u'filename', u''): u'filename',
            (u'filename', 'avi'): u'filename',
            (u'filename', u'avi'): u'filename',
            ('.bashrc', None): '.bashrc',
            ('.bashrc', ''): '.bashrc',
            ('.bashrc', u''): '.bashrc',
            ('.bashrc', 'avi'): '.bashrc',
            ('.bashrc', u'avi'): '.bashrc',
            (u'.bashrc', None): u'.bashrc',
            (u'.bashrc', ''): u'.bashrc',
            (u'.bashrc', u''): u'.bashrc',
            (u'.bashrc', 'avi'): u'.bashrc',
            (u'.bashrc', u'avi'): u'.bashrc',
            ('file.mkv', None): 'file.None',
            ('file.mkv', ''): 'file.',
            ('file.mkv', u''): 'file.',
            ('file.mkv', 'avi'): 'file.avi',
            ('file.mkv', u'avi'): 'file.avi',
            (u'file.mkv', None): u'file.None',
            (u'file.mkv', ''): u'file.',
            (u'file.mkv', u''): u'file.',
            (u'file.mkv', 'avi'): u'file.avi',
            (u'file.mkv', u'avi'): u'file.avi',
            ('file.name.mkv', None): 'file.name.None',
            ('file.name.mkv', ''): 'file.name.',
            ('file.name.mkv', u''): 'file.name.',
            ('file.name.mkv', 'avi'): 'file.name.avi',
            ('file.name.mkv', u'avi'): 'file.name.avi',
            (u'file.name.mkv', None): u'file.name.None',
            (u'file.name.mkv', ''): u'file.name.',
            (u'file.name.mkv', u''): u'file.name.',
            (u'file.name.mkv', 'avi'): u'file.name.avi',
            (u'file.name.mkv', u'avi'): u'file.name.avi',
        }

        for ((filename, extension), result) in tests.iteritems():
            self.assertEqual(replace_extension(filename, extension), result)

    def test_sanitize_filename(self):
        tests = {
            None: '',
            42: '',
            '': '',
            u'': u'',
            'filename': 'filename',
            u'filename': u'filename',
            'fi\\le/na*me': 'fi-le-na-me',
            u'fi\\le/na*me': u'fi-le-na-me',
            'fi:le"na<me': 'filename',
            u'fi:le"na<me': u'filename',
            'fi>le|na?me': 'filename',
            u'fi>le|na?me': u'filename',
            ' . file\u2122name. .': 'file-u2122name',
            u' . file\u2122name. .': u'filename',
        }

        for (filename, result) in tests.iteritems():
            self.assertEqual(sanitize_filename(filename), result)


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    suite = TestLoader().loadTestsFromTestCase(CommonTests)
    TextTestRunner(verbosity=2).run(suite)
