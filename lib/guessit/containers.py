#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
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

import types

from .patterns import compile_pattern, sep
from . import base_text_type
from .guess import Guess


def _get_span(prop, match):
    """Retrieves span for a match"""
    if not prop.global_span and match.re.groups:
        start = None
        end = None
        for i in range(1, match.re.groups + 1):
            span = match.span(i)
            if start is None or span[0] < start:
                start = span[0]
            if end is None or span[1] > end:
                end = span[1]
        return start, end
    else:
        return match.span()


def _trim_span(span, value, blanks = sep):
    start, end = span

    for i in range(0, len(value)):
        if value[i] in blanks:
            start += 1
        else:
            break

    for i in reversed(range(0, len(value))):
        if value[i] in blanks:
            end -= 1
        else:
            break
    if end <= start:
        return -1, -1
    return start, end


def _get_groups(compiled_re):
    """
    Retrieves groups from re

    :return: list of group names
    """
    if compiled_re.groups:
        indexgroup = {}
        for k, i in compiled_re.groupindex.items():
            indexgroup[i] = k
        ret = []
        for i in range(1, compiled_re.groups + 1):
            ret.append(indexgroup.get(i, i))
        return ret
    else:
        return [None]


class NoValidator(object):
    @staticmethod
    def validate(prop, string, node, match, entry_start, entry_end):
        return True


class LeftValidator(object):
    """Make sure our match is starting by separator, or by another entry"""

    @staticmethod
    def validate(prop, string, node, match, entry_start, entry_end):
        span = _get_span(prop, match)
        span = _trim_span(span, string[span[0]:span[1]])
        start, end = span

        sep_start = start <= 0 or string[start - 1] in sep
        start_by_other = start in entry_end
        if not sep_start and not start_by_other:
            return False
        return True


class RightValidator(object):
    """Make sure our match is ended by separator, or by another entry"""

    @staticmethod
    def validate(prop, string, node, match, entry_start, entry_end):
        span = _get_span(prop, match)
        span = _trim_span(span, string[span[0]:span[1]])
        start, end = span

        sep_end = end >= len(string) or string[end] in sep
        end_by_other = end in entry_start
        if not sep_end and not end_by_other:
            return False
        return True


class ChainedValidator(object):
    def __init__(self, *validators):
        self._validators = validators

    def validate(self, prop, string, node, match, entry_start, entry_end):
        for validator in self._validators:
            if not validator.validate(prop, string, node, match, entry_start, entry_end):
                return False
        return True


class SameKeyValidator(object):
    def __init__(self, validator_function):
        self.validator_function = validator_function

    def validate(self, prop, string, node, match, entry_start, entry_end):
        path_nodes = [path_node for path_node in node.ancestors if path_node.category == 'path']
        if path_nodes:
            path_node = path_nodes[0]
        else:
            path_node = node.root

        for key in prop.keys:
            for same_value_leaf in path_node.leaves_containing(key):
                ret = self.validator_function(same_value_leaf, key, prop, string, node, match, entry_start, entry_end)
                if ret is not None:
                    return ret
        return True


class OnlyOneValidator(SameKeyValidator):
    """
    Check that there's only one occurence of key for current directory
    """
    def __init__(self):
        super(OnlyOneValidator, self).__init__(lambda same_value_leaf, key, prop, string, node, match, entry_start, entry_end: False)


class DefaultValidator(object):
    """Make sure our match is surrounded by separators, or by another entry"""
    def validate(self, prop, string, node, match, entry_start, entry_end):
        span = _get_span(prop, match)
        span = _trim_span(span, string[span[0]:span[1]])
        return DefaultValidator.validate_string(string, span, entry_start, entry_end)

    @staticmethod
    def validate_string(string, span, entry_start=None, entry_end=None):
        start, end = span

        sep_start = start <= 0 or string[start - 1] in sep
        sep_end = end >= len(string) or string[end] in sep
        start_by_other = start in entry_end if entry_end else False
        end_by_other = end in entry_start if entry_start else False
        if (sep_start or start_by_other) and (sep_end or end_by_other):
            return True
        return False


class FunctionValidator(object):
    def __init__(self, function):
        self.function = function

    def validate(self, prop, string, node, match, entry_start, entry_end):
        return self.function(prop, string, node, match, entry_start, entry_end)


class FormatterValidator(object):
    def __init__(self, group_name=None, formatted_validator=None):
        self.group_name = group_name
        self.formatted_validator = formatted_validator

    def validate(self, prop, string, node, match, entry_start, entry_end):
        if self.group_name:
            formatted = prop.format(match.group(self.group_name), self.group_name)
        else:
            formatted = prop.format(match.group())
        if self.formatted_validator:
            return self.formatted_validator(formatted)
        else:
            return formatted


def _get_positions(prop, string, node, match, entry_start, entry_end):
    span = match.span()
    start = span[0]
    end = span[1]

    at_start = True
    at_end = True

    while start > 0:
        start -= 1
        if string[start] not in sep:
            at_start = False
            break
    while end < len(string) - 1:
        end += 1
        if string[end] not in sep:
            at_end = False
            break
    return at_start, at_end


class WeakValidator(DefaultValidator):
    """Make sure our match is surrounded by separators and is the first or last element in the string"""
    def validate(self, prop, string, node, match, entry_start, entry_end):
        if super(WeakValidator, self).validate(prop, string, node, match, entry_start, entry_end):
            at_start, at_end = _get_positions(prop, string, node, match, entry_start, entry_end)
            return at_start or at_end
        return False


class NeighborValidator(DefaultValidator):
    """Make sure the node is next another one"""
    def validate(self, prop, string, node, match, entry_start, entry_end):
        at_start, at_end = _get_positions(prop, string, node, match, entry_start, entry_end)

        if at_start:
            previous_leaf = node.root.previous_leaf(node)
            if previous_leaf is not None:
                return True

        if at_end:
            next_leaf = node.root.next_leaf(node)
            if next_leaf is not None:
                return True

        return False

class FullMatchValidator(DefaultValidator):
    """Make sure the node match fully"""
    def validate(self, prop, string, node, match, entry_start, entry_end):
        at_start, at_end = _get_positions(prop, string, node, match, entry_start, entry_end)

        return at_start and at_end


class LeavesValidator(DefaultValidator):
    def __init__(self, lambdas=None, previous_lambdas=None, next_lambdas=None, both_side=False, default_=True):
        self.previous_lambdas = previous_lambdas if previous_lambdas is not None else []
        self.next_lambdas = next_lambdas if next_lambdas is not None else []
        if lambdas:
            self.previous_lambdas.extend(lambdas)
            self.next_lambdas.extend(lambdas)
        self.both_side = both_side
        self.default_ = default_

    """Make sure our match is surrounded by separators and validates defined lambdas"""
    def validate(self, prop, string, node, match, entry_start, entry_end):
        if self.default_:
            super_ret = super(LeavesValidator, self).validate(prop, string, node, match, entry_start, entry_end)
        else:
            super_ret = True
        if not super_ret:
            return False

        previous_ = self._validate_previous(prop, string, node, match, entry_start, entry_end)
        next_ = self._validate_next(prop, string, node, match, entry_start, entry_end)

        if previous_ is None and next_ is None:
            return super_ret
        if self.both_side:
            return previous_ and next_
        else:
            return previous_ or next_

    def _validate_previous(self, prop, string, node, match, entry_start, entry_end):
        if self.previous_lambdas:
            for leaf in node.root.previous_leaves(node):
                for lambda_ in self.previous_lambdas:
                    ret = self._check_rule(lambda_, leaf)
                    if ret is not None:
                        return ret
            return False

    def _validate_next(self, prop, string, node, match, entry_start, entry_end):
        if self.next_lambdas:
            for leaf in node.root.next_leaves(node):
                for lambda_ in self.next_lambdas:
                    ret = self._check_rule(lambda_, leaf)
                    if ret is not None:
                        return ret
            return False

    @staticmethod
    def _check_rule(lambda_, previous_leaf):
        return lambda_(previous_leaf)


class _Property:
    """Represents a property configuration."""
    def __init__(self, keys=None, pattern=None, canonical_form=None, canonical_from_pattern=True, confidence=1.0, enhance=True, global_span=False, validator=DefaultValidator(), formatter=None, disabler=None, confidence_lambda=None, remove_duplicates=False):
        """
        :param keys: Keys of the property (format, screenSize, ...)
        :type keys: string
        :param canonical_form: Unique value of the property (DVD, 720p, ...)
        :type canonical_form: string
        :param pattern: Regexp pattern
        :type pattern: string
        :param confidence: confidence
        :type confidence: float
        :param enhance: enhance the pattern
        :type enhance: boolean
        :param global_span: if True, the whole match span will used to create the Guess.
                            Else, the span from the capturing groups will be used.
        :type global_span: boolean
        :param validator: Validator to use
        :type validator: :class:`DefaultValidator`
        :param formatter: Formater to use
        :type formatter: function
        :param remove_duplicates: Keep only the last match if multiple values are found
        :type remove_duplicates: bool
        """
        if isinstance(keys, list):
            self.keys = keys
        elif isinstance(keys, base_text_type):
            self.keys = [keys]
        else:
            self.keys = []
        self.canonical_form = canonical_form
        if pattern is not None:
            self.pattern = pattern
        else:
            self.pattern = canonical_form
        if self.canonical_form is None and canonical_from_pattern:
            self.canonical_form = self.pattern
        self.compiled = compile_pattern(self.pattern, enhance=enhance)
        for group_name in _get_groups(self.compiled):
            if isinstance(group_name, base_text_type) and not group_name in self.keys:
                self.keys.append(group_name)
        if not self.keys:
            raise ValueError("No property key is defined")
        self.confidence = confidence
        self.confidence_lambda = confidence_lambda
        self.global_span = global_span
        self.validator = validator
        self.formatter = formatter
        self.disabler = disabler
        self.remove_duplicates = remove_duplicates

    def disabled(self, options):
        if self.disabler:
            return self.disabler(options)
        return False

    def format(self, value, group_name=None):
        """Retrieves the final value from re group match value"""
        formatter = None
        if isinstance(self.formatter, dict):
            formatter = self.formatter.get(group_name)
            if formatter is None and group_name is not None:
                formatter = self.formatter.get(None)
        else:
            formatter = self.formatter
        if isinstance(formatter, types.FunctionType):
            return formatter(value)
        elif formatter is not None:
            return formatter.format(value)
        return value

    def __repr__(self):
        return "%s: %s" % (self.keys, self.canonical_form if self.canonical_form else self.pattern)


class PropertiesContainer(object):
    def __init__(self, **kwargs):
        self._properties = []
        self.default_property_kwargs = kwargs

    def unregister_property(self, name, *canonical_forms):
        """Unregister a property canonical forms

        If canonical_forms are specified, only those values will be unregistered

        :param name: Property name to unregister
        :type name: string
        :param canonical_forms: Values to unregister
        :type canonical_forms: varargs of string
        """
        _properties = [prop for prop in self._properties if prop.name == name and (not canonical_forms or prop.canonical_form in canonical_forms)]

    def register_property(self, name, *patterns, **property_params):
        """Register property with defined canonical form and patterns.

        :param name: name of the property (format, screenSize, ...)
        :type name: string
        :param patterns: regular expression patterns to register for the property canonical_form
        :type patterns: varargs of string
        """
        properties = []
        for pattern in patterns:
            params = dict(self.default_property_kwargs)
            params.update(property_params)
            if isinstance(pattern, dict):
                params.update(pattern)
                prop = _Property(name, **params)
            else:
                prop = _Property(name, pattern, **params)
            self._properties.append(prop)
            properties.append(prop)
        return properties

    def register_canonical_properties(self, name, *canonical_forms, **property_params):
        """Register properties from their canonical forms.

        :param name: name of the property (releaseGroup, ...)
        :type name: string
        :param canonical_forms: values of the property ('ESiR', 'WAF', 'SEPTiC', ...)
        :type canonical_forms: varargs of strings
        """
        properties = []
        for canonical_form in canonical_forms:
            params = dict(property_params)
            params['canonical_form'] = canonical_form
            properties.extend(self.register_property(name, canonical_form, **property_params))
        return properties

    def unregister_all_properties(self):
        """Unregister all defined properties"""
        self._properties.clear()

    def find_properties(self, string, node, options, name=None, validate=True, re_match=False, sort=True, multiple=False):
        """Find all distinct properties for given string

        If no capturing group is defined in the property, value will be grabbed from the entire match.

        If one ore more unnamed capturing group is defined in the property, first capturing group will be used.

        If named capturing group are defined in the property, they will be returned as property key.

        If validate, found properties will be validated by their defined validator

        If re_match, re.match will be used instead of re.search.

        if sort, found properties will be sorted from longer match to shorter match.

        If multiple is False and multiple values are found for the same property, the more confident one will be returned.

        If multiple is False and multiple values are found for the same property and the same confidence, the longer will be returned.

        :param string: input string
        :type string: string

        :param node: current node of the matching tree
        :type node: :class:`guessit.matchtree.MatchTree`

        :param name: name of property to find
        :type name: string

        :param re_match: use re.match instead of re.search
        :type re_match: bool

        :param multiple: Allows multiple property values to be returned
        :type multiple: bool

        :return: found properties
        :rtype: list of tuples (:class:`_Property`, match, list of tuples (property_name, tuple(value_start, value_end)))

        :see: `_Property`
        :see: `register_property`
        :see: `register_canonical_properties`
        """
        entry_start = {}
        entry_end = {}

        entries = []
        duplicate_matches = {}

        ret = []

        if not string.strip():
            return ret

        # search all properties
        for prop in self.get_properties(name):
            if not prop.disabled(options):
                valid_match = None
                if re_match:
                    match = prop.compiled.match(string)
                    if match:
                        entries.append((prop, match))
                else:
                    matches = list(prop.compiled.finditer(string))
                    if prop.remove_duplicates:
                        duplicate_matches[prop] = matches
                    for match in matches:
                        entries.append((prop, match))

        for prop, match in entries:
            # compute confidence
            if prop.confidence_lambda:
                computed_confidence = prop.confidence_lambda(match)
                if computed_confidence is not None:
                    prop.confidence = computed_confidence

        entries.sort(key=lambda entry: -entry[0].confidence)
        # sort entries, from most confident to less confident

        if validate:
            # compute entries start and ends
            for prop, match in entries:
                start, end = _get_span(prop, match)

                if start not in entry_start:
                    entry_start[start] = [prop]
                else:
                    entry_start[start].append(prop)

                if end not in entry_end:
                    entry_end[end] = [prop]
                else:
                    entry_end[end].append(prop)

            # remove invalid values
            while True:
                invalid_entries = []
                for entry in entries:
                    prop, match = entry
                    if not prop.validator.validate(prop, string, node, match, entry_start, entry_end):
                        invalid_entries.append(entry)
                if not invalid_entries:
                    break
                for entry in invalid_entries:
                    prop, match = entry
                    entries.remove(entry)
                    prop_duplicate_matches = duplicate_matches.get(prop)
                    if prop_duplicate_matches:
                        prop_duplicate_matches.remove(match)
                    invalid_span = _get_span(prop, match)
                    start = invalid_span[0]
                    end = invalid_span[1]
                    entry_start[start].remove(prop)
                    if not entry_start.get(start):
                        del entry_start[start]
                    entry_end[end].remove(prop)
                    if not entry_end.get(end):
                        del entry_end[end]

        for prop, prop_duplicate_matches in duplicate_matches.items():
            # Keeping the last valid match only.
            # Needed for the.100.109.hdtv-lol.mp4
            for duplicate_match in prop_duplicate_matches[:-1]:
                entries.remove((prop, duplicate_match))

        if multiple:
            ret = entries
        else:
            # keep only best match if multiple values where found
            entries_dict = {}
            for entry in entries:
                for key in prop.keys:
                    if key not in entries_dict:
                        entries_dict[key] = []
                    entries_dict[key].append(entry)

            for key_entries in entries_dict.values():
                if multiple:
                    for entry in key_entries:
                        ret.append(entry)
                else:
                    best_ret = {}

                    best_prop, best_match = None, None
                    if len(key_entries) == 1:
                        best_prop, best_match = key_entries[0]
                    else:
                        for prop, match in key_entries:
                            start, end = _get_span(prop, match)
                            if not best_prop or \
                            best_prop.confidence < prop.confidence or \
                            best_prop.confidence == prop.confidence and \
                            best_match.span()[1] - best_match.span()[0] < match.span()[1] - match.span()[0]:
                                best_prop, best_match = prop, match

                    best_ret[best_prop] = best_match

                    for prop, match in best_ret.items():
                        ret.append((prop, match))

        if sort:
            def _sorting(x):
                _, x_match = x
                x_start, x_end = x_match.span()
                return x_start - x_end

            ret.sort(key=_sorting)

        return ret

    def as_guess(self, found_properties, input=None, filter_=None, sep_replacement=None, multiple=False, *args, **kwargs):
        if filter_ is None:
            filter_ = lambda property, *args, **kwargs: True
        guesses = [] if multiple else None
        for prop, match in found_properties:
            first_key = None
            for key in prop.keys:
                # First property key will be used as base for effective name
                if isinstance(key, base_text_type):
                    if first_key is None:
                        first_key = key
                        break
            property_name = first_key if first_key else None
            span = _get_span(prop, match)
            guess = Guess(confidence=prop.confidence, input=input, span=span, prop=property_name)
            groups = _get_groups(match.re)
            for group_name in groups:
                name = group_name if isinstance(group_name, base_text_type) else property_name if property_name not in groups else None
                if name:
                    value = self._effective_prop_value(prop, group_name, input, match.span(group_name) if group_name else match.span(), sep_replacement)
                    if not value is None:
                        is_string = isinstance(value, base_text_type)
                        if not is_string or is_string and value:  # Keep non empty strings and other defined objects
                            if isinstance(value, dict):
                                for k, v in value.items():
                                    if k is None:
                                        k = name
                                    guess[k] = v
                            else:
                                if name in guess:
                                    if not isinstance(guess[name], list):
                                        guess[name] = [guess[name]]
                                    guess[name].append(value)
                                else:
                                    guess[name] = value
                            if group_name:
                                guess.metadata(prop).span = match.span(group_name)
            if filter_(guess):
                if multiple:
                    guesses.append(guess)
                else:
                    return guess
        return guesses

    @staticmethod
    def _effective_prop_value(prop, group_name, input=None, span=None, sep_replacement=None):
        if prop.canonical_form:
            return prop.canonical_form
        if input is None:
            return None
        value = input
        if span is not None:
            value = value[span[0]:span[1]]
        value = input[span[0]:span[1]] if input else None
        if sep_replacement:
            for sep_char in sep:
                value = value.replace(sep_char, sep_replacement)
        if value:
            value = prop.format(value, group_name)
        return value

    def get_properties(self, name=None, canonical_form=None):
        """Retrieve properties

        :return: Properties
        :rtype: generator
        """
        for prop in self._properties:
            if (name is None or name in prop.keys) and (canonical_form is None or prop.canonical_form == canonical_form):
                yield prop

    def get_supported_properties(self):
        supported_properties = {}
        for prop in self.get_properties():
            for k in prop.keys:
                values = supported_properties.get(k)
                if not values:
                    values = set()
                    supported_properties[k] = values
                if prop.canonical_form:
                    values.add(prop.canonical_form)
        return supported_properties


class QualitiesContainer():
    def __init__(self):
        self._qualities = {}

    def register_quality(self, name, canonical_form, rating):
        """Register a quality rating.

        :param name: Name of the property
        :type name: string
        :param canonical_form: Value of the property
        :type canonical_form: string
        :param rating: Estimated quality rating for the property
        :type rating: int
        """
        property_qualities = self._qualities.get(name)

        if property_qualities is None:
            property_qualities = {}
            self._qualities[name] = property_qualities

        property_qualities[canonical_form] = rating

    def unregister_quality(self, name, *canonical_forms):
        """Unregister quality ratings for given property name.

        If canonical_forms are specified, only those values will be unregistered

        :param name: Name of the property
        :type name: string
        :param canonical_forms: Value of the property
        :type canonical_forms: string
        """
        if not canonical_forms:
            if name in self._qualities:
                del self._qualities[name]
        else:
            property_qualities = self._qualities.get(name)
            if property_qualities is not None:
                for property_canonical_form in canonical_forms:
                    if property_canonical_form in property_qualities:
                        del property_qualities[property_canonical_form]
            if not property_qualities:
                del self._qualities[name]

    def clear_qualities(self,):
        """Unregister all defined quality ratings.
        """
        self._qualities.clear()

    def rate_quality(self, guess, *props):
        """Rate the quality of guess.

        :param guess: Guess to rate
        :type guess: :class:`guessit.guess.Guess`
        :param props: Properties to include in the rating. if empty, rating will be performed for all guess properties.
        :type props: varargs of string

        :return: Quality of the guess. The higher, the better.
        :rtype: int
        """
        rate = 0
        if not props:
            props = guess.keys()
        for prop in props:
            prop_value = guess.get(prop)
            prop_qualities = self._qualities.get(prop)
            if prop_value is not None and prop_qualities is not None:
                rate += prop_qualities.get(prop_value, 0)
        return rate

    def best_quality_properties(self, props, *guesses):
        """Retrieve the best quality guess, based on given properties

        :param props: Properties to include in the rating
        :type props: list of strings
        :param guesses: Guesses to rate
        :type guesses: :class:`guessit.guess.Guess`

        :return: Best quality guess from all passed guesses
        :rtype: :class:`guessit.guess.Guess`
        """
        best_guess = None
        best_rate = None
        for guess in guesses:
            rate = self.rate_quality(guess, *props)
            if best_rate is None or best_rate < rate:
                best_rate = rate
                best_guess = guess
        return best_guess

    def best_quality(self, *guesses):
        """Retrieve the best quality guess.

        :param guesses: Guesses to rate
        :type guesses: :class:`guessit.guess.Guess`

        :return: Best quality guess from all passed guesses
        :rtype: :class:`guessit.guess.Guess`
        """
        best_guess = None
        best_rate = None
        for guess in guesses:
            rate = self.rate_quality(guess)
            if best_rate is None or best_rate < rate:
                best_rate = rate
                best_guess = guess
        return best_guess

