#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
release_group property
"""
import copy

from rebulk.remodule import re

from rebulk import Rebulk, Rule, AppendMatch
from ..common.validators import int_coercable
from ..properties.title import TitleFromPosition
from ..common.formatters import cleanup
from ..common import seps, dash
from ..common.comparators import marker_sorted


def release_group():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    return Rebulk().rules(SceneReleaseGroup, AnimeReleaseGroup, ExpectedReleaseGroup)


forbidden_groupnames = ['rip', 'by', 'for', 'par', 'pour', 'bonus']

groupname_ignore_seps = '[]{}()'
groupname_seps = ''.join([c for c in seps if c not in groupname_ignore_seps])


def clean_groupname(string):
    """
    Removes and strip separators from input_string
    :param input_string:
    :type input_string:
    :return:
    :rtype:
    """
    string = string.strip(groupname_seps)
    if not (string.endswith(tuple(groupname_ignore_seps)) and string.startswith(tuple(groupname_ignore_seps)))\
            and not any(i in string.strip(groupname_ignore_seps) for i in groupname_ignore_seps):
        string = string.strip(groupname_ignore_seps)
    for forbidden in forbidden_groupnames:
        if string.lower().startswith(forbidden):
            string = string[len(forbidden):]
            string = string.strip(groupname_seps)
        if string.lower().endswith(forbidden):
            string = string[:len(forbidden)]
            string = string.strip(groupname_seps)
    return string


_scene_previous_names = ['video_codec', 'format', 'video_api', 'audio_codec', 'audio_profile', 'video_profile',
                         'audio_channels', 'screen_size', 'other', 'container', 'language', 'subtitle_language',
                         'subtitle_language.suffix', 'subtitle_language.prefix']

_scene_previous_tags = ['release-group-prefix']


class ExpectedReleaseGroup(Rule):
    """
    Add release_group match from expected_group option
    """
    consequence = AppendMatch

    properties = {'release_group': [None]}

    def enabled(self, context):
        return context.get('expected_group')

    def when(self, matches, context):
        expected_rebulk = Rebulk().defaults(name='release_group')

        for expected_group in context.get('expected_group'):
            if expected_group.startswith('re:'):
                expected_group = expected_group[3:]
                expected_group = expected_group.replace(' ', '-')
                expected_rebulk.regex(expected_group, abbreviations=[dash], flags=re.IGNORECASE)
            else:
                expected_rebulk.string(expected_group, ignore_case=True)

        matches = expected_rebulk.matches(matches.input_string, context)
        return matches


class SceneReleaseGroup(Rule):
    """
    Add release_group match in existing matches (scene format).

    Something.XViD-ReleaseGroup.mkv
    """
    dependency = [TitleFromPosition, ExpectedReleaseGroup]
    consequence = AppendMatch

    properties = {'release_group': [None]}

    def when(self, matches, context):
        # If a release_group is found before, ignore this kind of release_group rule.

        ret = []

        for filepart in marker_sorted(matches.markers.named('path'), matches):
            start, end = filepart.span

            last_hole = matches.holes(start, end + 1, formatter=clean_groupname,
                                      predicate=lambda hole: cleanup(hole.value), index=-1)

            if last_hole:
                previous_match = matches.previous(last_hole,
                                                  lambda match: not match.private or
                                                  match.name in _scene_previous_names,
                                                  index=0)
                if previous_match and (previous_match.name in _scene_previous_names or
                                       any(tag in previous_match.tags for tag in _scene_previous_tags)) and \
                        not matches.input_string[previous_match.end:last_hole.start].strip(seps) \
                        and not int_coercable(last_hole.value.strip(seps)):

                    last_hole.name = 'release_group'
                    last_hole.tags = ['scene']

                    # if hole is inside a group marker with same value, remove [](){} ...
                    group = matches.markers.at_match(last_hole, lambda marker: marker.name == 'group', 0)
                    if group:
                        group.formatter = clean_groupname
                        if group.value == last_hole.value:
                            last_hole.start = group.start + 1
                            last_hole.end = group.end - 1
                            last_hole.tags = ['anime']

                    ret.append(last_hole)
        return ret


class AnimeReleaseGroup(Rule):
    """
    Add release_group match in existing matches (anime format)
    ...[ReleaseGroup] Something.mkv
    """
    dependency = [SceneReleaseGroup, TitleFromPosition]
    consequence = AppendMatch

    properties = {'release_group': [None]}

    def when(self, matches, context):
        ret = []

        # If a release_group is found before, ignore this kind of release_group rule.
        if not matches.named('episode') and not matches.named('season') and matches.named('release_group'):
            # This doesn't seems to be an anime
            return

        for filepart in marker_sorted(matches.markers.named('path'), matches):

            # pylint:disable=bad-continuation
            empty_group_marker = matches.markers \
                .range(filepart.start, filepart.end, lambda marker: marker.name == 'group'
                                                                    and not matches.range(marker.start, marker.end)
                                                                    and not int_coercable(marker.value.strip(seps)),
                       0)

            if empty_group_marker:
                group = copy.copy(empty_group_marker)
                group.marker = False
                group.raw_start += 1
                group.raw_end -= 1
                group.tags = ['anime']
                group.name = 'release_group'
                ret.append(group)
        return ret
