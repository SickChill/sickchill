#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Processors
"""
from collections import defaultdict
import copy

import six

from rebulk import Rebulk, Rule, CustomRule, POST_PROCESS, PRE_PROCESS, AppendMatch, RemoveMatch
from guessit.rules.common.words import iter_words
from .common.formatters import cleanup
from .common.comparators import marker_sorted
from .common.date import valid_year


class EnlargeGroupMatches(CustomRule):
    """
    Enlarge matches that are starting and/or ending group to include brackets in their span.
    :param matches:
    :type matches:
    :return:
    :rtype:
    """
    priority = PRE_PROCESS

    def when(self, matches, context):
        starting = []
        ending = []

        for group in matches.markers.named('group'):
            for match in matches.starting(group.start + 1):
                starting.append(match)

            for match in matches.ending(group.end - 1):
                ending.append(match)

        if starting or ending:
            return starting, ending

    def then(self, matches, when_response, context):
        starting, ending = when_response
        for match in starting:
            matches.remove(match)
            match.start -= 1
            match.raw_start += 1
            matches.append(match)

        for match in ending:
            matches.remove(match)
            match.end += 1
            match.raw_end -= 1
            matches.append(match)


class EquivalentHoles(Rule):
    """
    Creates equivalent matches for holes that have same values than existing (case insensitive)
    """
    priority = POST_PROCESS
    consequence = AppendMatch

    def when(self, matches, context):
        new_matches = []

        for filepath in marker_sorted(matches.markers.named('path'), matches):
            holes = matches.holes(start=filepath.start, end=filepath.end, formatter=cleanup)
            for name in matches.names:
                for hole in list(holes):
                    for current_match in matches.named(name):
                        if isinstance(current_match.value, six.string_types) and \
                                        hole.value.lower() == current_match.value.lower():
                            if 'equivalent-ignore' in current_match.tags:
                                continue
                            new_value = _preferred_string(hole.value, current_match.value)
                            if hole.value != new_value:
                                hole.value = new_value
                            if current_match.value != new_value:
                                current_match.value = new_value
                            hole.name = name
                            hole.tags = ['equivalent']
                            new_matches.append(hole)
                            if hole in holes:
                                holes.remove(hole)

        return new_matches


class RemoveAmbiguous(Rule):
    """
    If multiple match are found with same name and different values, keep the one in the most valuable filepart.
    Also keep others match with same name and values than those kept ones.
    """
    priority = POST_PROCESS
    consequence = RemoveMatch

    def when(self, matches, context):
        fileparts = marker_sorted(matches.markers.named('path'), matches)

        previous_fileparts_names = set()
        values = defaultdict(list)

        to_remove = []
        for filepart in fileparts:
            filepart_matches = matches.range(filepart.start, filepart.end)

            filepart_names = set()
            for match in filepart_matches:
                filepart_names.add(match.name)
                if match.name in previous_fileparts_names:
                    if match.value not in values[match.name]:
                        to_remove.append(match)
                else:
                    if match.value not in values[match.name]:
                        values[match.name].append(match.value)

            previous_fileparts_names.update(filepart_names)

        return to_remove


def _preferred_string(value1, value2):  # pylint:disable=too-many-return-statements
    """
    Retrieves preferred title from both values.
    :param value1:
    :type value1: str
    :param value2:
    :type value2: str
    :return: The preferred title
    :rtype: str
    """
    if value1 == value2:
        return value1
    if value1.istitle() and not value2.istitle():
        return value1
    if not value1.isupper() and value2.isupper():
        return value1
    if not value1.isupper() and value1[0].isupper() and not value2[0].isupper():
        return value1
    if _count_title_words(value1) > _count_title_words(value2):
        return value1
    return value2


def _count_title_words(value):
    """
    Count only many words are titles in value.
    :param value:
    :type value:
    :return:
    :rtype:
    """
    ret = 0
    for word in iter_words(value):
        if word.value.istitle():
            ret += 1
    return ret


class SeasonYear(Rule):
    """
    If a season is a valid year and no year was found, create an match with year.
    """
    priority = POST_PROCESS
    consequence = AppendMatch

    def when(self, matches, context):
        ret = []
        if not matches.named('year'):
            for season in matches.named('season'):
                if valid_year(season.value):
                    year = copy.copy(season)
                    year.name = 'year'
                    ret.append(year)
        return ret


class Processors(CustomRule):
    """
    Empty rule for ordering post_processing properly.
    """
    priority = POST_PROCESS

    def when(self, matches, context):
        pass

    def then(self, matches, when_response, context):  # pragma: no cover
        pass


def processors():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    return Rebulk().rules(EnlargeGroupMatches, EquivalentHoles, RemoveAmbiguous, SeasonYear, Processors)
