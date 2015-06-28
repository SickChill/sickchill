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

from guessit.plugins.transformers import Transformer
from guessit.matcher import GuessFinder
from guessit.patterns import sep, build_or_pattern
from guessit.containers import PropertiesContainer, WeakValidator, NoValidator, ChainedValidator, DefaultValidator, \
    FormatterValidator
from guessit.patterns.numeral import numeral, digital_numeral, parse_numeral


class GuessEpisodesRexps(Transformer):
    def __init__(self):
        Transformer.__init__(self, 20)

        range_separators = ['-', 'to', 'a']
        discrete_separators = ['&', 'and', 'et']
        of_separators = ['of', 'sur', '/', '\\']

        season_words = ['seasons?', 'saisons?', 'series?']
        episode_words = ['episodes?']

        season_markers = ['s']
        episode_markers = ['e', 'ep']

        discrete_sep = sep
        for range_separator in range_separators:
            discrete_sep = discrete_sep.replace(range_separator, '')
        discrete_separators.append(discrete_sep)
        all_separators = list(range_separators)
        all_separators.extend(discrete_separators)

        self.container = PropertiesContainer(enhance=False, canonical_from_pattern=False)

        range_separators_re = re.compile(build_or_pattern(range_separators), re.IGNORECASE)
        discrete_separators_re = re.compile(build_or_pattern(discrete_separators), re.IGNORECASE)
        all_separators_re = re.compile(build_or_pattern(all_separators), re.IGNORECASE)
        of_separators_re = re.compile(build_or_pattern(of_separators, escape=True), re.IGNORECASE)

        season_words_re = re.compile(build_or_pattern(season_words), re.IGNORECASE)
        episode_words_re = re.compile(build_or_pattern(episode_words), re.IGNORECASE)

        season_markers_re = re.compile(build_or_pattern(season_markers), re.IGNORECASE)
        episode_markers_re = re.compile(build_or_pattern(episode_markers), re.IGNORECASE)

        def list_parser(value, property_list_name, discrete_separators_re=discrete_separators_re, range_separators_re=range_separators_re, allow_discrete=False, fill_gaps=False):
            discrete_elements = filter(lambda x: x != '', discrete_separators_re.split(value))
            discrete_elements = [x.strip() for x in discrete_elements]

            proper_discrete_elements = []
            i = 0
            while i < len(discrete_elements):
                if i < len(discrete_elements) - 2 and range_separators_re.match(discrete_elements[i+1]):
                    proper_discrete_elements.append(discrete_elements[i] + discrete_elements[i+1] + discrete_elements[i+2])
                    i += 3
                else:
                    match = range_separators_re.search(discrete_elements[i])
                    if match and match.start() == 0:
                        proper_discrete_elements[i - 1] += discrete_elements[i]
                    elif match and match.end() == len(discrete_elements[i]):
                        proper_discrete_elements.append(discrete_elements[i] + discrete_elements[i + 1])
                    else:
                        proper_discrete_elements.append(discrete_elements[i])
                    i += 1

            discrete_elements = proper_discrete_elements

            ret = []

            for discrete_element in discrete_elements:
                range_values = filter(lambda x: x != '', range_separators_re.split(discrete_element))
                range_values = [x.strip() for x in range_values]
                if len(range_values) > 1:
                    for x in range(0, len(range_values) - 1):
                        start_range_ep = parse_numeral(range_values[x])
                        end_range_ep = parse_numeral(range_values[x+1])
                        for range_ep in range(start_range_ep, end_range_ep + 1):
                            if range_ep not in ret:
                                ret.append(range_ep)
                else:
                    discrete_value = parse_numeral(discrete_element)
                    if discrete_value not in ret:
                        ret.append(discrete_value)

            if len(ret) > 1:
                if not allow_discrete:
                    valid_ret = list()
                    # replace discrete elements by ranges
                    valid_ret.append(ret[0])
                    for i in range(0, len(ret) - 1):
                        previous = valid_ret[len(valid_ret) - 1]
                        if ret[i+1] < previous:
                            pass
                        else:
                            valid_ret.append(ret[i+1])
                    ret = valid_ret
                if fill_gaps:
                    ret = list(range(min(ret), max(ret) + 1))
                if len(ret) > 1:
                    return {None: ret[0], property_list_name: ret}
            if len(ret) > 0:
                return ret[0]
            return None

        def episode_parser_x(value):
            return list_parser(value, 'episodeList', discrete_separators_re=re.compile('x', re.IGNORECASE))

        def episode_parser_e(value):
            return list_parser(value, 'episodeList', discrete_separators_re=re.compile('e', re.IGNORECASE), fill_gaps=True)

        def episode_parser(value):
            return list_parser(value, 'episodeList')

        def season_parser(value):
            return list_parser(value, 'seasonList')

        class ResolutionCollisionValidator(object):
            @staticmethod
            def validate(prop, string, node, match, entry_start, entry_end):
                return len(match.group(2)) < 3 # limit

        self.container.register_property(None, r'(' + season_words_re.pattern + sep + '?(?P<season>' + numeral + ')' + sep + '?' + season_words_re.pattern + '?)', confidence=1.0, formatter=parse_numeral)
        self.container.register_property(None, r'(' + season_words_re.pattern + sep + '?(?P<season>' + digital_numeral + '(?:' + sep + '?' + all_separators_re.pattern + sep + '?' + digital_numeral + ')*)' + sep + '?' + season_words_re.pattern + '?)' + sep, confidence=1.0, formatter={None: parse_numeral, 'season': season_parser}, validator=ChainedValidator(DefaultValidator(), FormatterValidator('season', lambda x: len(x) > 1 if hasattr(x, '__len__') else False)))

        self.container.register_property(None, r'(' + season_markers_re.pattern + '(?P<season>' + digital_numeral + ')[^0-9]?' + sep + '?(?P<episodeNumber>(?:e' + digital_numeral + '(?:' + sep + '?[e-]' + digital_numeral + ')*)))', confidence=1.0, formatter={None: parse_numeral, 'episodeNumber': episode_parser_e, 'season': season_parser}, validator=NoValidator())
        # self.container.register_property(None, r'[^0-9]((?P<season>' + digital_numeral + ')[^0-9 .-]?-?(?P<episodeNumber>(?:x' + digital_numeral + '(?:' + sep + '?[x-]' + digital_numeral + ')*)))', confidence=1.0, formatter={None: parse_numeral, 'episodeNumber': episode_parser_x, 'season': season_parser}, validator=ChainedValidator(DefaultValidator(), ResolutionCollisionValidator()))
        self.container.register_property(None, sep + r'((?P<season>' + digital_numeral + ')' + sep + '' + '(?P<episodeNumber>(?:x' + sep + digital_numeral + '(?:' + sep + '[x-]' + digital_numeral + ')*)))', confidence=1.0, formatter={None: parse_numeral, 'episodeNumber': episode_parser_x, 'season': season_parser}, validator=ChainedValidator(DefaultValidator(), ResolutionCollisionValidator()))
        self.container.register_property(None, r'((?P<season>' + digital_numeral + ')' + '(?P<episodeNumber>(?:x' + digital_numeral + '(?:[x-]' + digital_numeral + ')*)))', confidence=1.0, formatter={None: parse_numeral, 'episodeNumber': episode_parser_x, 'season': season_parser}, validator=ChainedValidator(DefaultValidator(), ResolutionCollisionValidator()))
        self.container.register_property(None, r'(' + season_markers_re.pattern + '(?P<season>' + digital_numeral + '(?:' + sep + '?' + all_separators_re.pattern + sep + '?' + digital_numeral + ')*))', confidence=0.6, formatter={None: parse_numeral, 'season': season_parser}, validator=NoValidator())

        self.container.register_property(None, r'((?P<episodeNumber>' + digital_numeral + ')' + sep + '?v(?P<version>\d+))', confidence=0.6, formatter=parse_numeral)
        self.container.register_property(None, r'(ep' + sep + r'?(?P<episodeNumber>' + digital_numeral + ')' + sep + '?)', confidence=0.7, formatter=parse_numeral)
        self.container.register_property(None, r'(ep' + sep + r'?(?P<episodeNumber>' + digital_numeral + ')' + sep + '?v(?P<version>\d+))', confidence=0.7, formatter=parse_numeral)


        self.container.register_property(None, r'(' + episode_markers_re.pattern + '(?P<episodeNumber>' + digital_numeral + '(?:' + sep + '?' + all_separators_re.pattern + sep + '?' + digital_numeral + ')*))', confidence=0.6, formatter={None: parse_numeral, 'episodeNumber': episode_parser})
        self.container.register_property(None, r'(' + episode_words_re.pattern + sep + '?(?P<episodeNumber>' + digital_numeral + '(?:' + sep + '?' + all_separators_re.pattern + sep + '?' + digital_numeral + ')*)' + sep + '?' + episode_words_re.pattern + '?)', confidence=0.8, formatter={None: parse_numeral, 'episodeNumber': episode_parser})

        self.container.register_property(None, r'(' + episode_markers_re.pattern + '(?P<episodeNumber>' + digital_numeral + ')'  + sep + '?v(?P<version>\d+))', confidence=0.6, formatter={None: parse_numeral, 'episodeNumber': episode_parser})
        self.container.register_property(None, r'(' + episode_words_re.pattern + sep + '?(?P<episodeNumber>' + digital_numeral + ')'  + sep + '?v(?P<version>\d+))', confidence=0.8, formatter={None: parse_numeral, 'episodeNumber': episode_parser})


        self.container.register_property('episodeNumber', r'^ ?(\d{2})' + sep, confidence=0.4, formatter=parse_numeral)
        self.container.register_property('episodeNumber', r'^ ?(\d{2})' + sep, confidence=0.4, formatter=parse_numeral)
        self.container.register_property('episodeNumber', r'^ ?0(\d{1,2})' + sep, confidence=0.4, formatter=parse_numeral)
        self.container.register_property('episodeNumber', sep + r'(\d{2}) ?$', confidence=0.4, formatter=parse_numeral)
        self.container.register_property('episodeNumber', sep + r'0(\d{1,2}) ?$', confidence=0.4, formatter=parse_numeral)

        self.container.register_property(None, r'((?P<episodeNumber>' + numeral + ')' + sep + '?' + of_separators_re.pattern + sep + '?(?P<episodeCount>' + numeral + ')(?:' + sep + '?(?:episodes?|eps?))?)', confidence=0.7, formatter=parse_numeral)
        self.container.register_property(None, r'((?:episodes?|eps?)' + sep + '?(?P<episodeNumber>' + numeral + ')' + sep + '?' + of_separators_re.pattern + sep + '?(?P<episodeCount>' + numeral + '))', confidence=0.7, formatter=parse_numeral)
        self.container.register_property(None, r'((?:seasons?|saisons?|s)' + sep + '?(?P<season>' + numeral + ')' + sep + '?' + of_separators_re.pattern + sep + '?(?P<seasonCount>' + numeral + '))', confidence=0.7, formatter=parse_numeral)
        self.container.register_property(None, r'((?P<season>' + numeral + ')' + sep + '?' + of_separators_re.pattern + sep + '?(?P<seasonCount>' + numeral + ')' + sep + '?(?:seasons?|saisons?|s))', confidence=0.7, formatter=parse_numeral)

        self.container.register_canonical_properties('other', 'FiNAL', 'Complete', validator=WeakValidator())

        self.container.register_property(None, r'[^0-9]((?P<season>' + digital_numeral + ')[^0-9 .-]?-?(?P<other>xAll))', confidence=1.0, formatter={None: parse_numeral, 'other': lambda x: 'Complete', 'season': season_parser}, validator=ChainedValidator(DefaultValidator(), ResolutionCollisionValidator()))

    def register_arguments(self, opts, naming_opts, output_opts, information_opts, webservice_opts, other_options):
        naming_opts.add_argument('-E', '--episode-prefer-number', action='store_true', dest='episode_prefer_number', default=False,
                               help='Guess "serie.213.avi" as the episodeNumber 213. Without this option, '
                                    'it will be guessed as season 2, episodeNumber 13')

    def supported_properties(self):
        return ['episodeNumber', 'season', 'episodeList', 'seasonList', 'episodeCount', 'seasonCount', 'version', 'other']

    def guess_episodes_rexps(self, string, node=None, options=None):
        found = self.container.find_properties(string, node, options)
        return self.container.as_guess(found, string)

    def should_process(self, mtree, options=None):
        return mtree.guess.get('type', '').startswith('episode')

    def process(self, mtree, options=None):
        GuessFinder(self.guess_episodes_rexps, None, self.log, options).process_nodes(mtree.unidentified_leaves())
