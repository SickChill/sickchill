#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2014 Nicolas Wack <wackou@gmail.com>
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


class TestApi(TestGuessit):
    def test_api(self):
        movie_path = 'Movies/Dark City (1998)/Dark.City.(1998).DC.BDRip.720p.DTS.X264-CHD.mkv'

        movie_info = guessit.guess_movie_info(movie_path)
        video_info = guessit.guess_video_info(movie_path)
        episode_info = guessit.guess_episode_info(movie_path)
        file_info = guessit.guess_file_info(movie_path)

        assert guessit.guess_file_info(movie_path, type='movie') == movie_info
        assert guessit.guess_file_info(movie_path, type='video') == video_info
        assert guessit.guess_file_info(movie_path, type='episode') == episode_info 

        assert guessit.guess_file_info(movie_path, options={'type': 'movie'}) == movie_info
        assert guessit.guess_file_info(movie_path, options={'type': 'video'}) == video_info
        assert guessit.guess_file_info(movie_path, options={'type': 'episode'}) == episode_info

        # kwargs priority other options
        assert guessit.guess_file_info(movie_path, options={'type': 'episode'}, type='movie') == episode_info

        movie_path_name_only = 'Movies/Dark City (1998)/Dark.City.(1998).DC.BDRip.720p.DTS.X264-CHD'
        file_info_name_only = guessit.guess_file_info(movie_path_name_only, options={"name_only": True})

        assert 'container' not in file_info_name_only
        assert 'container' in file_info
