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

from os.path import splitext

from guessit.plugins.transformers import Transformer
from guessit import fileutils


class SplitPathComponents(Transformer):
    def __init__(self):
        Transformer.__init__(self, 255)

    def process(self, mtree, options=None):
        """first split our path into dirs + basename + ext

        :return: the filename split into [ dir*, basename, ext ]
        """
        if not options.get('name_only'):
            components = fileutils.split_path(mtree.value)
            basename = components.pop(-1)
            components += list(splitext(basename))
            components[-1] = components[-1][1:]  # remove the '.' from the extension

            mtree.split_on_components(components, category='path')
        else:
            mtree.split_on_components([mtree.value, ''], category='path')

    def post_process(self, mtree, options=None):
        """
        Decrease confidence for properties found in directories, filename should always have priority.

        :param mtree:
        :param options:
        :return:
        """
        if not options.get('name_only'):
            path_nodes = [node for node in mtree.nodes() if node.category == 'path']

            for path_node in path_nodes[:-2]:
                self.alter_confidence(path_node, 0.3)

            try:
                last_directory_node = path_nodes[-2]
                self.alter_confidence(last_directory_node, 0.6)
            except IndexError:
                pass

    def alter_confidence(self, node, factor):
        for guess in node.guesses:
            for k in guess.keys():
                confidence = guess.confidence(k)
                guess.set_confidence(k, confidence * factor)
