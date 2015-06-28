#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Rémi Alvergnat <toilal.dev@gmail.com>
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

from pkg_resources import resource_stream  # @UnresolvedImport

from guessit.patterns import build_or_pattern
from guessit.containers import PropertiesContainer
from guessit.plugins.transformers import Transformer
from guessit.matcher import GuessFinder


TLDS = [l.strip().decode('utf-8')
        for l in resource_stream('guessit', 'tlds-alpha-by-domain.txt').readlines()
        if b'--' not in l][1:]


class GuessWebsite(Transformer):
    def __init__(self):
        Transformer.__init__(self, 45)

        self.container = PropertiesContainer(enhance=False, canonical_from_pattern=False)

        tlds_pattern = build_or_pattern(TLDS)  # All registered domain extension
        safe_tlds_pattern = build_or_pattern(['com', 'org', 'net'])  # For sure a website extension
        safe_subdomains_pattern = build_or_pattern(['www'])  # For sure a website subdomain
        safe_prefix_tlds_pattern = build_or_pattern(['co', 'com', 'org', 'net'])  # Those words before a tlds are sure

        self.container.register_property('website', '(?:' + safe_subdomains_pattern + '\.)+' + r'(?:[a-z-]+\.)+' + r'(?:' + tlds_pattern + r')+')
        self.container.register_property('website', '(?:' + safe_subdomains_pattern + '\.)*' + r'[a-z-]+\.' + r'(?:' + safe_tlds_pattern + r')+')
        self.container.register_property('website', '(?:' + safe_subdomains_pattern + '\.)*' + r'[a-z-]+\.' + r'(?:' + safe_prefix_tlds_pattern + r'\.)+' + r'(?:' + tlds_pattern + r')+')

    def supported_properties(self):
        return self.container.get_supported_properties()

    def guess_website(self, string, node=None, options=None):
        found = self.container.find_properties(string, node, options, 'website')
        return self.container.as_guess(found, string)

    def process(self, mtree, options=None):
        GuessFinder(self.guess_website, 1.0, self.log, options).process_nodes(mtree.unidentified_leaves())
