#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Common module
"""
from __future__ import unicode_literals

seps = r' [](){}+*|=§-_~#/\.,;:'  # list of tags/words separators

title_seps = r'-+/\|'  # separators for title

dash = (r'-', r'[\W_]')  # abbreviation used by many rebulk objects.
alt_dash = (r'@', r'[\W_]')  # abbreviation used by many rebulk objects.
