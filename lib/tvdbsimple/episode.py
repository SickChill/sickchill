# -*- coding: utf-8 -*-

"""
This module implements the Episode functionality of TheTVDb API.
Allows to retrieve episode detailed info.

See [Episodes API section](https://api.thetvdb.com/swagger#!/Episodes)
"""

from .base import TVDB

class Episode(TVDB):
    """
    Episode class to retrieve detailed info about an episode.
    Requires the episode id.
    """
    _BASE_PATH = 'episodes'
    _URLS = {
        'info': '/{id}'
    }

    def __init__(self, id, language=''):
        """
        Initialize the episode class.

        `id` is the TheTVDb episode id. You can also provide `language`, 
        the language id you want to use to retrieve the info.
        """
        super(Episode, self).__init__(id)
        self._set_language(language)

    def info(self, language=''):
        """
        Get the episode information of the episode and set its values to the local attributes.

        You can set `language` with the language id to retrieve info in that specific language.

        It returns a dictionary with all the episode info.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> ep = tvdb.Episode(5330530)
            >>> ep.imdbId
            'tt4701544'

        """
        path = self._get_id_path('info')
        
        self._set_language(language)
        response = self._GET(path)
        self._set_attrs_to_values(response)
        return response
