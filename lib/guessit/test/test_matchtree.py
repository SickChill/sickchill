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

from guessit.test.guessittest import *

from guessit.transfo.guess_release_group import GuessReleaseGroup
from guessit.transfo.guess_properties import GuessProperties
from guessit.matchtree import BaseMatchTree

keywords = yaml.load("""

? Xvid PROPER
: videoCodec: Xvid
  other: PROPER
  properCount: 1

? PROPER-Xvid
: videoCodec: Xvid
  other: PROPER
  properCount: 1

""")


def guess_info(string, options=None):
    mtree = MatchTree(string)
    GuessReleaseGroup().process(mtree, options)
    GuessProperties().process(mtree, options)
    return mtree.matched()


class TestMatchTree(TestGuessit):
    def test_base_tree(self):
        t = BaseMatchTree('One Two Three(Three) Four')
        t.partition((3, 7, 20))
        leaves = list(t.leaves())

        assert leaves[0].span == (0, 3)

        assert 'One' == leaves[0].value
        assert ' Two' == leaves[1].value
        assert ' Three(Three)' == leaves[2].value
        assert ' Four' == leaves[3].value

        leaves[2].partition((1, 6, 7, 12))
        three_leaves = list(leaves[2].leaves())

        assert 'Three' == three_leaves[1].value
        assert 'Three' == three_leaves[3].value

        leaves = list(t.leaves())

        assert len(leaves) == 8

        assert leaves[5] == three_leaves[3]

        assert t.previous_leaf(leaves[5]) == leaves[4]
        assert t.next_leaf(leaves[5]) == leaves[6]

        assert t.next_leaves(leaves[5]) == [leaves[6], leaves[7]]
        assert t.previous_leaves(leaves[5]) == [leaves[4], leaves[3], leaves[2], leaves[1], leaves[0]]

        assert t.next_leaf(leaves[7]) is None
        assert t.previous_leaf(leaves[0]) is None

        assert t.next_leaves(leaves[7]) == []
        assert t.previous_leaves(leaves[0]) == []

    def test_match(self):
        self.checkFields(keywords, guess_info)
