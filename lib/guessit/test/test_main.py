#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2014 Nicolas Wack <wackou@gmail.com>
#
# GuessIt is free software; you can redistribute it and/or modify it under
# the terms of the Lesser GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# GuessIt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function, unicode_literals

from guessit.test.guessittest import *
from guessit.fileutils import file_in_same_dir
from guessit import PY2
from guessit import __main__

if PY2:
    from StringIO import StringIO
else:
    from io import StringIO


class TestMain(TestGuessit):
    def setUp(self):
        self._stdout = sys.stdout
        string_out = StringIO()
        sys.stdout = string_out

    def tearDown(self):
        sys.stdout = self._stdout

    def test_list_properties(self):
        __main__.main(["-p"], False)
        __main__.main(["-V"], False)

    def test_list_transformers(self):
        __main__.main(["--transformers"], False)
        __main__.main(["-V", "--transformers"], False)

    def test_demo(self):
        __main__.main(["-d"], False)

    def test_filename(self):
        __main__.main(["A.Movie.2014.avi"], False)
        __main__.main(["A.Movie.2014.avi", "A.2nd.Movie.2014.avi"], False)
        __main__.main(["-y", "A.Movie.2014.avi"], False)
        __main__.main(["-a", "A.Movie.2014.avi"], False)
        __main__.main(["-v", "A.Movie.2014.avi"], False)
        __main__.main(["-t", "movie", "A.Movie.2014.avi"], False)
        __main__.main(["-t", "episode", "A.Serie.S02E06.avi"], False)
        __main__.main(["-i", "hash_mpc", file_in_same_dir(__file__, "1MB")], False)
        __main__.main(["-i", "hash_md5", file_in_same_dir(__file__, "1MB")], False)
