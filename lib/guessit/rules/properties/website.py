#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Website property.
"""
from pkg_resources import resource_stream  # @UnresolvedImport
from rebulk.remodule import re

from rebulk import Rebulk, Rule, RemoveMatch
from ...reutils import build_or_pattern


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

    rebulk.regex(r'(?:[^a-z0-9]|^)((?:'+build_or_pattern(safe_subdomains) +
                 r'\.)+(?:[a-z-]+\.)+(?:'+build_or_pattern(tlds) +
                 r'))(?:[^a-z0-9]|$)',
                 children=True)
    rebulk.regex(r'(?:[^a-z0-9]|^)((?:'+build_or_pattern(safe_subdomains) +
                 r'\.)*[a-z-]+\.(?:'+build_or_pattern(safe_tlds) +
                 r'))(?:[^a-z0-9]|$)',
                 safe_subdomains=safe_subdomains, safe_tlds=safe_tlds, children=True)
    rebulk.regex(r'(?:[^a-z0-9]|^)((?:'+build_or_pattern(safe_subdomains) +
                 r'\.)*[a-z-]+\.(?:'+build_or_pattern(safe_prefix) +
                 r'\.)+(?:'+build_or_pattern(tlds) +
                 r'))(?:[^a-z0-9]|$)',
                 safe_subdomains=safe_subdomains, safe_prefix=safe_prefix, tlds=tlds, children=True)

    class PreferTitleOverWebsite(Rule):
        """
        If found match is more likely a title, remove website.
        """
        consequence = RemoveMatch

        @staticmethod
        def valid_followers(match):
            """
            Validator for next website matches
            """
            return any(name in ['season', 'episode', 'year'] for name in match.names)

        def when(self, matches, context):
            to_remove = []
            for website_match in matches.named('website'):
                suffix = matches.next(website_match, PreferTitleOverWebsite.valid_followers, 0)
                if suffix:
                    to_remove.append(website_match)
            return to_remove

    rebulk.rules(PreferTitleOverWebsite)

    return rebulk
