#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
#
# GuessIt is free software; you can redistribute it and/or modify it under
# the terms of the Lesser GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# GuessIt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import defaultdict
from unittest import TestCase, TestLoader
import logging
import os
import sys
from os.path import *

import babelfish
import yaml


def currentPath():
    """Returns the path in which the calling file is located."""
    return dirname(join(os.getcwd(), sys._getframe(1).f_globals['__file__']))


def addImportPath(path):
    """Function that adds the specified path to the import path. The path can be
    absolute or relative to the calling file."""
    importPath = abspath(join(currentPath(), path))
    sys.path = [importPath] + sys.path

log = logging.getLogger(__name__)

from guessit.options import get_opts
from guessit import base_text_type
from guessit import *
from guessit.matcher import *
from guessit.fileutils import *
import guessit


def allTests(testClass):
    return TestLoader().loadTestsFromTestCase(testClass)


class TestGuessit(TestCase):

    def checkMinimumFieldsCorrect(self, filename, filetype=None, remove_type=True,
                                  exclude_files=None):
        groundTruth = yaml.load(load_file_in_same_dir(__file__, filename))

        def guess_func(string, options=None):
            return guess_file_info(string, options=options, type=filetype)

        return self.checkFields(groundTruth, guess_func, remove_type, exclude_files)

    def checkFields(self, groundTruth, guess_func, remove_type=True,
                    exclude_files=None):
        total = 0
        exclude_files = exclude_files or []

        fails = defaultdict(list)
        additionals = defaultdict(list)

        for filename, required_fields in groundTruth.items():
            filename = u(filename)
            if filename in exclude_files:
                continue

            log.debug('\n' + '-' * 120)
            log.info('Guessing information for file: %s' % filename)

            options = required_fields.pop('options') if 'options' in required_fields else None

            try:
                found = guess_func(filename, options)
            except Exception as e:
                fails[filename].append("An exception has occured in %s: %s" % (filename, e))
                log.exception("An exception has occured in %s: %s" % (filename, e))
                continue

            total += 1

            # no need for these in the unittests
            if remove_type:
                try:
                    del found['type']
                except:
                    pass
            for prop in ('container', 'mimetype', 'unidentified'):
                if prop in found:
                    del found[prop]

            # props which are list of just 1 elem should be opened for easier writing of the tests
            for prop in ('language', 'subtitleLanguage', 'other', 'episodeDetails', 'unidentified'):
                value = found.get(prop, None)
                if isinstance(value, list) and len(value) == 1:
                    found[prop] = value[0]

            # look for missing properties
            for prop, value in required_fields.items():
                if prop not in found:
                    log.debug("Prop '%s' not found in: %s" % (prop, filename))
                    fails[filename].append("'%s' not found in: %s" % (prop, filename))
                    continue

                # if both properties are strings, do a case-insensitive comparison
                if (isinstance(value, base_text_type) and
                    isinstance(found[prop], base_text_type)):
                    if value.lower() != found[prop].lower():
                        log.debug("Wrong prop value [str] for '%s': expected = '%s' - received = '%s'" % (prop, u(value), u(found[prop])))
                        fails[filename].append("'%s': expected = '%s' - received = '%s'" % (prop, u(value), u(found[prop])))

                elif isinstance(value, list) and isinstance(found[prop], list):
                    if found[prop] and isinstance(found[prop][0], babelfish.Language):
                        # list of languages
                        s1 = set(Language.fromguessit(s) for s in value)
                        s2 = set(found[prop])
                    else:
                        # by default we assume list of strings and do a case-insensitive
                        # comparison on their elements
                        s1 = set(u(s).lower() for s in value)
                        s2 = set(u(s).lower() for s in found[prop])

                    if s1 != s2:
                        log.debug("Wrong prop value [list] for '%s': expected = '%s' - received = '%s'" % (prop, u(value), u(found[prop])))
                        fails[filename].append("'%s': expected = '%s' - received = '%s'" % (prop, u(value), u(found[prop])))

                elif isinstance(found[prop], babelfish.Language):
                    try:
                        if babelfish.Language.fromguessit(value) != found[prop]:
                            raise ValueError
                    except:
                        log.debug("Wrong prop value [Language] for '%s': expected = '%s' - received = '%s'" % (prop, u(value), u(found[prop])))
                        fails[filename].append("'%s': expected = '%s' - received = '%s'" % (prop, u(value), u(found[prop])))

                elif isinstance(found[prop], babelfish.Country):
                    try:
                        if babelfish.Country.fromguessit(value) != found[prop]:
                            raise ValueError
                    except:
                        log.debug("Wrong prop value [Country] for '%s': expected = '%s' - received = '%s'" % (prop, u(value), u(found[prop])))
                        fails[filename].append("'%s': expected = '%s' - received = '%s'" % (prop, u(value), u(found[prop])))


                # otherwise, just compare their values directly
                else:
                    if found[prop] != value:
                        log.debug("Wrong prop value for '%s': expected = '%s' [%s] - received = '%s' [%s]" % (prop, u(value), type(value), u(found[prop]), type(found[prop])))
                        fails[filename].append("'%s': expected = '%s' [%s] - received = '%s' [%s]" % (prop, u(value), type(value), u(found[prop]), type(found[prop])))

            # look for additional properties
            for prop, value in found.items():
                if prop not in required_fields:
                    log.debug("Found additional info for prop = '%s': '%s'" % (prop, u(value)))
                    additionals[filename].append("'%s': '%s'" % (prop, u(value)))

        correct = total - len(fails)
        log.info('SUMMARY: Guessed correctly %d out of %d filenames' % (correct, total))

        for failed_entry, failed_properties in fails.items():
            log.error('---- ' + failed_entry + ' ----')
            for failed_property in failed_properties:
                log.error("FAILED: " + failed_property)

        for additional_entry, additional_properties in additionals.items():
            log.warning('---- ' + additional_entry + ' ----')
            for additional_property in additional_properties:
                log.warning("ADDITIONAL: " + additional_property)

        assert correct == total, 'Correct: %d < Total: %d' % (correct, total)
