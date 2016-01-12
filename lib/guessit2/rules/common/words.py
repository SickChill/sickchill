#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Words utils
"""
from __future__ import unicode_literals

import regex as re

_words_rexp = re.compile(r'\w+', re.UNICODE)


def iter_words(string):
    """
    Iterate on all words in a string
    :param string:
    :type string:
    :return:
    :rtype: iterable[str]
    """
    return _words_rexp.finditer(string.replace('_', ' '))

# list of common words which could be interpreted as properties, but which
# are far too common to be able to say they represent a property in the
# middle of a string (where they most likely carry their commmon meaning)
COMMON_WORDS = frozenset([
    # english words
    'is', 'it', 'am', 'mad', 'men', 'man', 'run', 'sin', 'st', 'to',
    'no', 'non', 'war', 'min', 'new', 'car', 'day', 'bad', 'bat', 'fan',
    'fry', 'cop', 'zen', 'gay', 'fat', 'one', 'cherokee', 'got', 'an', 'as',
    'cat', 'her', 'be', 'hat', 'sun', 'may', 'my', 'mr', 'rum', 'pi', 'bb',
    'bt', 'tv', 'aw', 'by', 'md', 'mp', 'cd', 'lt', 'gt', 'in', 'ad', 'ice',
    'ay', 'at', 'star', 'so', 'he',
    # french words
    'bas', 'de', 'le', 'son', 'ne', 'ca', 'ce', 'et', 'que',
    'mal', 'est', 'vol', 'or', 'mon', 'se', 'je', 'tu', 'me',
    'ne', 'ma', 'va', 'au',
    # japanese words,
    'wa', 'ga', 'ao',
    # spanish words
    'la', 'el', 'del', 'por', 'mar', 'al',
    # other
    'ind', 'arw', 'ts', 'ii', 'bin', 'chan', 'ss', 'san', 'oss', 'iii',
    'vi', 'ben', 'da', 'lt', 'ch', 'sr', 'ps', 'cx', 'vo',
    # new from babelfish
    'mkv', 'avi', 'dmd', 'the', 'dis', 'cut', 'stv', 'des', 'dia', 'and',
    'cab', 'sub', 'mia', 'rim', 'las', 'une', 'par', 'srt', 'ano', 'toy',
    'job', 'gag', 'reel', 'www', 'for', 'ayu', 'csi', 'ren', 'moi', 'sur',
    'fer', 'fun', 'two', 'big', 'psy', 'air',
    # movie title
    'brazil',
    # release groups
    'bs',  # Bosnian
    'kz',
    # countries
    'gt', 'lt', 'im',
    # part/pt
    'pt',
    # screener
    'scr'
])
