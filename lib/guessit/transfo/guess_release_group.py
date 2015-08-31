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

from guessit.plugins.transformers import Transformer
from guessit.matcher import GuessFinder, build_guess
from guessit.containers import PropertiesContainer
from guessit.patterns import sep
from guessit.guess import Guess
from guessit.textutils import strip_brackets


class GuessReleaseGroup(Transformer):
    def __init__(self):
        Transformer.__init__(self, -190)

        self.container = PropertiesContainer(canonical_from_pattern=False)
        self._allowed_groupname_pattern = '[\w@#€£$&!\?]'
        self._forbidden_groupname_lambda = [lambda elt: elt in ['rip', 'by', 'for', 'par', 'pour', 'bonus'],
                                            lambda elt: self._is_number(elt)]
        # If the previous property in this list, the match will be considered as safe
        # and group name can contain a separator.
        self.previous_safe_properties = ['videoCodec', 'format', 'videoApi', 'audioCodec', 'audioProfile', 'videoProfile', 'audioChannels', 'screenSize', 'other']
        self.previous_safe_values = {'other': ['Complete']}
        self.next_safe_properties = ['extension', 'website']
        self.next_safe_values = {'format': ['Telesync']}
        self.next_unsafe_properties = list(self.previous_safe_properties)
        self.next_unsafe_properties.extend(['episodeNumber', 'season'])
        self.container.sep_replace_char = '-'
        self.container.canonical_from_pattern = False
        self.container.enhance = True
        self.container.register_property('releaseGroup', self._allowed_groupname_pattern + '+')
        self.container.register_property('releaseGroup', self._allowed_groupname_pattern + '+-' + self._allowed_groupname_pattern + '+')
        self.re_sep = re.compile('(' + sep + ')')

    def register_arguments(self, opts, naming_opts, output_opts, information_opts, webservice_opts, other_options):
        naming_opts.add_argument('-G', '--expected-group', action='append', dest='expected_group',
                               help='Expected release group (can be used multiple times)')

    def supported_properties(self):
        return self.container.get_supported_properties()

    @staticmethod
    def _is_number(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def validate_group_name(self, guess):
        val = guess['releaseGroup']
        if len(val) > 1:
            checked_val = ""
            forbidden = False
            for elt in self.re_sep.split(val): # separators are in the list because of capturing group
                if forbidden:
                    # Previous was forbidden, don't had separator
                    forbidden = False
                    continue
                for forbidden_lambda in self._forbidden_groupname_lambda:
                    forbidden = forbidden_lambda(elt.lower())
                    if forbidden:
                        if checked_val:
                            # Removing previous separator
                            checked_val = checked_val[0:len(checked_val) - 1]
                        break
                if not forbidden:
                    checked_val += elt

            val = checked_val
            if not val:
                return False
            if self.re_sep.match(val[-1]):
                val = val[:len(val)-1]
            if not val:
                return False
            if self.re_sep.match(val[0]):
                val = val[1:]
            if not val:
                return False
            guess['releaseGroup'] = val
            forbidden = False
            for forbidden_lambda in self._forbidden_groupname_lambda:
                forbidden = forbidden_lambda(val.lower())
                if forbidden:
                    break
            if not forbidden:
                return True
        return False

    @staticmethod
    def is_leaf_previous(leaf, node):
        if leaf.span[1] <= node.span[0]:
            for idx in range(leaf.span[1], node.span[0]):
                if leaf.root.value[idx] not in sep:
                    return False
            return True
        return False

    def validate_next_leaves(self, node):
        if 'series' in node.root.info or 'title' in node.root.info:
            # --expected-series or --expected-title is used.
            return True

        next_leaf = node.root.next_leaf(node)
        node_idx = node.node_last_idx
        while next_leaf and next_leaf.node_last_idx >= node_idx:
            node_idx = next_leaf.node_last_idx
            # Check next properties in the same group are not in unsafe properties list
            for next_unsafe_property in self.next_unsafe_properties:
                if next_unsafe_property in next_leaf.info:
                    return False
            next_leaf = next_leaf.root.next_leaf(next_leaf)

        # Make sure to avoid collision with 'series' or 'title' guessed later. Should be more precise.
        leaves = node.root.unidentified_leaves()
        return len(list(leaves)) > 1

    def validate_node(self, leaf, node, safe=False):
        if not self.is_leaf_previous(leaf, node):
            return False
        if not self.validate_next_leaves(node):
            return False
        if safe:
            for k, v in leaf.guess.items():
                if k in self.previous_safe_values and v not in self.previous_safe_values[k]:
                    return False
        return True

    def guess_release_group(self, string, node=None, options=None):
        if options and options.get('expected_group'):
            expected_container = PropertiesContainer(enhance=True, canonical_from_pattern=False)
            for expected_group in options.get('expected_group'):
                if expected_group.startswith('re:'):
                    expected_group = expected_group[3:]
                    expected_group = expected_group.replace(' ', '-')
                    expected_container.register_property('releaseGroup', expected_group, enhance=True)
                else:
                    expected_group = re.escape(expected_group)
                    expected_container.register_property('releaseGroup', expected_group, enhance=False)

            found = expected_container.find_properties(string, node, options, 'releaseGroup')
            guess = expected_container.as_guess(found, string, self.validate_group_name)
            if guess:
                return guess

        found = self.container.find_properties(string, node, options, 'releaseGroup')
        guess = self.container.as_guess(found, string, self.validate_group_name)
        validated_guess = None
        if guess:
            group_node = node.group_node()
            if group_node:
                for leaf in group_node.leaves_containing(self.previous_safe_properties):
                    if self.validate_node(leaf, node, True):
                        if leaf.root.value[leaf.span[1]] == '-':
                            guess.metadata().confidence = 1
                        else:
                            guess.metadata().confidence = 0.7
                        validated_guess = guess

            if not validated_guess:
                # If previous group last leaf is identified as a safe property,
                # consider the raw value as a releaseGroup
                previous_group_node = node.previous_group_node()
                if previous_group_node:
                    for leaf in previous_group_node.leaves_containing(self.previous_safe_properties):
                        if self.validate_node(leaf, node, False):
                            guess = Guess({'releaseGroup': node.value}, confidence=1, input=node.value, span=(0, len(node.value)))
                            if self.validate_group_name(guess):
                                node.guess = guess
                                validated_guess = guess

            if validated_guess:
                # If following group nodes have only one unidentified leaf, it belongs to the release group
                next_group_node = node

                while True:
                    next_group_node = next_group_node.next_group_node()
                    if next_group_node:
                        leaves = list(next_group_node.leaves())
                        if len(leaves) == 1 and not leaves[0].guess:
                            validated_guess['releaseGroup'] = validated_guess['releaseGroup'] + leaves[0].value
                            leaves[0].guess = validated_guess
                        else:
                            break
                    else:
                        break

            if not validated_guess and node.is_explicit() and node.node_last_idx == 0: # first node from group
                validated_guess = build_guess(node, 'releaseGroup', value=node.value[1:len(node.value)-1])
                validated_guess.metadata().confidence = 0.4
                validated_guess.metadata().span = 1, len(node.value)
                node.guess = validated_guess

        if validated_guess:
            # Strip brackets
            validated_guess['releaseGroup'] = strip_brackets(validated_guess['releaseGroup'])

        return validated_guess

    def process(self, mtree, options=None):
        GuessFinder(self.guess_release_group, None, self.log, options).process_nodes(mtree.unidentified_leaves())
