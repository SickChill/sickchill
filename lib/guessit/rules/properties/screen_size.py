#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
screen_size property
"""
from rebulk.remodule import re

from rebulk import Rebulk, Rule, RemoveMatch
from ..common.validators import seps_surround
from ..common import dash


def screen_size():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    def conflict_solver(match, other):
        """
        Conflict solver for most screen_size.
        """
        if other.name == 'screen_size':
            if 'resolution' in other.tags:
                # The chtouile to solve conflict in "720 x 432" string matching both 720p pattern
                int_value = _digits_re.findall(match.raw)[-1]
                if other.value.startswith(int_value):
                    return match
            return other
        return '__default__'

    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(name="screen_size", validator=seps_surround, conflict_solver=conflict_solver)

    rebulk.regex(r"(?:\d{3,}(?:x|\*))?360(?:i|p?x?)", value="360p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?368(?:i|p?x?)", value="368p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?480(?:i|p?x?)", value="480p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?576(?:i|p?x?)", value="576p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?720(?:i|p?(?:50|60)?x?)", value="720p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?720(?:p(?:50|60)?x?)", value="720p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?720p?hd", value="720p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?900(?:i|p?x?)", value="900p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?1080i", value="1080i")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?1080p?x?", value="1080p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?1080(?:p(?:50|60)?x?)", value="1080p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?1080p?hd", value="1080p")
    rebulk.regex(r"(?:\d{3,}(?:x|\*))?2160(?:i|p?x?)", value="4K")

    _digits_re = re.compile(r'\d+')

    rebulk.defaults(name="screen_size", validator=seps_surround)
    rebulk.regex(r'\d{3,}-?(?:x|\*)-?\d{3,}',
                 formatter=lambda value: 'x'.join(_digits_re.findall(value)),
                 abbreviations=[dash],
                 tags=['resolution'],
                 conflict_solver=lambda match, other: '__default__' if other.name == 'screen_size' else other)

    rebulk.rules(ScreenSizeOnlyOne)

    return rebulk


class ScreenSizeOnlyOne(Rule):
    """
    Keep a single screen_size pet filepath part.
    """
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for filepart in matches.markers.named('path'):
            screensize = list(reversed(matches.range(filepart.start, filepart.end,
                                                     lambda match: match.name == 'screen_size')))
            if len(screensize) > 1:
                to_remove.extend(screensize[1:])

        return to_remove
