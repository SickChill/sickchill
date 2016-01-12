#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Website property.
"""
from __future__ import unicode_literals

from pkg_resources import resource_stream  # @UnresolvedImport
import regex as re

from rebulk import Rebulk


def website():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(name="website")

    tlds = [l.strip().decode('utf-8')
            for l in resource_stream('guessit', 'tlds-alpha-by-domain.txt').readlines()
            if b'--' not in l][1:]  # All registered domain extension

    safe_tlds = ['com', 'org', 'net']  # For sure a website extension
    safe_subdomains = ['www']  # For sure a website subdomain
    safe_prefix = ['co', 'com', 'org', 'net']  # Those words before a tlds are sure

    rebulk.regex(r'(?:[^a-z0-9]|^)((?:\L<safe_subdomains>\.)+(?:[a-z-]+\.)+(?:\L<tlds>))(?:[^a-z0-9]|$)',
                 safe_subdomains=safe_subdomains, tlds=tlds, children=True)
    rebulk.regex(r'(?:[^a-z0-9]|^)((?:\L<safe_subdomains>\.)*[a-z-]+\.(?:\L<safe_tlds>))(?:[^a-z0-9]|$)',
                 safe_subdomains=safe_subdomains, safe_tlds=safe_tlds, children=True)
    rebulk.regex(
        r'(?:[^a-z0-9]|^)((?:\L<safe_subdomains>\.)*[a-z-]+\.(?:\L<safe_prefix>\.)+(?:\L<tlds>))(?:[^a-z0-9]|$)',
        safe_subdomains=safe_subdomains, safe_prefix=safe_prefix, tlds=tlds, children=True)

    return rebulk
