#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
video_codec and video_profile property
"""
from rebulk.remodule import re

from rebulk import Rebulk, Rule, RemoveMatch

from guessit.rules.common.validators import seps_after, seps_before
from ..common import dash
from ..common.validators import seps_surround


def video_codec():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name="video_codec")

    rebulk.regex(r"Rv\d{2}", value="Real")
    rebulk.regex("Mpeg2", value="Mpeg2")
    rebulk.regex("DVDivX", "DivX", value="DivX")
    rebulk.regex("XviD", value="XviD")
    rebulk.regex("[hx]-?264(?:-?AVC(HD)?)?", "MPEG-?4(?:-?AVC(HD)?)", "AVCHD", value="h264")
    rebulk.regex("[hx]-?265(?:-?HEVC)?", "HEVC", value="h265")

    # http://blog.mediacoderhq.com/h264-profiles-and-levels/
    # http://fr.wikipedia.org/wiki/H.264
    rebulk.defaults(name="video_profile", validator=seps_surround)

    rebulk.regex('10.?bit', 'Hi10P', value='10bit')
    rebulk.regex('8.?bit', value='8bit')

    rebulk.string('BP', value='BP', tags='video_profile.rule')
    rebulk.string('XP', 'EP', value='XP', tags='video_profile.rule')
    rebulk.string('MP', value='MP', tags='video_profile.rule')
    rebulk.string('HP', 'HiP', value='HP', tags='video_profile.rule')
    rebulk.regex('Hi422P', value='Hi422P', tags='video_profile.rule')
    rebulk.regex('Hi444PP', value='Hi444PP', tags='video_profile.rule')

    rebulk.string('DXVA', value='DXVA', name='video_api')

    rebulk.rules(ValidateVideoCodec, VideoProfileRule)

    return rebulk


class ValidateVideoCodec(Rule):
    """
    Validate video_codec with format property or separated
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for codec in matches.named('video_codec'):
            if not seps_before(codec) and \
                    not matches.at_index(codec.start - 1, lambda match: match.name == 'format'):
                ret.append(codec)
                continue
            if not seps_after(codec):
                ret.append(codec)
                continue
        return ret


class VideoProfileRule(Rule):
    """
    Rule to validate video_profile
    """
    consequence = RemoveMatch

    def when(self, matches, context):
        profile_list = matches.named('video_profile', lambda match: 'video_profile.rule' in match.tags)
        ret = []
        for profile in profile_list:
            codec = matches.previous(profile, lambda match: match.name == 'video_codec')
            if not codec:
                codec = matches.next(profile, lambda match: match.name == 'video_codec')
            if not codec:
                ret.append(profile)
        return ret
