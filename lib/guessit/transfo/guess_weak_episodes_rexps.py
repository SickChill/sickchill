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

import re
from guessit.patterns.list import list_parser, all_separators_re

from guessit.plugins.transformers import Transformer

from guessit.matcher import GuessFinder
from guessit.patterns import sep, build_or_pattern
from guessit.containers import PropertiesContainer
from guessit.patterns.numeral import numeral, parse_numeral
from guessit.date import valid_year


class GuessWeakEpisodesRexps(Transformer):
    def __init__(self):
        Transformer.__init__(self, 15)

        of_separators = ['of', 'sur', '/', '\\']
        of_separators_re = re.compile(build_or_pattern(of_separators, escape=True), re.IGNORECASE)

        self.container = PropertiesContainer(enhance=False, canonical_from_pattern=False, remove_duplicates=True)

        episode_words = ['episodes?']

        def episode_list_parser(value):
            return list_parser(value, 'episodeList')

        def season_episode_parser(episode_number):
            epnum = parse_numeral(episode_number)
            if not valid_year(epnum):
                if epnum > 100:
                    season, epnum = epnum // 100, epnum % 100
                    # episodes which have a season > 50 are most likely errors
                    # (Simpson is at 25!)
                    if season > 50:
                        return None
                    return {'season': season, 'episodeNumber': epnum}
                else:
                    return epnum

        self.container.register_property(['episodeNumber', 'season'], '[0-9]{2,4}', confidence=0.6, formatter=season_episode_parser, disabler=lambda options: options.get('episode_prefer_number') if options else False)
        self.container.register_property(['episodeNumber', 'season'], '[0-9]{4}', confidence=0.6, formatter=season_episode_parser)
        self.container.register_property(None, '(' + build_or_pattern(episode_words) + sep + '?(?P<episodeNumber>' + numeral + '))[^0-9]', confidence=0.4, formatter=parse_numeral)
        self.container.register_property(None, r'(?P<episodeNumber>' + numeral + ')' + sep + '?' + of_separators_re.pattern + sep + '?(?P<episodeCount>' + numeral +')', confidence=0.6, formatter=parse_numeral)
        self.container.register_property('episodeNumber', '[^0-9](\d{2,3}' + '(?:' + sep + '?' + all_separators_re.pattern + sep + '?' + '\d{2,3}' + ')*)', confidence=0.4, formatter=episode_list_parser, disabler=lambda options: not options.get('episode_prefer_number') if options else True)
        self.container.register_property('episodeNumber', r'^' + sep + '?(\d{2,3}' + '(?:' + sep + '?' + all_separators_re.pattern + sep + '?' + '\d{2,3}' + ')*)' + sep, confidence=0.4, formatter=episode_list_parser, disabler=lambda options: not options.get('episode_prefer_number') if options else True)
        self.container.register_property('episodeNumber', sep + r'(\d{2,3}' + '(?:' + sep + '?' + all_separators_re.pattern + sep + '?' + '\d{2,3}' + ')*)' + sep + '?$', confidence=0.4, formatter=episode_list_parser, disabler=lambda options: not options.get('episode_prefer_number') if options else True)

    def supported_properties(self):
        return self.container.get_supported_properties()

    def guess_weak_episodes_rexps(self, string, node=None, options=None):
        properties = self.container.find_properties(string, node, options)
        guess = self.container.as_guess(properties, string)

        if node and guess:
            if 'episodeNumber' in guess and 'season' in guess:
                existing_guesses = list(filter(lambda x: 'season' in x and 'episodeNumber' in x, node.group_node().guesses))
                if existing_guesses:
                    return None
            elif 'episodeNumber' in guess:
                # If we only have episodeNumber in the guess, and another node contains both season and episodeNumber
                # keep only the second.
                safe_guesses = list(filter(lambda x: 'season' in x and 'episodeNumber' in x, node.group_node().guesses))
                if safe_guesses:
                    return None
                else:
                    # If we have other nodes containing episodeNumber, create an episodeList.
                    existing_guesses = list(filter(lambda x: 'season' not in x and 'episodeNumber' in x, node.group_node().guesses))
                    for existing_guess in existing_guesses:
                        if 'episodeList' not in existing_guess:
                            existing_guess['episodeList'] = [existing_guess['episodeNumber']]
                        existing_guess['episodeList'].append(guess['episodeNumber'])
                        existing_guess['episodeList'].sort()
                        if existing_guess['episodeNumber'] > guess['episodeNumber']:
                            existing_guess.set_confidence('episodeNumber', 0)
                        else:
                            guess.set_confidence('episodeNumber', 0)
                        guess['episodeList'] = list(existing_guess['episodeList'])

        return guess

    def should_process(self, mtree, options=None):
        return mtree.guess.get('type', '').startswith('episode')

    def process(self, mtree, options=None):
        GuessFinder(self.guess_weak_episodes_rexps, 0.6, self.log, options).process_nodes(mtree.unidentified_leaves())
