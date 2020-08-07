# -*- coding: utf-8 -*-

"""
This module implements the Search functionality of TheTVDb API.
Allows to search for tv series in the db.

See [Search API section](https://api.thetvdb.com/swagger#!/Search)
"""

from .base import TVDB

class Search(TVDB):
    """
    Class that allow to search for series with filters.
    """
    _BASE_PATH = 'search'
    _URLS = {
        'series': '/series',
        'series_params': '/series/params'
    }

    def series(self, name='', imdbId='', zap2itId='', language=''):
        """
        Search series with the information provided.

        You can set `name` to search for a series with that name. You can set `imdbId` 
        to search a series with the provided imdb id. You can set `zap2itId` 
        to search a series with the provided zap2it id. You can set `language` to 
        retrieve the results with the provided language.

        Returns a list series with basic information that matches your search.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> search = tvdb.Search()
            >>> reponse = search.series("doctor who 2005")
            >>> search.series[0]['seriesName']
            'Doctor Who (2005)'

        """
        path = self._get_path('series')

        filters = {}
        if name:
            filters['name'] = name
        if imdbId:
            filters['imdbId'] = imdbId
        if zap2itId:
            filters['zap2itId'] = zap2itId

        self._set_language(language)
        response = self._GET(path, params=filters)
        self._set_attrs_to_values({'series': response})
        return response

    def series_params(self):
        """
        Return the available search params.
        
        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('series_params')

        response = self._GET(path)
        self._set_attrs_to_values({'series_params': response})
        return response
