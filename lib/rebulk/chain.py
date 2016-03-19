#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chain patterns and handle repetiting capture group
"""
# pylint: disable=super-init-not-called
import six

from .loose import call, set_defaults
from .match import Match
from .pattern import Pattern, filter_match_kwargs
from .remodule import re


class _InvalidChainException(Exception):
    """
    Internal exception raised when a chain is not valid
    """
    pass


class Chain(Pattern):
    """
    Definition of a pattern chain to search for.
    """

    def __init__(self, rebulk, **kwargs):
        call(super(Chain, self).__init__, **kwargs)
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)
        self._defaults = {}
        self._regex_defaults = {}
        self._string_defaults = {}
        self._functional_defaults = {}
        self.rebulk = rebulk
        self.parts = []

    def defaults(self, **kwargs):
        """
        Define default keyword arguments for all patterns
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        self._defaults = kwargs
        return self

    def regex_defaults(self, **kwargs):
        """
        Define default keyword arguments for functional patterns.
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        self._regex_defaults = kwargs
        return self

    def string_defaults(self, **kwargs):
        """
        Define default keyword arguments for string patterns.
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        self._string_defaults = kwargs
        return self

    def functional_defaults(self, **kwargs):
        """
        Define default keyword arguments for functional patterns.
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        self._functional_defaults = kwargs
        return self

    def chain(self):
        """
        Add patterns chain, using configuration from this chain

        :return:
        :rtype:
        """
        # pylint: disable=protected-access
        chain = self.rebulk.chain(**self._kwargs)
        chain._defaults = dict(self._defaults)
        chain._regex_defaults = dict(self._regex_defaults)
        chain._functional_defaults = dict(self._functional_defaults)
        chain._string_defaults = dict(self._string_defaults)
        return chain

    def regex(self, *pattern, **kwargs):
        """
        Add re pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(self._kwargs, kwargs)
        set_defaults(self._regex_defaults, kwargs)
        set_defaults(self._defaults, kwargs)
        pattern = self.rebulk.build_re(*pattern, **kwargs)
        part = ChainPart(self, pattern)
        self.parts.append(part)
        return part

    def functional(self, *pattern, **kwargs):
        """
        Add functional pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(self._kwargs, kwargs)
        set_defaults(self._functional_defaults, kwargs)
        set_defaults(self._defaults, kwargs)
        pattern = self.rebulk.build_functional(*pattern, **kwargs)
        part = ChainPart(self, pattern)
        self.parts.append(part)
        return part

    def string(self, *pattern, **kwargs):
        """
        Add string pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(self._kwargs, kwargs)
        set_defaults(self._functional_defaults, kwargs)
        set_defaults(self._defaults, kwargs)
        pattern = self.rebulk.build_string(*pattern, **kwargs)
        part = ChainPart(self, pattern)
        self.parts.append(part)
        return part

    def close(self):
        """
        Close chain builder to continue registering other pattern

        :return:
        :rtype:
        """
        return self.rebulk

    def _match(self, pattern, input_string, context=None):
        chain_matches = []
        chain_input_string = input_string
        offset = 0
        while offset < len(input_string):
            current_chain_matches = []
            valid_chain = True
            is_chain_start = True
            for chain_part in self.parts:
                try:
                    chain_part_matches = Chain._match_chain_part(is_chain_start, chain_part, chain_input_string,
                                                                 context)
                    if chain_part_matches:
                        Chain._fix_matches_offset(chain_part_matches, input_string, offset)
                        offset = chain_part_matches[-1].raw_end
                        chain_input_string = input_string[offset:]
                        if not chain_part.is_hidden:
                            current_chain_matches.extend(chain_part_matches)
                except _InvalidChainException:
                    valid_chain = False
                    if current_chain_matches:
                        offset = current_chain_matches[0].raw_end
                    break
                is_chain_start = False
            if not current_chain_matches:
                break
            if valid_chain:
                match = self._build_chain_match(current_chain_matches, input_string)
                chain_matches.append(match)

        return chain_matches

    def _build_chain_match(self, current_chain_matches, input_string):
        start = None
        end = None
        for match in current_chain_matches:
            if start is None or start > match.start:
                start = match.start
            if end is None or end < match.end:
                end = match.end
        match = call(Match, start, end, pattern=self, input_string=input_string, **self._match_kwargs)
        for chain_match in current_chain_matches:
            if chain_match.children:
                for child in chain_match.children:
                    match.children.append(child)
            if chain_match not in match.children:
                match.children.append(chain_match)
        return match

    @staticmethod
    def _fix_matches_offset(chain_part_matches, input_string, offset):
        for chain_part_match in chain_part_matches:
            if chain_part_match.input_string != input_string:
                chain_part_match.input_string = input_string
                chain_part_match.end += offset
                chain_part_match.start += offset
            if chain_part_match.children:
                Chain._fix_matches_offset(chain_part_match.children, input_string, offset)

    @staticmethod
    def _match_chain_part(is_chain_start, chain_part, chain_input_string, context):
        chain_part_matches = chain_part.pattern.matches(chain_input_string, context)
        chain_part_matches = Chain._truncate_chain_part_matches(is_chain_start, chain_part_matches, chain_part,
                                                                chain_input_string)
        Chain._validate_chain_part_matches(chain_part_matches, chain_part)
        return chain_part_matches

    @staticmethod
    def _truncate_chain_part_matches(is_chain_start, chain_part_matches, chain_part, chain_input_string):
        if not chain_part_matches:
            return chain_part_matches

        if not is_chain_start:
            separator = chain_input_string[0:chain_part_matches[0].initiator.raw_start]
            if len(separator) > 0:
                return []

        j = 1
        for i in range(0, len(chain_part_matches) - 1):
            separator = chain_input_string[chain_part_matches[i].initiator.raw_end:
                                           chain_part_matches[i + 1].initiator.raw_start]
            if len(separator) > 0:
                break
            j += 1
        truncated = chain_part_matches[:j]
        if chain_part.repeater_end is not None:
            return truncated[:chain_part.repeater_end]
        return truncated

    @staticmethod
    def _validate_chain_part_matches(chain_part_matches, chain_part):
        if len(chain_part_matches) < chain_part.repeater_start:
            raise _InvalidChainException

    @property
    def match_options(self):
        return {}

    @property
    def patterns(self):
        return [self]

    def __repr__(self):
        defined = ""
        if self.defined_at:
            defined = "@" + six.text_type(self.defined_at)
        return "<{0!s}{1!s}:{2!s}>".format(self.__class__.__name__, defined, self.parts)


class ChainPart(object):
    """
    Part of a pattern chain.
    """

    def __init__(self, chain, pattern):
        self._chain = chain
        self.pattern = pattern
        self.repeater_start = 1
        self.repeater_end = 1
        self._hidden = False

    def chain(self):
        """
        Add patterns chain, using configuration from this chain

        :return:
        :rtype:
        """
        return self._chain.chain()

    def hidden(self, hidden=True):
        """
        Hide chain part results from global chain result

        :param hidden:
        :type hidden:
        :return:
        :rtype:
        """
        self._hidden = hidden
        return self

    @property
    def is_hidden(self):
        """
        Check if the chain part is hidden
        :return:
        :rtype:
        """
        return self._hidden

    def regex(self, *pattern, **kwargs):
        """
        Add re pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        return self._chain.regex(*pattern, **kwargs)

    def functional(self, *pattern, **kwargs):
        """
        Add functional pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        return self._chain.functional(*pattern, **kwargs)

    def string(self, *pattern, **kwargs):
        """
        Add string pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        return self._chain.string(*pattern, **kwargs)

    def close(self):
        """
        Close the chain builder to continue registering other patterns

        :return:
        :rtype:
        """
        return self._chain.close()

    def repeater(self, value):
        """
        Define the repeater of the current chain part.

        :param value:
        :type value:
        :return:
        :rtype:
        """
        try:
            value = int(value)
            self.repeater_start = value
            self.repeater_end = value
            return self
        except ValueError:
            pass
        if value == '+':
            self.repeater_start = 1
            self.repeater_end = None
        if value == '*':
            self.repeater_start = 0
            self.repeater_end = None
        elif value == '?':
            self.repeater_start = 0
            self.repeater_end = 1
        else:
            match = re.match(r'\{\s*(\d*)\s*,?\s*(\d*)\s*\}', value)
            if match:
                start = match.group(1)
                end = match.group(2)
                if start or end:
                    self.repeater_start = int(start) if start else 0
                    self.repeater_end = int(end) if end else None
        return self

    def __repr__(self):
        return "{0!s}({{{1!s},{2!s}}})".format(self.pattern, self.repeater_start, self.repeater_end)
