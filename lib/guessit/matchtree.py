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

import copy
import logging

import guessit  # @UnusedImport needed for doctests
from guessit import UnicodeMixin, base_text_type
from guessit.textutils import clean_default, str_fill
from guessit.patterns import group_delimiters
from guessit.guess import smart_merge, Guess

log = logging.getLogger(__name__)


class BaseMatchTree(UnicodeMixin):
    """A BaseMatchTree is a tree covering the filename, where each
    node represents a substring in the filename and can have a ``Guess``
    associated with it that contains the information that has been guessed
    in this node. Nodes can be further split into subnodes until a proper
    split has been found.

    Each node has the following attributes:
     - string = the original string of which this node represents a region
     - span = a pair of (begin, end) indices delimiting the substring
     - parent = parent node
     - children = list of children nodes
     - guess = Guess()

    BaseMatchTrees are displayed in the following way:

        >>> path = 'Movies/Dark City (1998)/Dark.City.(1998).DC.BDRip.720p.DTS.X264-CHD.mkv'
        >>> print(guessit.IterativeMatcher(path).match_tree)
        000000 1111111111111111 2222222222222222222222222222222222222222222 333
        000000 0000000000111111 0000000000111111222222222222222222222222222 000
                         011112           011112000011111222222222222222222 000
                                                         011112222222222222
                                                              0000011112222
                                                              01112    0111
        Movies/__________(____)/Dark.City.(____).DC._____.____.___.____-___.___
               tttttttttt yyyy             yyyy     fffff ssss aaa vvvv rrr ccc
        Movies/Dark City (1998)/Dark.City.(1998).DC.BDRip.720p.DTS.X264-CHD.mkv

    The last line contains the filename, which you can use a reference.
    The previous line contains the type of property that has been found.
    The line before that contains the filename, where all the found groups
    have been blanked. Basically, what is left on this line are the leftover
    groups which could not be identified.

    The lines before that indicate the indices of the groups in the tree.

    For instance, the part of the filename 'BDRip' is the leaf with index
    ``(2, 2, 1)`` (read from top to bottom), and its meaning is 'format'
    (as shown by the ``f``'s on the last-but-one line).
    """

    def __init__(self, string='', span=None, parent=None, clean_function=None, category=None):
        self.string = string
        self.span = span or (0, len(string))
        self.parent = parent
        self.children = []
        self.guess = Guess()
        self._clean_value = None
        self._clean_function = clean_function or clean_default
        self.category = category

    @property
    def value(self):
        """Return the substring that this node matches."""
        return self.string[self.span[0]:self.span[1]]

    @property
    def clean_value(self):
        """Return a cleaned value of the matched substring, with better
        presentation formatting (punctuation marks removed, duplicate
        spaces, ...)"""
        if self._clean_value is None:
            self._clean_value = self.clean_string(self.value)
        return self._clean_value

    def clean_string(self, string):
        return self._clean_function(string)

    @property
    def offset(self):
        return self.span[0]

    @property
    def info(self):
        """Return a dict containing all the info guessed by this node,
        subnodes included."""
        result = dict(self.guess)

        for c in self.children:
            result.update(c.info)

        return result

    @property
    def raw(self):
        result = {}
        for guess in self.guesses:
            for k in guess.keys():
                result[k] = guess.raw(k)
        return result

    @property
    def guesses(self):
        """
        List all guesses, including children ones.

        :return: list of guesses objects
        """

        result = []

        if self.guess:
            result.append(self.guess)

        for c in self.children:
            result.extend(c.guesses)

        return result

    @property
    def root(self):
        """Return the root node of the tree."""
        if not self.parent:
            return self

        return self.parent.root

    @property
    def ancestors(self):
        """
        Retrieve all ancestors, from this node to root node.

        :return: a list of MatchTree objects
        """
        ret = [self]

        if not self.parent:
            return ret

        parent_ancestors = self.parent.ancestors
        ret.extend(parent_ancestors)

        return ret

    @property
    def depth(self):
        """Return the depth of this node."""
        if self.is_leaf():
            return 0

        return 1 + max(c.depth for c in self.children)

    def is_leaf(self):
        """Return whether this node is a leaf or not."""
        return self.children == []

    def add_child(self, span, category=None):
        """Add a new child node to this node with the given span.

        :param span: span of the new MatchTree
        :param category: category of the new MatchTree
        :return: A new MatchTree instance having self as a parent
        """
        child = MatchTree(self.string, span=span, parent=self, clean_function=self._clean_function, category=category)
        self.children.append(child)
        return child

    def get_partition_spans(self, indices):
        """Return the list of absolute spans for the regions of the original
        string defined by splitting this node at the given indices (relative
        to this node)

        :param indices: indices of the partition spans
        :return: a list of tuple of the spans
        """
        indices = sorted(indices)
        if indices[-1] > len(self.value):
            log.error('Filename: {}'.format(self.string))
            log.error('Invalid call to get_partitions_spans, indices are too high: {}, len({}) == {:d}'
                      .format(indices, self.value, len(self.value)))
        if indices[0] != 0:
            indices.insert(0, 0)
        if indices[-1] != len(self.value):
            indices.append(len(self.value))

        spans = []
        for start, end in zip(indices[:-1], indices[1:]):
            spans.append((self.offset + start,
                          self.offset + end))

        return spans

    def partition(self, indices, category=None):
        """Partition this node by splitting it at the given indices,
        relative to this node.

        :param indices: indices of the partition spans
        :param category: category of the new MatchTree
        :return: a list of created MatchTree instances
        """
        created = []
        for partition_span in self.get_partition_spans(indices):
            created.append(self.add_child(span=partition_span, category=category))
        return created

    def split_on_components(self, components, category=None):
        offset = 0
        created = []
        for c in components:
            start = self.value.find(c, offset)
            end = start + len(c)
            created.append(self.add_child(span=(self.offset + start,
                                       self.offset + end), category=category))
            offset = end
        return created

    def nodes_at_depth(self, depth):
        """Return all the nodes at a given depth in the tree"""
        if depth == 0:
            yield self

        for child in self.children:
            for node in child.nodes_at_depth(depth - 1):
                yield node

    @property
    def node_idx(self):
        """Return this node's index in the tree, as a tuple.
        If this node is the root of the tree, then return ()."""
        if self.parent is None:
            return ()
        return self.parent.node_idx + (self.node_last_idx,)

    @property
    def node_last_idx(self):
        if self.parent is None:
            return None
        return self.parent.children.index(self)

    def node_at(self, idx):
        """Return the node at the given index in the subtree rooted at
        this node."""
        if not idx:
            return self

        try:
            return self.children[idx[0]].node_at(idx[1:])
        except IndexError:
            raise ValueError('Non-existent node index: %s' % (idx,))

    def nodes(self):
        """Return a generator of all nodes and subnodes in this tree."""
        yield self
        for child in self.children:
            for node in child.nodes():
                yield node

    def leaves(self):
        """Return a generator over all the nodes that are leaves."""
        if self.is_leaf():
            yield self
        else:
            for child in self.children:
                for leaf in child.leaves():
                    yield leaf

    def group_node(self):
        return self._other_group_node(0)

    def previous_group_node(self):
        return self._other_group_node(-1)

    def next_group_node(self):
        return self._other_group_node(+1)

    def _other_group_node(self, offset):
        if len(self.node_idx) > 1:
            group_idx = self.node_idx[:2]
            if group_idx[1] + offset >= 0:
                other_group_idx = (group_idx[0], group_idx[1] + offset)
                try:
                    other_group_node = self.root.node_at(other_group_idx)
                    return other_group_node
                except ValueError:
                    pass
        return None

    def previous_leaf(self, leaf):
        """Return previous leaf for this node"""
        return self._other_leaf(leaf, -1)

    def next_leaf(self, leaf):
        """Return next leaf for this node"""
        return self._other_leaf(leaf, +1)

    def _other_leaf(self, leaf, offset):
        leaves = list(self.leaves())
        index = leaves.index(leaf) + offset
        if 0 < index < len(leaves):
            return leaves[index]
        return None

    def previous_leaves(self, leaf):
        """Return previous leaves for this node"""
        leaves = list(self.leaves())
        index = leaves.index(leaf)
        if 0 < index < len(leaves):
            previous_leaves = leaves[:index]
            previous_leaves.reverse()
            return previous_leaves
        return []

    def next_leaves(self, leaf):
        """Return next leaves for this node"""
        leaves = list(self.leaves())
        index = leaves.index(leaf)
        if 0 < index < len(leaves):
            return leaves[index + 1:len(leaves)]
        return []

    def to_string(self):
        """Return a readable string representation of this tree.

        The result is a multi-line string, where the lines are:
         - line 1 -> N-2: each line contains the nodes at the given depth in the tree
         - line N-2: original string where all the found groups have been blanked
         - line N-1: type of property that has been found
         - line N: the original string, which you can use a reference.
        """
        empty_line = ' ' * len(self.string)

        def to_hex(x):
            if isinstance(x, int):
                return str(x) if x < 10 else chr(55 + x)
            return x

        def meaning(result):
            mmap = {'episodeNumber': 'E',
                    'season': 'S',
                    'extension': 'e',
                    'format': 'f',
                    'language': 'l',
                    'country': 'C',
                    'videoCodec': 'v',
                    'videoProfile': 'v',
                    'audioCodec': 'a',
                    'audioProfile': 'a',
                    'audioChannels': 'a',
                    'website': 'w',
                    'container': 'c',
                    'series': 'T',
                    'title': 't',
                    'date': 'd',
                    'year': 'y',
                    'releaseGroup': 'r',
                    'screenSize': 's',
                    'other': 'o'
                    }

            if result is None:
                return ' '

            for prop, l in mmap.items():
                if prop in result:
                    return l

            return 'x'

        lines = [empty_line] * (self.depth + 2)  # +2: remaining, meaning
        lines[-2] = self.string

        for node in self.nodes():
            if node == self:
                continue

            idx = node.node_idx
            depth = len(idx) - 1
            if idx:
                lines[depth] = str_fill(lines[depth], node.span,
                                        to_hex(idx[-1]))
            if node.guess:
                lines[-2] = str_fill(lines[-2], node.span, '_')
                lines[-1] = str_fill(lines[-1], node.span, meaning(node.guess))

        lines.append(self.string)

        return '\n'.join(l.rstrip() for l in lines)

    def __unicode__(self):
        return self.to_string()

    def __repr__(self):
        return '<MatchTree: root=%s>' % self.value


class MatchTree(BaseMatchTree):
    """The MatchTree contains a few "utility" methods which are not necessary
    for the BaseMatchTree, but add a lot of convenience for writing
    higher-level rules.
    """

    def unidentified_leaves(self,
                            valid=lambda leaf: len(leaf.clean_value) > 0):
        """Return a generator of leaves that are not empty."""
        for leaf in self.leaves():
            if not leaf.guess and valid(leaf):
                yield leaf

    def leaves_containing(self, property_name):
        """Return a generator of leaves that guessed the given property."""
        if isinstance(property_name, base_text_type):
            property_name = [property_name]

        for leaf in self.leaves():
            for prop in property_name:
                if prop in leaf.guess:
                    yield leaf
                    break

    def first_leaf_containing(self, property_name):
        """Return the first leaf containing the given property."""
        try:
            return next(self.leaves_containing(property_name))
        except StopIteration:
            return None

    def previous_unidentified_leaves(self, node):
        """Return a generator of non-empty leaves that are before the given
        node (in the string)."""
        node_idx = node.node_idx
        for leaf in self.unidentified_leaves():
            if leaf.node_idx < node_idx:
                yield leaf

    def previous_leaves_containing(self, node, property_name):
        """Return a generator of leaves containing the given property that are
        before the given node (in the string)."""
        node_idx = node.node_idx
        for leaf in self.leaves_containing(property_name):
            if leaf.node_idx < node_idx:
                yield leaf

    def is_explicit(self):
        """Return whether the group was explicitly enclosed by
        parentheses/square brackets/etc."""
        return (self.value[0] + self.value[-1]) in group_delimiters

    def matched(self):
        """Return a single guess that contains all the info found in the
        nodes of this tree, trying to merge properties as good as possible.
        """
        if not getattr(self, '_matched_result', None):
            # we need to make a copy here, as the merge functions work in place and
            # calling them on the match tree would modify it
            parts = [copy.copy(node.guess) for node in self.nodes() if node.guess]

            result = smart_merge(parts)

            log.debug('Final result: ' + result.nice_string())
            self._matched_result = result

        for leaf in self.unidentified_leaves():
            if 'unidentified' not in self._matched_result:
                self._matched_result['unidentified'] = []
            self._matched_result['unidentified'].append(leaf.clean_value)

        return self._matched_result
