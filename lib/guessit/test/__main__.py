#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
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
from guessit.test import (test_api, test_autodetect, test_autodetect_all, test_doctests,
                          test_episode, test_hashes, test_language, test_main,
                          test_matchtree, test_movie, test_quality, test_utils)
from unittest import TextTestRunner


import logging

def main():
    for suite in [test_api.suite, test_autodetect.suite,
                  test_autodetect_all.suite, test_doctests.suite,
                  test_episode.suite, test_hashes.suite, test_language.suite,
                  test_main.suite, test_matchtree.suite, test_movie.suite,
                  test_quality.suite, test_utils.suite]:
        TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    main()
