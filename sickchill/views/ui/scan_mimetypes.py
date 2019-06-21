# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import logging
import mimetypes
import os
from argparse import ArgumentParser


class FindMimeTypes(object):
    def __init__(self):

        self.parser = ArgumentParser()
        self.parser.add_argument('--path', '-p', default='', action='store', required=True, help='Path to scan recursively')
        self.parser.add_argument('--list', '-l', default=False, action='store_true', help='List found mimes')
        self.parser.add_argument('--show-errors', '-e', default=False, action='store_true', help='Display parsing errors')
        self.parser.add_argument('--show', '-s', default=False, action='store_true', help='Display files that are being parsed')
        self.parser.add_argument('--add', '-a', default=False, action='store_true', help='Add parsed mimes to the system')
        self.parser.parse_args(namespace=self)

        self.errors = dict()

        if not (os.path.exists(self.path) and os.path.isdir(self.path)):
            print('Path must be an existing directory that is accessible, please try again')
            exit(1)

        if self.list:
            self.get_mimetypes
        if self.add:
            self.mime_adder
        if self.show:
            for found in self.list_files:
                print(found)
        if not (self.list or self.add or self.show):
            self.get_mimetypes
        if self.show_errors:
            if not (self.list or self.add):
                for _ in self.mime_code_generator:
                    continue
            for error in self.errors:
                print(error)

    @property
    def list_files(self):
        found_list = set()
        for path, directories, files in os.walk(self.path):
            for found in files:
                full_found = os.path.join(path, found)
                if full_found not in found_list:
                    yield full_found

    @property
    def mime_extractor(self):
        mimes = set()
        for found in self.list_files:
            try:
                extension = os.path.splitext(found)[1]
                mime = mimetypes.guess_type(found)[0]
                if not mime:
                    if extension:
                        # Just store the last one of each type
                        self.errors[extension] = found
                    continue

            except IndexError:
                continue

            if mime + extension not in mimes:
                mimes.add(mime + extension)
                yield mime, extension

    @property
    def mime_code_generator(self):
        mimes = set()
        for mime, extension in self.mime_extractor:
            code = 'mimetypes.add_type("{}", "{}")'.format(mime, extension)
            if code not in mimes:
                mimes.add(code)
                yield code

    @property
    def mime_adder(self):
        for mime, extension in self.mime_extractor:
            mimetypes.add_type(mime, extension)

        print('Could not determine mimetype for these types: {}'.format(self.errors.keys()))
        return

    @property
    def get_mimetypes(self):
        mt = set()
        for m in self.mime_code_generator:
            mt.add(m)

        print('\n'.join(mt))
        print('\n')
        print('Could not determine mimetype for these types: {}'.format(self.errors.keys()))
        return


if  __name__ =='__main__':
    finder = FindMimeTypes()
