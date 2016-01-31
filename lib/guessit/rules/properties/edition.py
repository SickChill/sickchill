#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
edition property
"""
from rebulk.remodule import re

from rebulk import Rebulk
from ..common import dash
from ..common.validators import seps_surround


def edition():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name='edition', validator=seps_surround)

    rebulk.regex('collector', 'collector-edition', 'edition-collector', value='Collector Edition')
    rebulk.regex('special-edition', 'edition-special', value='Special Edition',
                 conflict_solver=lambda match, other: other
                 if other.name == 'episode_details' and other.value == 'Special'
                 else '__default__')
    rebulk.regex('criterion-edition', 'edition-criterion', value='Criterion Edition')
    rebulk.regex('deluxe', 'deluxe-edition', 'edition-deluxe', value='Deluxe Edition')
    rebulk.regex('director\'?s?-cut', 'director\'?s?-cut-edition', 'edition-director\'?s?-cut', value='Director\'s cut')

    return rebulk
