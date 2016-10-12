#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comparators
"""
try:
    from functools import cmp_to_key
except ImportError:
    from ...backports import cmp_to_key


def marker_comparator_predicate(match):
    """
    Match predicate used in comparator
    """
    return not match.private and \
           match.name not in ['proper_count', 'title', 'episode_title', 'alternative_title'] and \
           not (match.name == 'container' and 'extension' in match.tags)


def marker_weight(matches, marker):
    """
    Compute the comparator weight of a marker
    :param matches:
    :param marker:
    :return:
    """
    return len(set(match.name for match in matches.range(*marker.span, predicate=marker_comparator_predicate)))


def marker_comparator(matches, markers):
    """
    Builds a comparator that returns markers sorted from the most valuable to the less.

    Take the parts where matches count is higher, then when length is higher, then when position is at left.

    :param matches:
    :type matches:
    :return:
    :rtype:
    """
    def comparator(marker1, marker2):
        """
        The actual comparator function.
        """
        matches_count = marker_weight(matches, marker2) - marker_weight(matches, marker1)
        if matches_count:
            return matches_count
        len_diff = len(marker2) - len(marker1)
        if len_diff:
            return len_diff
        return markers.index(marker2) - markers.index(marker1)

    return comparator


def marker_sorted(markers, matches):
    """
    Sort markers from matches, from the most valuable to the less.

    :param fileparts:
    :type fileparts:
    :param matches:
    :type matches:
    :return:
    :rtype:
    """
    return sorted(markers, key=cmp_to_key(marker_comparator(matches, markers)))
