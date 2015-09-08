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

from functools import reduce

from guessit.plugins.transformers import Transformer
from guessit.textutils import find_first_level_groups
from guessit.patterns import group_delimiters


class SplitExplicitGroups(Transformer):
    def __init__(self):
        Transformer.__init__(self, 250)

    def process(self, mtree, options=None):
        """split each of those into explicit groups (separated by parentheses or square brackets)

        :return: return the string split into explicit groups, that is, those either
        between parenthese, square brackets or curly braces, and those separated
        by a dash."""
        for c in mtree.unidentified_leaves():
            groups = find_first_level_groups(c.value, group_delimiters[0])
            for delimiters in group_delimiters:
                flatten = lambda l, x: l + find_first_level_groups(x, delimiters)
                groups = reduce(flatten, groups, [])

            # do not do this at this moment, it is not strong enough and can break other
            # patterns, such as dates, etc...
            # groups = functools.reduce(lambda l, x: l + x.split('-'), groups, [])

            c.split_on_components(groups, category='explicit')

    def post_process(self, mtree, options=None):
        """
        Decrease confidence for properties found in explicit groups.

        :param mtree:
        :param options:
        :return:
        """
        if not options.get('name_only'):
            explicit_nodes = [node for node in mtree.nodes() if node.category == 'explicit' and node.is_explicit()]

            for explicit_node in explicit_nodes:
                self.alter_confidence(explicit_node, 0.5)

    def alter_confidence(self, node, factor):
        for guess in node.guesses:
            for k in guess.keys():
                confidence = guess.confidence(k)
                guess.set_confidence(k, confidence * factor)
