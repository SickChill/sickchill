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

from guessit.test.guessittest import *


class TestLanguage(TestGuessit):

    def check_languages(self, languages):
        for lang1, lang2 in languages.items():
            assert Language.fromguessit(lang1) == Language.fromguessit(lang2)

    def test_addic7ed(self):
        languages = {'English': 'en',
                     'English (US)': 'en-US',
                     'English (UK)': 'en-UK',
                     'Italian': 'it',
                     'Portuguese': 'pt',
                     'Portuguese (Brazilian)': 'pt-BR',
                     'Romanian': 'ro',
                     'Español (Latinoamérica)': 'es-MX',
                     'Español (España)': 'es-ES',
                     'Spanish (Latin America)': 'es-MX',
                     'Español': 'es',
                     'Spanish': 'es',
                     'Spanish (Spain)': 'es-ES',
                     'French': 'fr',
                     'Greek': 'el',
                     'Arabic': 'ar',
                     'German': 'de',
                     'Croatian': 'hr',
                     'Indonesian': 'id',
                     'Hebrew': 'he',
                     'Russian': 'ru',
                     'Turkish': 'tr',
                     'Swedish': 'se',
                     'Czech': 'cs',
                     'Dutch': 'nl',
                     'Hungarian': 'hu',
                     'Norwegian': 'no',
                     'Polish': 'pl',
                     'Persian': 'fa'}

        self.check_languages(languages)

    def test_subswiki(self):
        languages = {'English (US)': 'en-US', 'English (UK)': 'en-UK', 'English': 'en',
                     'French': 'fr', 'Brazilian': 'po', 'Portuguese': 'pt',
                     'Español (Latinoamérica)': 'es-MX', 'Español (España)': 'es-ES',
                     'Español': 'es', 'Italian': 'it', 'Català': 'ca'}

        self.check_languages(languages)

    def test_tvsubtitles(self):
        languages = {'English': 'en', 'Español': 'es', 'French': 'fr', 'German': 'de',
                     'Brazilian': 'br', 'Russian': 'ru', 'Ukrainian': 'ua', 'Italian': 'it',
                     'Greek': 'gr', 'Arabic': 'ar', 'Hungarian': 'hu', 'Polish': 'pl',
                     'Turkish': 'tr', 'Dutch': 'nl', 'Portuguese': 'pt', 'Swedish': 'sv',
                     'Danish': 'da', 'Finnish': 'fi', 'Korean': 'ko', 'Chinese': 'cn',
                     'Japanese': 'jp', 'Bulgarian': 'bg', 'Czech': 'cz', 'Romanian': 'ro'}

        self.check_languages(languages)

    def test_opensubtitles(self):
        opensubtitles_langfile = file_in_same_dir(__file__, 'opensubtitles_languages_2012_05_09.txt')
        for l in [u(l).strip() for l in io.open(opensubtitles_langfile, encoding='utf-8')][1:]:
            idlang, alpha2, _, upload_enabled, web_enabled = l.strip().split('\t')
            # do not test languages that are too esoteric / not widely available
            if int(upload_enabled) and int(web_enabled):
                # check that we recognize the opensubtitles language code correctly
                # and that we are able to output this code from a language
                assert idlang == Language.fromguessit(idlang).opensubtitles
                if alpha2:
                    # check we recognize the opensubtitles 2-letter code correctly
                    self.check_languages({idlang: alpha2})

    def test_tmdb(self):
        # examples from http://api.themoviedb.org/2.1/language-tags
        for lang in ['en-US', 'en-CA', 'es-MX', 'fr-PF']:
            assert lang == str(Language.fromguessit(lang))

    def test_subtitulos(self):
        languages = {'English (US)': 'en-US', 'English (UK)': 'en-UK', 'English': 'en',
                     'French': 'fr', 'Brazilian': 'po', 'Portuguese': 'pt',
                     'Español (Latinoamérica)': 'es-MX', 'Español (España)': 'es-ES',
                     'Español': 'es', 'Italian': 'it', 'Català': 'ca'}

        self.check_languages(languages)

    def test_thesubdb(self):
        languages = {'af': 'af', 'cs': 'cs', 'da': 'da', 'de': 'de', 'en': 'en', 'es': 'es', 'fi': 'fi',
                     'fr': 'fr', 'hu': 'hu', 'id': 'id', 'it': 'it', 'la': 'la', 'nl': 'nl', 'no': 'no',
                     'oc': 'oc', 'pl': 'pl', 'pt': 'pt', 'ro': 'ro', 'ru': 'ru', 'sl': 'sl', 'sr': 'sr',
                     'sv': 'sv', 'tr': 'tr'}

        self.check_languages(languages)

    def test_exceptions(self):
        assert Language.fromguessit('br') == Language.fromguessit('pt(br)')
        assert Language.fromguessit('unknown') == Language.fromguessit('und')
