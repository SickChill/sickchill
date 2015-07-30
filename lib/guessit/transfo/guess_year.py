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

from guessit.plugins.transformers import Transformer
from guessit.matcher import GuessFinder
from guessit.date import search_year, valid_year


class GuessYear(Transformer):
    def __init__(self):
        Transformer.__init__(self, -160)

    def supported_properties(self):
        return ['year']

    @staticmethod
    def guess_year(string, node=None, options=None):
        year, span = search_year(string)
        if year:
            return {'year': year}, span
        else:
            return None, None

    def second_pass_options(self, mtree, options=None):
        year_nodes = list(mtree.leaves_containing('year'))
        # if we found a year, let's try by ignoring all instances of that year
        # as a candidate, let's take the one that appears last in the filename
        if year_nodes:
            year_candidate = year_nodes[-1].guess['year']
            year_nodes = [year for year in year_nodes if year.guess['year'] != year_candidate]
            if year_nodes:
                return {'skip_nodes': year_nodes}
        return None

    def process(self, mtree, options=None):
        GuessFinder(self.guess_year, 1.0, self.log, options).process_nodes(mtree.unidentified_leaves())

        # if we found a season number that is a valid year, it is usually safe to assume
        # we can also set the year property to that value
        for n in mtree.leaves_containing('season'):
            g = n.guess
            season = g['season']
            if valid_year(season):
                g['year'] = season
