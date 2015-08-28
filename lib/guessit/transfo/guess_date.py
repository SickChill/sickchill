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
from guessit.containers import DefaultValidator

from guessit.plugins.transformers import Transformer
from guessit.matcher import GuessFinder
from guessit.date import search_date


class GuessDate(Transformer):
    def __init__(self):
        Transformer.__init__(self, 50)

    def register_arguments(self, opts, naming_opts, output_opts, information_opts, webservice_opts, other_options):
        naming_opts.add_argument('-Y', '--date-year-first', action='store_true', dest='date_year_first', default=None,
                                 help='If short date is found, consider the first digits as the year.')
        naming_opts.add_argument('-D', '--date-day-first', action='store_true', dest='date_day_first', default=None,
                                 help='If short date is found, consider the second digits as the day.')

    def supported_properties(self):
        return ['date']

    @staticmethod
    def guess_date(string, node=None, options=None):
        date, span = search_date(string, options.get('date_year_first') if options else False, options.get('date_day_first') if options else False)
        if date and span and DefaultValidator.validate_string(string, span): # ensure we have a separator before and after date
            return {'date': date}, span
        return None, None

    def process(self, mtree, options=None):
        GuessFinder(self.guess_date, 1.0, self.log, options).process_nodes(mtree.unidentified_leaves())
