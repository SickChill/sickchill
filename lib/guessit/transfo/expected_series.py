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
import re

from guessit.containers import PropertiesContainer
from guessit.matcher import GuessFinder
from guessit.plugins.transformers import Transformer


class ExpectedSeries(Transformer):
    def __init__(self):
        Transformer.__init__(self, 230)

    def register_arguments(self, opts, naming_opts, output_opts, information_opts, webservice_opts, other_options):
        naming_opts.add_argument('-S', '--expected-series', action='append', dest='expected_series',
                                 help='Expected series to parse (can be used multiple times)')

    def should_process(self, mtree, options=None):
        return options and options.get('expected_series')

    @staticmethod
    def expected_series(string, node=None, options=None):
        container = PropertiesContainer(enhance=True, canonical_from_pattern=False)

        for expected_serie in options.get('expected_series'):
            if expected_serie.startswith('re:'):
                expected_serie = expected_serie[3:]
                expected_serie = expected_serie.replace(' ', '-')
                container.register_property('series', expected_serie, enhance=True)
            else:
                expected_serie = re.escape(expected_serie)
                container.register_property('series', expected_serie, enhance=False)

        found = container.find_properties(string, node, options)
        return container.as_guess(found, string)

    def supported_properties(self):
        return ['series']

    def process(self, mtree, options=None):
        GuessFinder(self.expected_series, None, self.log, options).process_nodes(mtree.unidentified_leaves())
