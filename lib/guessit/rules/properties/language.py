#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
language and subtitle_language properties
"""
# pylint: disable=no-member
import copy

import babelfish

from rebulk.remodule import re
from rebulk import Rebulk, Rule, RemoveMatch, RenameMatch
from ..common.words import iter_words, COMMON_WORDS
from ..common.validators import seps_surround


def language():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()

    rebulk.string(*subtitle_prefixes, name="subtitle_language.prefix", ignore_case=True, private=True,
                  validator=seps_surround)
    rebulk.string(*subtitle_suffixes, name="subtitle_language.suffix", ignore_case=True, private=True,
                  validator=seps_surround)
    rebulk.functional(find_languages, properties={'language': [None]})
    rebulk.rules(SubtitlePrefixLanguageRule, SubtitleSuffixLanguageRule, SubtitleExtensionRule)

    return rebulk


COMMON_WORDS_STRICT = frozenset(['brazil'])

UNDETERMINED = babelfish.Language('und')

SYN = {('und', None): ['unknown', 'inconnu', 'unk', 'un'],
       ('ell', None): ['gr', 'greek'],
       ('spa', None): ['esp', 'español'],
       ('fra', None): ['français', 'vf', 'vff', 'vfi', 'vfq'],
       ('swe', None): ['se'],
       ('por', 'BR'): ['po', 'pb', 'pob', 'br', 'brazilian'],
       ('cat', None): ['català'],
       ('ces', None): ['cz'],
       ('ukr', None): ['ua'],
       ('zho', None): ['cn'],
       ('jpn', None): ['jp'],
       ('hrv', None): ['scr'],
       ('mul', None): ['multi', 'dl']}  # http://scenelingo.wordpress.com/2009/03/24/what-does-dl-mean/


class GuessitConverter(babelfish.LanguageReverseConverter):  # pylint: disable=missing-docstring
    _with_country_regexp = re.compile(r'(.*)\((.*)\)')
    _with_country_regexp2 = re.compile(r'(.*)-(.*)')

    def __init__(self):
        self.guessit_exceptions = {}
        for (alpha3, country), synlist in SYN.items():
            for syn in synlist:
                self.guessit_exceptions[syn.lower()] = (alpha3, country, None)

    @property
    def codes(self):  # pylint: disable=missing-docstring
        return (babelfish.language_converters['alpha3b'].codes |
                babelfish.language_converters['alpha2'].codes |
                babelfish.language_converters['name'].codes |
                babelfish.language_converters['opensubtitles'].codes |
                babelfish.country_converters['name'].codes |
                frozenset(self.guessit_exceptions.keys()))

    def convert(self, alpha3, country=None, script=None):
        return str(babelfish.Language(alpha3, country, script))

    def reverse(self, name):
        with_country = (GuessitConverter._with_country_regexp.match(name) or
                        GuessitConverter._with_country_regexp2.match(name))

        name = name.lower()
        if with_country:
            lang = babelfish.Language.fromguessit(with_country.group(1).strip())
            lang.country = babelfish.Country.fromguessit(with_country.group(2).strip())
            return lang.alpha3, lang.country.alpha2 if lang.country else None, lang.script or None

        # exceptions come first, as they need to override a potential match
        # with any of the other guessers
        try:
            return self.guessit_exceptions[name]
        except KeyError:
            pass

        for conv in [babelfish.Language,
                     babelfish.Language.fromalpha3b,
                     babelfish.Language.fromalpha2,
                     babelfish.Language.fromname,
                     babelfish.Language.fromopensubtitles]:
            try:
                reverse = conv(name)
                return reverse.alpha3, reverse.country, reverse.script
            except (ValueError, babelfish.LanguageReverseError):
                pass

        raise babelfish.LanguageReverseError(name)


babelfish.language_converters['guessit'] = GuessitConverter()

subtitle_both = ['sub', 'subs', 'subbed', 'custom subbed', 'custom subs', 'custom sub', 'customsubbed', 'customsubs',
                 'customsub']
subtitle_prefixes = subtitle_both + ['st', 'vost', 'subforced', 'fansub', 'hardsub']
subtitle_suffixes = subtitle_both + ['subforced', 'fansub', 'hardsub']
lang_prefixes = ['true']

all_lang_prefixes_suffixes = subtitle_prefixes + subtitle_suffixes + lang_prefixes


def find_languages(string, context=None):
    """Find languages in the string

    :return: list of tuple (property, Language, lang_word, word)
    """
    allowed_languages = context.get('allowed_languages')
    common_words = COMMON_WORDS_STRICT if allowed_languages else COMMON_WORDS

    matches = []
    for word_match in iter_words(string):
        word = word_match.value
        start, end = word_match.span

        lang_word = word.lower()
        key = 'language'
        for prefix in subtitle_prefixes:
            if lang_word.startswith(prefix):
                lang_word = lang_word[len(prefix):]
                key = 'subtitle_language'
        for suffix in subtitle_suffixes:
            if lang_word.endswith(suffix):
                lang_word = lang_word[:len(lang_word) - len(suffix)]
                key = 'subtitle_language'
        for prefix in lang_prefixes:
            if lang_word.startswith(prefix):
                lang_word = lang_word[len(prefix):]
        if lang_word not in common_words and word.lower() not in common_words:
            try:
                lang = babelfish.Language.fromguessit(lang_word)
                match = (start, end, {'name': key, 'value': lang})
                if allowed_languages:
                    if lang.name.lower() in allowed_languages \
                            or lang.alpha2.lower() in allowed_languages \
                            or lang.alpha3.lower() in allowed_languages:
                        matches.append(match)
                # Keep language with alpha2 equivalent. Others are probably
                # uncommon languages.
                elif lang == 'mul' or hasattr(lang, 'alpha2'):
                    matches.append(match)
            except babelfish.Error:
                pass
    return matches


class SubtitlePrefixLanguageRule(Rule):
    """
    Convert language guess as subtitle_language if previous match is a subtitle language prefix
    """
    consequence = RemoveMatch

    properties = {'subtitle_language': [None]}

    def when(self, matches, context):
        to_rename = []
        to_remove = matches.named('subtitle_language.prefix')
        for lang in matches.named('language'):
            prefix = matches.previous(lang, lambda match: match.name == 'subtitle_language.prefix', 0)
            if not prefix:
                group_marker = matches.markers.at_match(lang, lambda marker: marker.name == 'group', 0)
                if group_marker:
                    # Find prefix if placed just before the group
                    prefix = matches.previous(group_marker, lambda match: match.name == 'subtitle_language.prefix',
                                              0)
                    if not prefix:
                        # Find prefix if placed before in the group
                        prefix = matches.range(group_marker.start, lang.start,
                                               lambda match: match.name == 'subtitle_language.prefix', 0)
            if prefix:
                to_rename.append((prefix, lang))
                if prefix in to_remove:
                    to_remove.remove(prefix)
        return to_rename, to_remove

    def then(self, matches, when_response, context):
        to_rename, to_remove = when_response
        super(SubtitlePrefixLanguageRule, self).then(matches, to_remove, context)
        for prefix, match in to_rename:
            # Remove suffix equivalent of  prefix.
            suffix = copy.copy(prefix)
            suffix.name = 'subtitle_language.suffix'
            if suffix in matches:
                matches.remove(suffix)
            matches.remove(match)
            match.name = 'subtitle_language'
            matches.append(match)


class SubtitleSuffixLanguageRule(Rule):
    """
    Convert language guess as subtitle_language if next match is a subtitle language suffix
    """
    dependency = SubtitlePrefixLanguageRule
    consequence = RemoveMatch

    properties = {'subtitle_language': [None]}

    def when(self, matches, context):
        to_append = []
        to_remove = matches.named('subtitle_language.suffix')
        for lang in matches.named('language'):
            suffix = matches.next(lang, lambda match: match.name == 'subtitle_language.suffix', 0)
            if suffix:
                to_append.append(lang)
                if suffix in to_remove:
                    to_remove.remove(suffix)
        return to_append, to_remove

    def then(self, matches, when_response, context):
        to_rename, to_remove = when_response
        super(SubtitleSuffixLanguageRule, self).then(matches, to_remove, context)
        for match in to_rename:
            matches.remove(match)
            match.name = 'subtitle_language'
            matches.append(match)


class SubtitleExtensionRule(Rule):
    """
    Convert language guess as subtitle_language if next match is a subtitle extension
    """
    consequence = RenameMatch('subtitle_language')

    properties = {'subtitle_language': [None]}

    def when(self, matches, context):
        subtitle_extension = matches.named('container',
                                           lambda match: 'extension' in match.tags and 'subtitle' in match.tags,
                                           0)
        if subtitle_extension:
            subtitle_lang = matches.previous(subtitle_extension, lambda match: match.name == 'language', 0)
            if subtitle_lang:
                return subtitle_lang
