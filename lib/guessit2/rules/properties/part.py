#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
part property
"""
from __future__ import unicode_literals

import regex as re

from rebulk import Rebulk
from ..common import dash
from ..common.validators import seps_surround
from ..common.numeral import numeral, parse_numeral


def part():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash], validator={'__parent__': seps_surround})

    prefixes = ['pt', 'part']

    rebulk.regex(r'\L<prefixes>-?(' + numeral + r')', prefixes=prefixes,
                 name='part', validate_all=True, private_parent=True, children=True, formatter=parse_numeral)

    return rebulk
