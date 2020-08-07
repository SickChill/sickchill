# -*- coding: utf-8 -*-

"""
tmdbsimple.search
~~~~~~~~~~~~~~~~~
This module implements the Search functionality of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class Search(TMDB):
    """
    Search functionality

    See: https://developers.themoviedb.org/3/search
    """
    BASE_PATH = 'search'
    URLS = {
        'company': '/company',
        'collection': '/collection',
        'keyword': '/keyword',
        'movie': '/movie',
        'multi': '/multi',
        'person': '/person',
        'tv': '/tv',
    }

    def company(self, **kwargs):
        """
        Search for companies.

        Args:
            query: (required) Pass a text query to search. This value should be
                URI encoded.
            page: (optional) Minimum 1, maximum 1000, default 1.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('company')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def collection(self, **kwargs):
        """
        Search for collections.

        Args:
            language: (optional) (optional) ISO 639-1 code.
            query: (required) Pass a text query to search. This value should be
                URI encoded.
            page: (optional) Minimum 1, maximum 1000, default 1.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('collection')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def keyword(self, **kwargs):
        """
        Search for keywords.

        Args:
            query: (required) Pass a text query to search. This value should be
                URI encoded.
            page: (optional) Minimum 1, maximum 1000, default 1.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('keyword')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def movie(self, **kwargs):
        """
        Search for movies.

        Args:
            language: (optional) (optional) ISO 639-1 code.
            query: (required) Pass a text query to search. This value should be
                URI encoded.
            page: (optional) Minimum 1, maximum 1000, default 1.
            include_adult: (optional) Choose whether to inlcude adult
                (pornography) content in the results.
            region: (optional) Specify a ISO 3166-1 code to filter release
                dates. Must be uppercase.
            year: (optional) A filter to limit the results to a specific year
                (looking at all release dates).
            primary_release_year: (optional) A filter to limit the results to a
                specific primary release year.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('movie')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def multi(self, **kwargs):
        """
        Search multiple models in a single request. Multi search currently
        supports searching for movies, tv shows and people in a single request.

        Args:
            language: (optional) (optional) ISO 639-1 code.
            query: (required) Pass a text query to search. This value should be
                URI encoded.
            page: (optional) Minimum 1, maximum 1000, default 1.
            include_adult: (optional) Choose whether to inlcude adult
                (pornography) content in the results.
            region: (optional) Specify a ISO 3166-1 code to filter release
                dates. Must be uppercase.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('multi')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def person(self, **kwargs):
        """
        Search for people.

        Args:
            language: (optional) (optional) ISO 639-1 code.
            query: (required) Pass a text query to search. This value should be
                URI encoded.
            page: (optional) Minimum 1, maximum 1000, default 1.
            include_adult: (optional) Choose whether to inlcude adult
                (pornography) content in the results.
            region: (optional) Specify a ISO 3166-1 code to filter release
                dates. Must be uppercase.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('person')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def tv(self, **kwargs):
        """
        Search for a TV show.

        Args:
            language: (optional) (optional) ISO 639-1 code.
            query: (required) Pass a text query to search. This value should be
                URI encoded.
            page: (optional) Minimum 1, maximum 1000, default 1.
            include_adult: (optional) Choose whether to inlcude adult
                (pornography) content in the results.
            first_air_date_year: (optional) Filter the results to only match
                shows that have an air date with with value.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('tv')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response
