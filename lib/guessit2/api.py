#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API functions that can be used by external software
"""
from __future__ import unicode_literals
try:
    from collections import OrderedDict
except ImportError:  # pragma: no-cover
    from ordereddict import OrderedDict  # pylint:disable=import-error

import six

from rebulk.introspector import introspect

from .rules import rebulk_builder
from .options import parse_options


def guessit(string, options=None):
    """
    Retrieves all matches from string as a dict
    :param string: the filename or release name
    :type string: str
    :param options: the filename or release name
    :type options: str|dict
    :return:
    :rtype:
    """
    return default_api.guessit(string, options)


def properties(options=None):
    """
    Retrieves all properties with possible values that can be guessed
    :param options:
    :type options:
    :return:
    :rtype:
    """
    return default_api.properties(options)


class GuessItApi(object):
    """
    An api class that can be configured with custom Rebulk configuration.
    """

    def __init__(self, rebulk):
        """
        :param rebulk: Rebulk instance to use.
        :type rebulk: Rebulk
        :return:
        :rtype:
        """
        self.rebulk = rebulk

    def guessit(self, string, options=None):
        """
        Retrieves all matches from string as a dict
        :param string: the filename or release name
        :type string: str
        :param options: the filename or release name
        :type options: str|dict
        :return:
        :rtype:
        """
        if not isinstance(string, six.text_type):
            raise TypeError("guessit input must be %s." % six.text_type.__name__)
        options = parse_options(options)
        return self.rebulk.matches(string, options).to_dict(options.get('advanced', False),
                                                            options.get('implicit', False))

    def properties(self, options=None):
        """
        Grab properties and values that can be generated.
        :param options:
        :type options:
        :return:
        :rtype:
        """
        unordered = introspect(self.rebulk, options).properties
        ordered = OrderedDict()
        for k in sorted(unordered.keys(), key=six.text_type):
            ordered[k] = list(sorted(unordered[k], key=six.text_type))
        return ordered


default_api = GuessItApi(rebulk_builder())
